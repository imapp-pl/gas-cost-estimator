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
    if opcode in constants.MEMORY_OPCODES:
      # memory-copying OPCODEs need arguments to indicate up to 16KB of memory
      args = [random.randint(0, (1<<14) - 1) for _ in range(0, arity(operation))]
      single_op_pushes = [byte_size_push(2, arg) for arg in args]
      # for these OPCODEs the important size variable is just the argument
      arg_sizes = args
    elif opcode.startswith("PUSH"):
      push_size = int(opcode[4:])
      arg_size = random.randint(1, push_size + 1)
      value = random.getrandbits(8 * arg_size)
      push_format = "%0." + str(push_size * 2) + "X"
      operation = operation.copy()
      operation['Value'] = operation['Value'] + (push_format % int(value))
      single_op_pushes = []
      arg_sizes = [arg_size]
    else:
      arg_byte_sizes = [random.randint(1, 32) for _ in range(0, arity(operation))]
      # NOTE: `random_value_byte_size_push` means in this case, we randomize the size of pushed value, but keep the PUSH
      # variant resticted to PUSH32.
      single_op_pushes = [random_value_byte_size_push(size, 32) for size in arg_byte_sizes]
      # for these OPCODEs the important size variable is the number of bytes of the argument
      arg_sizes = arg_byte_sizes
    # the arguments are popped from the stack
    single_op_pushes.reverse()

    return [Program(generate_single_marginal(single_op_pushes, operation, o), operation['Mnemonic'], o, arg_sizes) for o in op_counts]

def main():
  fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
  main()
