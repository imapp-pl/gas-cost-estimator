import os
import csv
import fire
import random
import sys

import constants
from common import generate_single_marginal, prepare_opcodes, get_selection, arity

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
      
    programs = [self._generate_single_program(operation, op_count, max_op_count) for operation in operations for op_count in op_counts]

    return programs

  def _generate_single_program(self, operation, op_count, max_op_count):
    assert op_count <= constants.MAX_INSTRUCTIONS
    # for compatibility with the generate_single_marginal function
    if operation['Mnemonic'] == 'CREATE':
      return Program(_generate_create_program(operation, op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] in ['EXTCODEHASH', 'EXTCODESIZE']:
      return Program(_generate_extcode_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'EXTCODECOPY':
      return Program(_generate_extcodecopy_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] in ['CALL', 'STATICCALL', 'DELEGATECALL']:
      return Program(_generate_call_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] in ['LOG0', 'LOG1', 'LOG2', 'LOG3', 'LOG4']:
      return Program(_generate_log_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] in ['REVERT', 'RETURN', 'STOP']:
      return Program(_generate_subcontext_exit_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'MCOPY':
      return Program(_generate_mcopy_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'KECCAK256':
      return Program(_generate_keccak256_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)

    single_op_pushes = ["6003"] * arity(operation)

    return Program(generate_single_marginal(single_op_pushes, operation, op_count), operation['Mnemonic'], op_count)

def _generate_create_program(create_operation, op_count):
  """
  Generates a program for CREATE opcode
  """
  assert create_operation['Mnemonic'] == 'CREATE'

  account_code = '6d6460016001016000526005601cf3600052'
  empty_pushes = '6000' * constants.MAX_INSTRUCTIONS
  single_op_pushes = '600d60126000' * op_count
  opcodes_with_pops = (create_operation['Value'][2:4] + '50') * op_count
  pops = '50' * (constants.MAX_INSTRUCTIONS - op_count)
  return account_code + empty_pushes + single_op_pushes + opcodes_with_pops + pops

def _generate_extcode_program(create_operation, op_count, max_op_count):
  """
  Generates a program for EXTCODEHASH and EXTCODESIZE opcodes
  """
  assert create_operation['Mnemonic'] in ['EXTCODEHASH', 'EXTCODESIZE']

  empty_pushes = '60ff' * constants.MAX_INSTRUCTIONS
  account_code = '6c63ffffffff60005260046000f3600052600d60006000f0'
  opcode_args = '80' * (max_op_count - 1) # duplicate the address on stack
  opcodes_with_pops = (create_operation['Value'][2:4] + '50') * op_count
  pops = '50' * (constants.MAX_INSTRUCTIONS + max_op_count - op_count)
  return empty_pushes + account_code + opcode_args + opcodes_with_pops + pops

def _generate_extcodecopy_program(create_operation, op_count, max_op_count):
  """
  Generates a program for EXTCODECOPY opcode
  """
  assert create_operation['Mnemonic'] == 'EXTCODECOPY'

  empty_pushes = '60ff' * 5
  account_deployment_code = '7f7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6000527fff60005260206000f30000000000000000000000000000000000000000000000602052602960006000f0'
  opcode_args = '60206000600083' * max_op_count
  opcodes = create_operation['Value'][2:4] * op_count
  pops = '50' * 5
  return empty_pushes + account_deployment_code + opcode_args + opcodes + pops

def _generate_call_program(create_operation, op_count, max_op_count):
  """
  Generates a program for CALL, STATICCALL, DELEGATECALL opcodes
  """
  assert create_operation['Mnemonic'] in ['CALL', 'STATICCALL', 'DELEGATECALL']

  empty_pushes = '60ff' * 5
  account_deployment_code = '7067600035600757fe5b60005260086018f36000526011600f6000f0'
  opcode_args = ''
  if create_operation['Mnemonic'] == 'CALL':
    opcode_args = '600060006020600060008661ffff' * max_op_count
  else:
    opcode_args = '60006000602060008561ffff' * max_op_count

  opcodes_with_pops = (create_operation['Value'][2:4] + '50') * op_count
  pops = '50' * (max_op_count - op_count + 5)
  return empty_pushes + account_deployment_code + '60ff' + opcode_args + opcodes_with_pops + pops

def _generate_log_program(log_operation, op_count, max_op_count):
  """
  Generates a program for LOG* opcodes
  """
  assert log_operation['Mnemonic'] in ['LOG0', 'LOG1', 'LOG2', 'LOG3', 'LOG4']
  
  # fill first 32 bytes of memory
  memory = '7f' + 'ff' * 32 + '6000' + '52'
  
  arguments = ('60ff' * (arity(log_operation) - 2) + '60206000') * max_op_count
  logs = log_operation['Value'][2:4] * op_count

  return memory + arguments + logs

def _generate_mcopy_program(mcopy_operation, op_count, max_op_count):
  """
  Generates a program for MCOPY opcode
  """
  assert mcopy_operation['Mnemonic'] == 'MCOPY'
  
  # fill 32nd byte of memory
  memory = '60ff600052'
  # copy 32nd byte of memory to the 1st byte so there is no memory expansion on MCOPY
  arguments = '6001601f6000' * max_op_count

  return memory + arguments + mcopy_operation['Value'][2:4] * op_count

def _generate_keccak256_program(mcopy_operation, op_count, max_op_count):
  """
  Generates a program for KECCAK256 opcode
  """
  assert mcopy_operation['Mnemonic'] == 'KECCAK256'
  
  # fill first 32 bytes
  memory = '7f' + 'ff' * 32 + '5f52'
  empty_pushes = '5f' * max_op_count
  arguments = '60206000' * max_op_count
  keccaks_with_pops = (mcopy_operation['Value'][2:4] + '50') * op_count
  pop_leftover = '50' * (max_op_count - op_count)

  return memory + empty_pushes + arguments + keccaks_with_pops + pop_leftover

def _generate_subcontext_exit_program(operation, op_count, max_op_count):
  """
  Generates a program for REVERT, RETURN and STOP opcodes
  """
  assert operation['Mnemonic'] in ['REVERT', 'RETURN', 'STOP']

  no_op_subcontext_code = '60ff60005260026018'
  op_subcontext_code = no_op_subcontext_code + operation['Value'][2:4]
  op_deployment_code = '7269' + op_subcontext_code + '600052600a6016f36000526013600d6000f0'
  no_op_deployment_code = '7168' + no_op_subcontext_code + '60005260096017f36000526012600e6000f0'

  op_address_store = '60ff52'
  op_address_load = '60ff51'

  no_op_calls = '60006000600060008461fffff450' * (max_op_count - op_count)
  op_calls = op_address_load + '60006000600060008461fffff450' * op_count
  
  return op_deployment_code + op_address_store + no_op_deployment_code + no_op_calls + op_address_load + op_calls
        
def main():
  fire.Fire(ProgramGenerator, name='generate')

if __name__ == '__main__':
  main()
