import os
import csv
import fire
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))


class Program(object):
  """
  POD object for a program
  """

  def __init__(self, bytecode, measured_op_position):
    self.bytecode = bytecode
    self.measured_op_position = measured_op_position


class ProgramGenerator(object):
  """
  Sample program generator for EVM instrumentation

  If used with `--fullCsv`, will print out a CSV in the following format:
  ```
  | program_id | opcode_measured | measured_op_position | bytecode |
  ```
  """

  def __init__(self):
    opcodes_file = os.path.join(dir_path, 'data', 'opcodes.csv')
    with open(opcodes_file) as csvfile:
      reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
      opcodes = list(reader)

    selection_file = os.path.join(dir_path, 'data', 'selection.csv')
    with open(selection_file) as csvfile:
      reader = csv.DictReader(csvfile, delimiter=' ', quotechar='"')
      selection = {i['Opcode']: i['Name'] for i in reader}

    self._operations = [i for i in opcodes if i['Value'] in selection]

  def generate(self, fullCsv=False):
    """
    Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
    programs to STDOUT

    Parameters:
    fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
    """

    programs = self._generate_simplest()

    if fullCsv:
      writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')
      opcodes = [operation['Mnemonic'] for operation in self._operations]

      # TODO: for now we only have a single program per opcode, hence the program_id is:
      program_ids = [opcode + '_0' for opcode in opcodes]
      measured_op_positions = [program.measured_op_position for program in programs]
      bytecodes = [program.bytecode for program in programs]

      header = ['program_id', 'opcode_measured', 'measured_op_position', 'bytecode']
      writer.writerow(header)

      rows = zip(program_ids, opcodes, measured_op_positions, bytecodes)
      for row in rows:
        writer.writerow(row)
    else:
      for program in programs:
        print(program.bytecode)


  def _generate_simplest(self):
    """
    Generates programs simple enough to run successfully and have the measured operation as last one

    (`0xfe` is an invalid opcode so in that case error is expected)
    """

    programs = [self._prepend_simplest_stack_prepare(operation) for operation in self._operations]
    programs = [self._maybe_prepend_something(program) for program in programs]
    return programs

  def _prepend_simplest_stack_prepare(self, operation):
    """
    Prepends simples pushes to meet the stack requirements for `operation`
    """

    if operation['Value'] != '0xfe':
      # valid opcodes
      removed_from_stack = int(operation['Removed from stack'])
      # i.e. 23 from 0x23
      opcode = operation['Value'][2:4]
      # push some garbage enough times to satisfy stack requirement for operation
      pushes = ["6020"] * removed_from_stack
      bytecode = ''.join(pushes + [opcode])
      return Program(bytecode, removed_from_stack)
    else:
      # designated invalid opcode
      return Program('fe', 0)

  def _maybe_prepend_something(self, program):
    """
    Just prepends some operation that's as little significant as possible to avoid running the
    measured operation as first operation (current `instrumenter.go` captures startup time there).

    TODO: remove when not necessary anymore
    """
    should_prepend = program.measured_op_position == 0
    bytecode = '6000' + program.bytecode if should_prepend else program.bytecode
    measured_op_position = 1 + program.measured_op_position if should_prepend else program.measured_op_position

    return Program(bytecode, measured_op_position)

def main():
  fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
  main()
