import os
import csv
import fire
import sys
import subprocess
import tempfile
import binascii

import constants

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
  Sample program generator for EVM/Ewasm instrumentation

  If used with `--fullCsv`, will print out a CSV in the following format:
  ```
  | program_id | opcode_measured | measured_op_position | bytecode |
  ```

  NOTE: `measured_op_position` doesn't take into account the specific instructions fired before the
  generated part starts executing. It is relative to the first instruction of the _generated_ part
  of the program. E.g.: `evmone` prepends `JUMPDESTI`, `openethereum_ewasm` prepends many instructions
  """

  def __init__(self, ewasm=False):
    self._ewasm = ewasm

    if self._ewasm:
      opcodes_file = os.path.join(dir_path, 'data', 'opcodes_ewasm.csv')
    else:
      opcodes_file = os.path.join(dir_path, 'data', 'opcodes.csv')

    with open(opcodes_file) as csvfile:
      reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
      opcodes = {i['Value']: i for i in reader}

    # complete the opcodes file with push/dup/swap, which are formatted differently in our source
    if not self._ewasm:
      opcodes = self._fill_opcodes_push_dup_swap(opcodes)

    if self._ewasm:
      selection_file = os.path.join(dir_path, 'data', 'selection_ewasm_first_pass.csv')
    else:
      selection_file = os.path.join(dir_path, 'data', 'selection.csv')

    with open(selection_file) as csvfile:
      reader = csv.DictReader(csvfile, delimiter=' ', quotechar='"')
      selection = [i['Opcode'] for i in reader]

    self._operations = [opcodes[op] for op in selection]

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

    (EVM `0xfe` is an invalid opcode so in that case error is expected)
    """

    programs = [self._prepend_simplest_stack_prepare(operation) for operation in self._operations]
    programs = [self._maybe_prepend_something(program) for program in programs]
    programs = [self._maybe_prepend_ewasm(program) for program in programs]
    programs = [self._maybe_append_ewasm(program, opcode) for program, opcode in zip(programs, self._operations)]
    programs = [self._maybe_wat2wasm(program) for program in programs]
    return programs

  def _prepend_simplest_stack_prepare(self, operation):
    """
    Prepends simples pushes (`i32.const` for Ewasm) to meet the stack requirements for `operation`.
    """

    if self._ewasm:
      # valid opcodes
      removed_from_stack = int(operation['Removed from stack'])
      opcode = "    " + operation['Mnemonic']
      # push some garbage enough times to satisfy stack requirement for operation
      # TODO: our data should allow to customize for `i64` instructions and push using that here
      pushes = ["    i32.const 32\n"] * removed_from_stack
      has_parameter = True if 'Parameter' in operation and operation['Parameter'] else False
      bytecode = ''.join(pushes + [opcode, operation['Parameter']]) if has_parameter else ''.join(pushes + [opcode])
      return Program(bytecode, removed_from_stack)
    else:
      if operation['Value'] != '0xfe':
        # valid opcodes
        removed_from_stack = int(operation['Removed from stack'])
        # i.e. 23 from 0x23
        opcode = operation['Value'][2:4]
        # push some garbage enough times to satisfy stack requirement for operation
        pushes = ["6020"] * removed_from_stack
        has_parameter = True if 'Parameter' in operation and operation['Parameter'] else False
        bytecode = ''.join(pushes + [opcode, operation['Parameter']]) if has_parameter else ''.join(pushes + [opcode])
        return Program(bytecode, removed_from_stack)
      else:
        # designated invalid opcode
        return Program('fe', 0)

  def _maybe_prepend_ewasm(self, program):
    """
    Prepends the same thing for every operation, just to get a valid ewasm program start
    """
    if self._ewasm:
      to_prepend = constants.EWASM_PREAMBLE
      new_code = to_prepend + program.bytecode
      program.bytecode = new_code
      return program
    else:
      return program

  def _maybe_append_ewasm(self, program, opcode):
    """
    Appends the same thing for every operation, just to get a valid ewasm program start
    """
    if self._ewasm:
      added_to_stack = int(opcode['Added to stack'])
      droppings = constants.EWASM_DROP * added_to_stack

      parenthesis = constants.EWASM_CLOSING_PARENTHESIS

      to_append = droppings + parenthesis
      new_code = program.bytecode + to_append
      program.bytecode = new_code
      return program
    else:
      return program

  def _maybe_wat2wasm(self, program):
    """
    Runs the compilation to wasm for ewasm using WABT
    """

    if self._ewasm:
      wat2wasm = ['wat2wasm']

      with tempfile.TemporaryDirectory() as tempdir:
        input_file_path = os.path.join(tempdir, "input.wat")
        output_file_path = os.path.join(tempdir, "output.wasm")
        args = ['-o', output_file_path, input_file_path]
        invocation = wat2wasm + args

        with open(input_file_path, 'w') as file:
          file.write(program.bytecode)

        result = subprocess.run(invocation, stdout=subprocess.PIPE, universal_newlines=True)
        assert result.returncode == 0

        with open(output_file_path, 'rb') as file:
          wasm_result_bin = file.read()

      wasm_result = binascii.hexlify(wasm_result_bin).decode('ascii')
      program.bytecode = wasm_result
      return program
    else:
      return program

  def _maybe_prepend_something(self, program):
    """
    Just prepends some operation that's as little significant as possible to avoid running the
    measured operation as first operation.

    TODO: remove when not necessary anymore
    """
    should_prepend = program.measured_op_position == 0

    if self._ewasm:
      prependable = constants.EWASM_SOMETHING
      prependable_length = constants.EWASM_SOMETHING_LENGTH
    else:
      prependable = constants.EVM_SOMETHING
      prependable_length = constants.EVM_SOMETHING_LENGTH

    if should_prepend:
      bytecode = prependable + program.bytecode
      measured_op_position = prependable_length + program.measured_op_position

      return Program(bytecode, measured_op_position)
    else:
      return program

  def _fill_opcodes_push_dup_swap(self, opcodes):
    pushes = constants.EVM_PUSHES
    dups = constants.EVM_DUPS
    swaps = constants.EVM_SWAPS

    pushes = self._opcodes_dict_push_dup_swap(pushes, [0] * len(pushes), [1] * len(pushes), parameter='00')
    opcodes = {**opcodes, **pushes}
    dups = self._opcodes_dict_push_dup_swap(dups, range(1, len(dups)), range(2, len(dups)+1))
    opcodes = {**opcodes, **dups}
    swaps = self._opcodes_dict_push_dup_swap(swaps, range(2, len(swaps)+1), range(2, len(swaps)+1))
    opcodes = {**opcodes, **swaps}
    return opcodes

  def _opcodes_dict_push_dup_swap(self, source, removeds, addeds, parameter=None):
    source_list = source.split()
    opcodes = source_list[::2]
    names = source_list[1::2]
    new_part = {
      opcode: {
        'Value': opcode,
        'Mnemonic': name,
        'Removed from stack': removed,
        'Added to stack': added,
        'Parameter': parameter
      } for opcode, name, removed, added in zip(opcodes, names, removeds, addeds)
    }

    return new_part

def main():
  fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
  main()
