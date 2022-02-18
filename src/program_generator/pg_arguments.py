from math import ceil
import os
import csv
import fire
import random
import sys

import constants

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

  def generate(self, fullCsv=False, count=1, opcode=None, opCount=10):
    """
    Main entrypoint of the CLI tool. Should dispatch to the desired generation routine and print
    programs to STDOUT

    Parameters:
    fullCsv (boolean): if set, will generate programs with accompanying data in CSV format
    count (int): the number of programs
    opcode (string): if set, will only generate programs for opcode
    opCount (integer): number of measured opcodes, defaults to 10

    selectionFile (string): file name of the OPCODE selection file under `data`, defaults to `selection.csv`
    seed: a seed for random number generator, defaults to 0
    """

    programs = self._generate_marginal(opcode, count, opCount)

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


  def _generate_marginal(self, opcode, count, op_count):
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

  # TODO: copied from pg_arythmetic.py. Refactor!
  def _random_push(self, push):
    value = random.getrandbits(8*push)
    value = hex(value)
    value = value[2:]
    if len(value) < 2*push:
      value = (2*push-len(value))*'0' + value
    op_num = 6 * 16 + push - 1  # 0x60 is PUSH1
    op = hex(op_num)[2:]
    return op + value

  def _generate_program_triplet(self, operation, op_count):
    arity = int(operation['Removed from stack'])
    arg_bit_sizes = [random.randint(1, 32) for _ in range(0, arity)]
    single_op_pushes = [self._random_push(size) for size in arg_bit_sizes]
    # the arguments are popped from the stack
    single_op_pushes.reverse()
    return [self._generate_single_program(single_op_pushes, arg_bit_sizes, operation, 0),
            self._generate_single_program(single_op_pushes, arg_bit_sizes, operation, op_count),
            self._generate_single_program(single_op_pushes, arg_bit_sizes, operation, op_count * 2)]

  def _generate_single_program(self, single_op_pushes, arg_bit_sizes, operation, op_count):
    """
    
    """
    arity = int(operation['Removed from stack'])

    # i.e. 23 from 0x23
    opcode = operation['Value'][2:4]
    popcode = "50"

    has_parameter = True if 'Parameter' in operation and operation['Parameter'] else False
    if has_parameter:
      opcode += operation['Parameter']

    push_count = 120
    total_pop_count = 40

    interleaved_pop_count = max(op_count - 1, 0)
    end_pop_count = total_pop_count - interleaved_pop_count
      
    pushes = single_op_pushes * ceil(push_count / arity)

    if op_count == 0:
      middle = []
      pops = [popcode] * total_pop_count
    elif op_count >= 1:
      middle = [opcode] + [popcode, opcode] * interleaved_pop_count
      pops = [popcode] * end_pop_count

    bytecode = ''.join(pushes + middle + pops)

    # just in case
    assert interleaved_pop_count + end_pop_count == total_pop_count
    assert end_pop_count > 0

    return Program(bytecode, operation['Mnemonic'], op_count, arg_bit_sizes)
        
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
