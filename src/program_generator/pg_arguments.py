import os
import csv
import fire
import random
import sys

import constants
from common import generate_single_marginal, prepare_opcodes, get_selection, arity, random_value_byte_size_push, byte_size_push

dir_path = os.path.dirname(os.path.realpath(__file__))

def get(l, index, default=None):
  return l[index] if -len(l) <= index < len(l) else default

class Program(object):
  """
  POD object for a program
  """

  def __init__(self, bytecode, opcode, op_count, args):
    self.bytecode = bytecode
    self.opcode = opcode
    self.op_count = op_count

    if opcode in constants.EVM_DUPS:
      variant = int(opcode[3:])
      self.arg0, self.arg1, self.arg2 = get(args, variant - 1), None, None
    elif opcode in constants.EVM_SWAPS:
      variant = int(opcode[4:])
      self.arg0, self.arg1, self.arg2 = get(args, 0), get(args, variant), None
    else:
      self.arg0 = get(args, 0)
      self.arg1 = get(args, 1)
      self.arg2 = get(args, 2)


class ProgramGenerator(object):
  """
  Sample program generator for EVM instrumentation

  If used with `--fullCsv`, will print out a CSV in the following format:
  ```
  | program_id | opcode | op_count | arg0 | arg1 | arg2 | bytecode |
  ```

  """

  def __init__(self, selectionFile='selection_arguments.csv', seed=0):
    random.seed(a=seed, version=2)

    opcodes = prepare_opcodes(os.path.join(dir_path, 'data', 'opcodes.csv'))
    selection = get_selection(os.path.join(dir_path, 'data', selectionFile))

    self._operations = [op for op in opcodes if op['Value'] in selection]

  def generate(self, fullCsv=True, count=1, opcode=None, opCount=10):
    """
    Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
    programs to STDOUT

    Parameters:
    fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
    count (int): the number of programs
    opcode (string): if set, will only generate programs for opcode
    opCount (integer): number of measured opcodes, defaults to 10. In total, programs with 0, `opCount` and `2 * opCount` will be generated.

    selectionFile (string): file name of the OPCODE selection file under `data`, defaults to `selection.csv`
    seed: a seed for random number generator, defaults to 0
    """

    programs = self._do_generate(opcode, count, opCount)

    if fullCsv:
      writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')

      opcodes = [program.opcode for program in programs]
      op_counts = [program.op_count for program in programs]
      arg0s = [program.arg0 for program in programs]
      arg1s = [program.arg1 for program in programs]
      arg2s = [program.arg2 for program in programs]
      program_ids = [program.opcode + '_' + str(idx) for idx, program in enumerate(programs)]
      bytecodes = [program.bytecode for program in programs]

      header = ['program_id', 'opcode', 'op_count', 'arg0', 'arg1', 'arg2', 'bytecode']
      writer.writerow(header)

      rows = zip(program_ids, opcodes, op_counts, arg0s, arg1s, arg2s, bytecodes)
      for row in rows:
        writer.writerow(row)
    else:
      for program in programs:
        print(program.bytecode)


  def _do_generate(self, opcode, count, op_count):
    """
    """
    operations = [operation for operation in self._operations if operation['Value'] != '0xfe']
    if opcode:
      operations = [operation for operation in operations if operation['Mnemonic'] == opcode]
    else:
      pass

    programs = [self._generate_program_triplet(operation, op_count) for operation in operations for _ in range(0, count)]
    programs = [item for sublist in programs for item in sublist]

    return programs

  def _generate_program_triplet(self, operation, op_count):
    opcode = operation['Mnemonic']

    # the program triplet will be for the following number of measured OPCODEs
    op_counts = [0, op_count, op_count * 2]

    if opcode == "CREATE":
      # the opcode arity is 3
      # allocate max possible used memory
      mem_allocation = "5f61080052"
      # put on stack the initial code for CREATE,
      # the initial code on stack is the same as for marginal examination but shifted left for convenience
      initial_code_on_stack = "7f6460016001015f526005601bf360000000000000000000000000000000000000"
      # fill memory first 32 slots stores the same initial code
      initial_code_in_mem = ""
      for pre_offset in range(32):
        offset = "%0.4X" % (32 * pre_offset)
        initial_code_in_mem += "8061" + offset + "52"
      # prefix code is the same for all programs - the same gas cost
      prefix_code = mem_allocation + initial_code_on_stack + initial_code_in_mem
      arg_sizes = [1, random.randint(1, 32), random.randint(1, 32)]
      # prepare arguments, the range for the initial code passed to CREATE
      # the offset and size are random, but effectively executed initial code is the same
      # note that the effectively executed initial code and the deployed code are the same as for marginal examination
      single_op_pushes = ["61%0.4X" % (arg_sizes[2] * 32), "61%0.4X" % ((arg_sizes[1] - 1) * 32), "5f"]
      return [Program(prefix_code + generate_single_marginal(single_op_pushes, operation, o), operation['Mnemonic'], o, arg_sizes) for
              o in op_counts]
    if opcode in ['CALL', 'STATICCALL', 'DELEGATECALL']:
      arg_sizes = [random.randint(1, 32) for _ in range(0, 2)]  # argsOffset and argsSize
      args_offset = "61%0.4X" % ((arg_sizes[0] - 1) * 32)
      args_size = "61%0.4X" % (arg_sizes[1] * 32)
      single_call = ''
      noop = ''  # contains the same series of opcodes as those invoked by single_call
      if opcode == 'CALL':  #
        single_call = '86868686868686f150'
        noop = '8686868686868660015860060157fe5b50'
      elif opcode == 'STATICCALL':
        single_call = '858585858585fa50'
        noop = '85858585858560015860060157fe5b50'
      elif opcode == 'DELEGATECALL':  #
        single_call = '858585858585f450'
        noop = '85858585858560015860060157fe5b50'
      max_op_count = max(op_counts)
      dummy_pushes = '60ff' * 5
      # allocate max possible used memory
      mem_allocation = "5f61080052"
      account_deployment_code = '716860015860060157fe5b60005260096017f36000526012600e6000f0'  # CREATE
      account_deployment_code += '5f5f' + args_size + args_offset  # retSize + retOffset + argsOffset + argsSize in reverse order
      if opcode == 'CALL':  # CALL takes extra parameter 'value'
        account_deployment_code += '5f85'
      else:
        account_deployment_code += '84'
      account_deployment_code += '61ffff'  # gas
      dummy_pops = '50' * 5
      # calls = single_call * op_count
      # noops = noop * (max_op_count - op_count)
      return [Program(dummy_pushes + mem_allocation + account_deployment_code + (single_call * o) + (
                noop * (max_op_count - o)) + dummy_pops, opcode, o, arg_sizes) for o in op_counts]
    if opcode in ['REVERT', 'RETURN']: # not in MEMORY_OPCODES, maybe should be
      arg_sizes = [random.randint(0, (1<<14) - 1) for _ in range(0, arity(operation))]
      no_op_subcontext_code = '6000617fff5361%0.4X61%0.4X' % (arg_sizes[0], arg_sizes[1])
      op_subcontext_code = no_op_subcontext_code + operation['Value'][2:4]
      op_deployment_code = '756c' + op_subcontext_code + '600052600d6013f36000526016600a6000f0'
      no_op_deployment_code = '746b' + no_op_subcontext_code + '600052600c6014f36000526015600b6000f0'

      op_address_store = '60ff52'
      op_address_load = '60ff51'

      no_op_call = '60006000600060008461fffff450'
      op_call = '60006000600060008461fffff450'

      max_op_count = max(op_counts)

      return [Program(
        op_deployment_code + op_address_store + no_op_deployment_code + (no_op_call * (max_op_count - o)) + op_address_load + (op_call * o),
        operation['Mnemonic'], o, arg_sizes
      ) for o in op_counts]

    init_code = None
    if opcode == "MCOPY": # MCOPY is also in MEMORY_OPCODES
      arg_sizes = [random.randint(1, 32) for _ in range(0, 3)]  # dest, offset and size, but in words
      dest = "61%0.4X" % ((arg_sizes[0] - 1) * 32)
      offset = "61%0.4X" % ((arg_sizes[1] - 1) * 32)
      size = "61%0.4X" % (arg_sizes[2] * 32)
      single_op_pushes = [dest, offset, size]
    elif opcode in ['MLOAD', 'MSTORE', 'MSTORE8']: # MLOAD, MSTORE, MSTORE8 are also in MEMORY_OPCODES
      offset_size = random.randint(0, 31 * 32) # 32 words only, it is enough
      if opcode == 'MSTORE8':
        value_size = 1
      else:
        value_size = random.randint(1, 32)
      offset = "61%0.4X" % offset_size
      value = "7f%0.64X" % random.getrandbits(8 * value_size)
      arg_sizes = [offset_size, value_size]
      if opcode == 'MLOAD':
        single_op_pushes = [offset]
        init_code = value + offset + '52'
      else:
        single_op_pushes = [offset, value]
    elif opcode in ['LOG0', 'LOG1', 'LOG2', 'LOG3', 'LOG4']: # LOGs are also in MEMORY_OPCODES
      # memory-copying part need arguments to indicate up to 16KB of memory
      args = [random.randint(0, (1 << 14) - 1) for _ in range(0, 2)]
      # topics
      args = args + [random.randint(1, 32) for _ in range(2, arity(operation))]
      single_op_pushes = [byte_size_push(2, arg) for arg in args[0:2]]
      single_op_pushes = single_op_pushes + [random_value_byte_size_push(size, 32) for size in args[2:]]
      arg_sizes = args
    elif opcode in constants.MEMORY_OPCODES:
      # memory-copying OPCODEs need arguments to indicate up to 16KB of memory
      args = [random.randint(0, (1<<14) - 1) for _ in range(0, arity(operation))]
      single_op_pushes = [byte_size_push(2, arg) for arg in args]
      # for these OPCODEs the important size variable is just the argument
      arg_sizes = args
    elif opcode.startswith("PUSH"):
      push_size = int(opcode[4:])
      arg_size = random.randint(1, push_size)
      value = random.getrandbits(8 * arg_size)
      push_format = "%0." + str(push_size * 2) + "X"
      operation = operation.copy()
      operation['Value'] = operation['Value'] + (push_format % int(value))
      single_op_pushes = []
      arg_sizes = [arg_size]
    else: # arithemetic
      arg_byte_sizes = [random.randint(1, 32) for _ in range(0, arity(operation))]
      # NOTE: `random_value_byte_size_push` means in this case, we randomize the size of pushed value, but keep the PUSH
      # variant resticted to PUSH32.
      single_op_pushes = [random_value_byte_size_push(size, 32) for size in arg_byte_sizes]
      # for these OPCODEs the important size variable is the number of bytes of the argument
      arg_sizes = arg_byte_sizes
    # the arguments are popped from the stack
    single_op_pushes.reverse()

    return [Program(generate_single_marginal(single_op_pushes, operation, o, init_code), operation['Mnemonic'], o, arg_sizes) for o in op_counts]

def main():
  fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
  main()
