import os
import csv
import fire
import sys

import constants

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

  def __init__(self):
    opcodes_file = os.path.join(dir_path, 'data', 'opcodes.csv')

    with open(opcodes_file) as csvfile:
      reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
      opcodes = {i['Value']: i for i in reader}

    opcodes = self._fill_opcodes_push_dup_swap(opcodes)

    selection_file = os.path.join(dir_path, 'data', 'selection.csv')

    with open(selection_file) as csvfile:
      reader = csv.DictReader(csvfile, delimiter=' ', quotechar='"')
      selection = [i['Opcode'] for i in reader]

    self._operations = [opcodes[op] for op in selection]

  def generate(self, fullCsv=False, opcode=None):
    """
    Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
    programs to STDOUT

    Parameters:
    fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
    opcode (string): if set, will only generate programs for opcode
    """

    programs = self._generate_marginal(opcode)

    if fullCsv:
      writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')

      # TODO: for now we only have a single program per opcode, hence the program_id is:
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


  def _generate_marginal(self, opcode):
    """
    """
    operations = [operation for operation in self._operations if operation['Value'] != '0xfe']
    if opcode:
      operations = [operation for operation in operations if operation['Mnemonic'] == opcode]
    else:
      arithmetic_ops = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]  # ADD MUL SUB DIV SDIV MOD SMOD ADDMOD MULMOD
      exp_ops = [0x0a]  # EXP
      bitwise_ops = [0x16, 0x17, 0x18, 0x19]  # AND OR XOR NOT
      byte_ops = [0x1a, 0x0b]  # BYTE SIGNEXTEND
      shift_ops = [0x1b, 0x1c, 0x1d]  # SHL, SHR, SAR
      comparison_ops = [0x10, 0x11, 0x12, 0x13, 0x14]  # LT, GT, SLT, SGT, EQ
      iszero_ops = [0x15]  # ISZERO
      all_ops = []
      all_ops.extend(arithmetic_ops)
      all_ops.extend(exp_ops)
      all_ops.extend(bitwise_ops)
      all_ops.extend(byte_ops)
      all_ops.extend(shift_ops)
      all_ops.extend(comparison_ops)
      all_ops.extend(iszero_ops)
      operations = [operation for operation in operations if int(operation['Value'], 16) in all_ops]
      
    programs = [self._generate_single_program(operation, op_count) for operation in operations for op_count in range(0, 200)]

    return programs

  def _generate_single_program(self, operation, op_count):
    """
    
    """
    # valid opcodes
    removed_from_stack = int(operation['Removed from stack'])
    added_to_stack = int(operation['Added to stack'])
    # i.e. 23 from 0x23
    opcode = operation['Value'][2:4]
    popcode = "50"

    pushes = ["6020"] * 1000

    # TODO for pushes
    # has_parameter = True if 'Parameter' in operation and operation['Parameter'] else False

    interleaved_pop_count = op_count - 1
    if op_count == 0:
      middle = []
      pops = [popcode] * 499
    elif op_count == 1:
      middle = [opcode]
      pops = [popcode] * 499
    elif op_count > 1:
      middle = [opcode] + [popcode, opcode] * interleaved_pop_count
      pops = [popcode] * (499 - interleaved_pop_count)

    bytecode = ''.join(pushes + middle + pops)

    return Program(bytecode, operation['Mnemonic'], op_count)
        
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
