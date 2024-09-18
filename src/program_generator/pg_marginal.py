import os
import csv
import fire
import random
import sys

from common import generate_create_program, generate_single_marginal, prepare_opcodes, get_selection, arity

dir_path = os.path.dirname(os.path.realpath(__file__))


class Program(object):
  """
  POD object for a program
  """

  def __init__(self, bytecode, opcode, op_count):
    self.bytecode = bytecode
    self.opcode = opcode
    self.op_count = op_count


class ProgramGenerator(object):
  """
  Sample program generator for EVM instrumentation

  If used with `--fullCsv`, will print out a CSV in the following format:
  ```
  | program_id | opcode | op_count | bytecode |
  ```

  """

  def __init__(self, selectionFile='selection.csv', seed=0):
    random.seed(a=seed, version=2)

    opcodes = prepare_opcodes(os.path.join(dir_path, 'data', 'opcodes.csv'))
    selection = get_selection(os.path.join(dir_path, 'data', selectionFile))

    self._operations = [opcodes[op] for op in selection]

  def generate(self, fullCsv=False, opcode=None, maxOpCount=50, shuffleCounts=False, stepOpCount=5):
    """
    Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
    programs to STDOUT

    Parameters:
    fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
    opcode (string): if set, will only generate programs for opcode
    maxOpCount (integer): maximum number of measured opcodes, defaults to 50
    shuffleCounts (boolean): if set, will shuffle the op counts used to generate programs for each OPCODE
    stepOpCount (integer): by how much the number of measured opcodes should increase, defaults to 5

    selectionFile (string): file name of the OPCODE selection file under `data`, defaults to `selection.csv`
    seed: a seed for random number generator, defaults to 0
    """

    programs = self._do_generate(opcode, maxOpCount, shuffleCounts, stepOpCount)

    if fullCsv:
      writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')

      opcodes = [program.opcode for program in programs]
      op_counts = [program.op_count for program in programs]
      program_ids = [program.opcode + '_' + str(program.op_count) for program in programs]
      bytecodes = [program.bytecode for program in programs]

      header = ['program_id', 'opcode', 'op_count', 'bytecode']
      writer.writerow(header)

      rows = zip(program_ids, opcodes, op_counts, bytecodes)
      for row in rows:
        writer.writerow(row)
    else:
      for program in programs:
        print(program.bytecode)


  def _do_generate(self, opcode, max_op_count, shuffle_counts, step_op_count):
    """
    """
    operations = [operation for operation in self._operations if operation['Value'] != '0xfe']
    if opcode:
      operations = [operation for operation in operations if operation['Mnemonic'] == opcode]
    else:
      pass

    op_counts = list(range(0, max_op_count + 1, step_op_count))
    if shuffle_counts:
      random.shuffle(op_counts)
      
    programs = [self._generate_single_program(operation, op_count) for operation in operations for op_count in op_counts]

    return programs

  def _generate_single_program(self, operation, op_count):
    # for compatibility with the generate_single_marginal function
    if operation['Mnemonic'] == 'CREATE':
        return Program(generate_create_program(operation, op_count), operation['Mnemonic'], op_count)

    single_op_pushes = ["6003"] * arity(operation)

    return Program(generate_single_marginal(single_op_pushes, operation, op_count), operation['Mnemonic'], op_count)
        
def main():
  fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
  main()
