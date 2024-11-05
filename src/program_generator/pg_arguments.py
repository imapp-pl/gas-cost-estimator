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

  def __init__(self, selectionFile='selection.csv', seed=0):
    random.seed(a=seed, version=2)

    opcodes = prepare_opcodes(os.path.join(dir_path, 'data', 'opcodes.csv'))
    selection = get_selection(os.path.join(dir_path, 'data', selectionFile))

    self._operations = [opcodes[op] for op in selection]

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
    if opcode in constants.MEMORY_OPCODES:
      # memory-copying OPCODEs need arguments to indicate up to 16KB of memory
      args = [random.randint(0, (1<<14) - 1) for _ in range(0, arity(operation))]
      single_op_pushes = [byte_size_push(2, arg) for arg in args]
      # for these OPCODEs the important size variable is just the argument
      arg_sizes = args
    else:
      arg_byte_sizes = [random.randint(1, 32) for _ in range(0, arity(operation))]
      # NOTE: `random_value_byte_size_push` means in this case, we randomize the size of pushed value, but keep the PUSH
      # variant resticted to PUSH32.
      single_op_pushes = [random_value_byte_size_push(size, 32) for size in arg_byte_sizes]
      # for these OPCODEs the important size variable is the number of bytes of the argument
      arg_sizes = arg_byte_sizes
    # the arguments are popped from the stack
    single_op_pushes.reverse()

    # the program triplet will be for the following number of measured OPCODEs
    op_counts = [0, op_count, op_count * 2]

    return [Program(generate_single_marginal(single_op_pushes, operation, o), operation['Mnemonic'], o, arg_sizes) for o in op_counts]

def main():
  fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
  main()
