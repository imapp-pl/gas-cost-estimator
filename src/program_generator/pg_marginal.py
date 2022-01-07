import os
import csv
import fire
import random
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

  def __init__(self, selectionFile='selection.csv', seed=0):
    if seed:
      random.seed(a=seed, version=2)

    opcodes_file = os.path.join(dir_path, 'data', 'opcodes.csv')

    with open(opcodes_file) as csvfile:
      reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
      opcodes = {i['Value']: i for i in reader}

    opcodes = self._fill_opcodes_push_dup_swap(opcodes)

    selection_file = os.path.join(dir_path, 'data', selectionFile)

    with open(selection_file) as csvfile:
      reader = csv.DictReader(csvfile, delimiter=' ', quotechar='"')
      selection = [i['Opcode'] for i in reader]

    self._operations = [opcodes[op] for op in selection]

  def generate(self, fullCsv=False, opcode=None, maxOpCount=50, shuffleCounts=False):
    """
    Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
    programs to STDOUT

    Parameters:
    fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
    opcode (string): if set, will only generate programs for opcode
    maxOpCount (integer): maximum number of measured opcodes, defaults to 50
    shuffleCounts (boolean): if set, will shuffle the op counts used to generate programs for each OPCODE

    selectionFile (string): file name of the OPCODE selection file under `data`, defaults to `selection.csv`
    seed: a seed for random number generator, defaults to 0
    """

    programs = self._generate_marginal(opcode, maxOpCount, shuffleCounts)

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


  def _generate_marginal(self, opcode, max_op_count, shuffle_counts):
    """
    """
    operations = [operation for operation in self._operations if operation['Value'] != '0xfe']
    if opcode:
      operations = [operation for operation in operations if operation['Mnemonic'] == opcode]
    else:
      pass

    op_counts = list(range(0, max_op_count))
    if shuffle_counts:
      random.shuffle(op_counts)
      
    programs = [self._generate_single_program(operation, op_count) for operation in operations for op_count in op_counts]

    return programs

  def _generate_single_program(self, operation, op_count):
    """
    
    """

    # i.e. 23 from 0x23
    opcode = operation['Value'][2:4]
    popcode = "50"

    has_parameter = True if 'Parameter' in operation and operation['Parameter'] else False
    if has_parameter:
      opcode += operation['Parameter']

    if ("PUSH" in operation['Mnemonic'] or "DUP" in operation['Mnemonic']):
      push_count = 200
      total_pop_count = 200
    else:
      push_count = 1000
      total_pop_count = 200

    interleaved_pop_count = max(op_count - 1, 0)
    end_pop_count = total_pop_count - interleaved_pop_count
      
    pushes = ["6020"] * push_count

    if op_count == 0:
      middle = []
      pops = [popcode] * total_pop_count
    elif op_count >= 1:
      middle = [opcode] + [popcode, opcode] * interleaved_pop_count
      pops = [popcode] * end_pop_count

    bytecode = ''.join(pushes + middle + pops)

    # just in case
    assert interleaved_pop_count + end_pop_count == total_pop_count

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
