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

    self._operations = [op for op in opcodes if op['Value'] in selection]

  def generate(self, fullCsv=True, opcode=None, maxOpCount=50, shuffleCounts=False, stepOpCount=5):
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
    operations = self._operations
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
    if operation['Mnemonic'] in ['CALLDATASIZE', 'CALLDATACOPY', 'CALLDATALOAD']:
      return Program(_generate_calldata_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
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
    if operation['Mnemonic'] in ['REVERT', 'RETURN']:
      return Program(_generate_subcontext_exit_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'MSTORE':
      return Program(_generate_mstore_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'MSTORE_COLD':
      return Program(_generate_mstore_cold_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'MCOPY':
      return Program(_generate_mcopy_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'MCOPY_COLD':
      return Program(_generate_mcopy_cold_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'KECCAK256':
      return Program(_generate_keccak256_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'SLOAD_COLD':
      return Program(_generate_sload_cold_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'SLOAD_WARM':
      return Program(_generate_sload_warm_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'SSTORE_COLD_CHANGE':
      return Program(_generate_sstore_cold_change_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'SSTORE_COLD_NO_CHANGE':
      return Program(_generate_sstore_cold_no_change_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'SSTORE_WARM_CHANGE':
      return Program(_generate_sstore_warm_change_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'SSTORE_WARM_NO_CHANGE':
      return Program(_generate_sstore_warm_no_change_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'TLOAD':
      return Program(_generate_tload_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'TLOAD_EXT':
      return Program(_generate_tload_ext_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'TSTORE':
      return Program(_generate_tstore_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'TSTORE0':
      return Program(_generate_tstore0_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'] == 'TSTORE_EXT':
      return Program(_generate_tstore_ext_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)
    if operation['Mnemonic'].startswith('PUSH'):
      return Program(_generate_push_program(operation, op_count, max_op_count), operation['Mnemonic'], op_count)

    single_op_pushes = ["6003"] * arity(operation)

    return Program(generate_single_marginal(single_op_pushes, operation, op_count), operation['Mnemonic'], op_count)

def _generate_create_program(create_operation, op_count):
  """
  Generates a program for CREATE opcode
  """
  assert create_operation['Mnemonic'] == 'CREATE'

  account_code = '6d6460016001016000526005601bf3600052'
  empty_pushes = '6000' * constants.MAX_INSTRUCTIONS
  single_op_pushes = '600e60126000' * op_count
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

  single_call = ''
  noop = '' # contains the same series of opcodes as those invoked by single_call
  if create_operation['Mnemonic'] == 'CALL': #
    single_call = '86868686868686f150'
    noop = '8686868686868660015860060157fe5b50'
  elif create_operation['Mnemonic'] == 'STATICCALL':
    single_call = '858585858585fa50'
    noop = '85858585858560015860060157fe5b50'
  elif create_operation['Mnemonic'] == 'DELEGATECALL': #
    single_call = '858585858585f450'
    noop = '85858585858560015860060157fe5b50'

  dummy_pushes = '60ff' * 5
  account_deployment_code = '716860015860060157fe5b60005260096017f36000526012600e6000f05f5f60205f5f8561ffff'
  calls = single_call * op_count
  noops = noop * (max_op_count - op_count)
  dummy_pops = '50' * 5
  return dummy_pushes + account_deployment_code + calls + noops + dummy_pops

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

def _generate_mstore_program(mcopy_operation, op_count, max_op_count):
  """
  Generates a program for MSTORE opcode
  """
  assert mcopy_operation['Mnemonic'] == 'MSTORE'
  
  init = '60ff5f52'
  ops = '60ff5f52' * op_count
  noops = '60ff5f' * (max_op_count - op_count)
  return init + ops + noops

def _generate_mstore_cold_program(mcopy_operation, op_count, max_op_count):
  """
  Generates a program for MSTORE opcode using cold memory (memory expansion every time)
  """
  assert mcopy_operation['Mnemonic'] == 'MSTORE_COLD'

  init = '60ff5f525f'
  ops = '60200160ff8152' * op_count
  noops = '60200160ff81' * (max_op_count - op_count)
  return init + ops + noops

def _generate_mcopy_program(mcopy_operation, op_count, max_op_count):
  """
  Generates a program for MCOPY opcode
  """
  assert mcopy_operation['Mnemonic'] == 'MCOPY'
  
  init = '60ff5f5260fe602052'
  ops = '60205f60205e' * op_count
  noops = '60205f6020' * (max_op_count - op_count)
  return init + ops + noops

def _generate_mcopy_cold_program(mcopy_operation, op_count, max_op_count):
  """
  Generates a program for MCOPY opcode using cold memory (memory expansion every time)
  """
  assert mcopy_operation['Mnemonic'] == 'MCOPY_COLD'
    
  init = '60ff5f525f'
  ops = '60200160205f825e' * op_count
  noops = '60200160205f82' * (max_op_count - op_count)
  return init + ops + noops

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

def _generate_tload_program(tload_operation, op_count, max_op_count):
  """
  Generates a program for TLOAD opcode
  """
  assert tload_operation['Mnemonic'] == 'TLOAD'

  # tstore single value
  prepare = '60ff60ff5d'

  arguments = '60ff' * max_op_count

  return prepare + arguments + (tload_operation['Value'][2:4] + '50') * op_count + '50' * (max_op_count - op_count)

def _generate_tload_ext_program(tload_operation, op_count, max_op_count):
  """
  Generates a program for TLOAD opcode, with an external contract
  """
  assert tload_operation['Mnemonic'] == 'TLOAD_EXT'

  no_op_subcontext_code = '60ff'
  op_subcontext_code = no_op_subcontext_code + tload_operation['Value'][2:4]
  no_op_deployment_code = '6f60ff60ff5d61' + no_op_subcontext_code + '6000526002601ef3600052601060106000f0'
  op_deployment_code =    '7060ff60ff5d62' + op_subcontext_code +    '6000526003601df36000526011600f6000f0'

  op_address_store = '60ff52'
  op_address_load = '60ff51'

  no_op_calls = '600060006000600060008561fffff150' * (max_op_count - op_count)
  op_calls =    '600060006000600060008561fffff150' * op_count

  return op_deployment_code + op_address_store + no_op_deployment_code + no_op_calls + op_address_load + op_calls

def _generate_tstore_program(tstore_operation, op_count, max_op_count):
  """
  Generates a program for TSTORE opcode
  """
  assert tstore_operation['Mnemonic'] == 'TSTORE'

  # values start with 16 so hex format naturally occupies two positions
  arguments = ''
  for v in range(max_op_count):
    arguments += '60' + hex(v + 16)[2:] + '6001'

  return arguments + tstore_operation['Value'][2:4] * op_count

def _generate_tstore0_program(tstore_operation, op_count, max_op_count):
  """
  Generates a program for TSTORE opcode but always store in a new slot
  """
  assert tstore_operation['Mnemonic'] == 'TSTORE0'

  # values start with 16 so hex format naturally occupies two positions
  arguments = ''
  for v in range(max_op_count):
    arguments += '60' + hex(v + 16)[2:] + '60' + hex(v + 16)[2:]

  return arguments + tstore_operation['Value'][2:4] * op_count

def _generate_tstore_ext_program(tstore_operation, op_count, max_op_count):
  """
  Generates a program for TSTORE opcode, with an external contract
  """
  assert tstore_operation['Mnemonic'] == 'TSTORE_EXT'

  no_op_subcontext_code = '60ff5c60010160ff'
  op_subcontext_code = no_op_subcontext_code + tstore_operation['Value'][2:4]
  no_op_deployment_code = '7067' + no_op_subcontext_code + '60005260086018f36000526011600f6000f0'
  op_deployment_code =    '7168' + op_subcontext_code +    '60005260096017f36000526012600e6000f0'

  op_address_store = '60ff52'
  op_address_load = '60ff51'

  no_op_calls = '600060006000600060008561fffff150' * (max_op_count - op_count)
  op_calls =    '600060006000600060008561fffff150' * op_count

  return op_deployment_code + op_address_store + no_op_deployment_code + no_op_calls + op_address_load + op_calls

def _generate_push_program(operation, op_count, max_op_count):
  """
  Generates a program for PUSH opcodes
  """
  assert operation['Mnemonic'].startswith('PUSH')

  push_size = int(operation['Mnemonic'][4:])
  operation = operation.copy()
  operation['Value'] = operation['Value'] + ('03' * push_size)  # just add default value

  single_op_pushes = []

  return generate_single_marginal(single_op_pushes, operation, op_count)

def _generate_subcontext_exit_program(operation, op_count, max_op_count):
  """
  Generates a program for REVERT, RETURN and STOP opcodes
  """
  assert operation['Mnemonic'] in ['REVERT', 'RETURN']

  no_op_subcontext_code = '60ff60005260026018'
  op_subcontext_code = no_op_subcontext_code + operation['Value'][2:4]
  op_deployment_code = '7269' + op_subcontext_code + '600052600a6016f36000526013600d6000f0'
  no_op_deployment_code = '7168' + no_op_subcontext_code + '60005260096017f36000526012600e6000f0'

  op_address_store = '60ff52'
  op_address_load = '60ff51'

  no_op_calls = '60006000600060008461fffff450' * (max_op_count - op_count)
  op_calls = '60006000600060008461fffff450' * op_count
  
  return op_deployment_code + op_address_store + no_op_deployment_code + no_op_calls + op_address_load + op_calls

def _generate_calldata_program(operation, op_count, max_op_count):
  """
  Generates a program for CALLDATASIZE
  """
  assert operation['Mnemonic'] in ['CALLDATASIZE', 'CALLDATACOPY', 'CALLDATALOAD']

  op_deployment_code = '' # this prevents warnings
  no_op_deployment_code = ''
  if operation['Mnemonic'] == 'CALLDATALOAD':
    no_op_subcontext_code = '5f'
    op_subcontext_code = '5f35'
    op_deployment_code = '6961' + op_subcontext_code + '5f526002601ef3600052600a60166000f0'
    no_op_deployment_code = '6860' + no_op_subcontext_code + '5f526001601ff3600052600960176000f0'
  elif operation['Mnemonic'] == 'CALLDATASIZE':
    no_op_subcontext_code = '5f'
    op_subcontext_code = '5f36'
    op_deployment_code = '6961' + op_subcontext_code + '5f526002601ef3600052600a60166000f0'
    no_op_deployment_code = '6860' + no_op_subcontext_code + '5f526001601ff3600052600960176000f0'
  elif operation['Mnemonic'] == 'CALLDATACOPY':
    no_op_subcontext_code = '5f5f5260205f5f'
    op_subcontext_code = no_op_subcontext_code + '37'
    op_deployment_code = '6f67' + op_subcontext_code + '5f5260086018f3600052601060106000f0'
    no_op_deployment_code = '6e66' + no_op_subcontext_code + '5f5260076019f3600052600f60116000f0'

  op_address_store = '60ff52'
  op_address_load = '60ff51'

  # 32 bytes calldata
  no_op_calls = '60006000602060008461fffff450' * (max_op_count - op_count)
  op_calls = '60006000602060008461fffff450' * op_count
  
  return op_deployment_code + op_address_store + no_op_deployment_code + no_op_calls + op_address_load + op_calls

    
def _generate_sload_cold_program(operation, op_count, max_op_count):
  """
  Generates a program for SLOAD where every SLOAD loads from a cold slot
  """
  assert operation['Mnemonic'] == 'SLOAD_COLD'

  # push 0..max_op_count range on the stack
  args_pushes = ''.join([f'60{i:02x}' for i in range(max_op_count)])
  opcodes = (operation['Value'][2:] + '50') * op_count
  pops = '50' * (max_op_count - op_count)
  
  return args_pushes + opcodes + pops

def _generate_sload_warm_program(operation, op_count, max_op_count):
  """
  Generates a program for SLOAD where every SLOAD loads from a warm slot
  """
  assert operation['Mnemonic'] == 'SLOAD_WARM'

  slot_warmup_code = '5f5450' # SLOAD from slot 0 and pop
  args_pushes = '5f' * max_op_count
  opcodes = (operation['Value'][2:] + '50') * op_count
  pops = '50' * (max_op_count - op_count)
  
  return slot_warmup_code + args_pushes + opcodes + pops

def _generate_sstore_cold_change_program(operation, op_count, max_op_count):
  """
  Generates a program for SSTORE opcode where every SSTORE stores in a cold storage slot and value in the slot is changed
  """
  assert operation['Mnemonic'] == 'SSTORE_COLD_CHANGE'

  # store values in different slots
  args_pushes = ''.join([('7f' + 'ff' * 32 + f'60{i:02x}') for i in range(0, max_op_count)])
  opcodes = operation['Value'][2:] * op_count
  
  return args_pushes + opcodes

def _generate_sstore_cold_no_change_program(operation, op_count, max_op_count):
  """
  Generates a program for SSTORE opcode where every SSTORE stores in a cold storage slot but value is unchanged
  """
  assert operation['Mnemonic'] == 'SSTORE_COLD_NO_CHANGE'

  # store 0 in different slots - values not changed in slots
  args_pushes = ''.join([('5f' + f'60{i:02x}') for i in range(0, max_op_count)])
  opcodes = operation['Value'][2:] * op_count
  
  return args_pushes + opcodes

def _generate_sstore_warm_no_change_program(operation, op_count, max_op_count):
  """
  Generates a program SSTORE opcode where every SSTORE stores in a warm storage slot but value is unchanged
  """
  assert operation['Mnemonic'] == 'SSTORE_WARM_NO_CHANGE'

  args_push = '7f' + 'ff' * 32 + '5f'
  slot_warmup_code = args_push + '55' # SSTORE to slot 0
  args_pushes = args_push * max_op_count
  opcodes = operation['Value'][2:] * op_count
  
  return slot_warmup_code + args_pushes + opcodes

def _generate_sstore_warm_change_program(operation, op_count, max_op_count):
  """
  Generates a program for SSTORE opcode where every SSTORE stores in a warm storage slot and value in the slot is changed
  """
  assert operation['Mnemonic'] == 'SSTORE_WARM_CHANGE'

  slot_warmup_code = '5f5450' # SLOAD from slot 0 and pop
  # store different values in slot 0
  args_pushes = ''.join([(f'60{i:02x}' + '5f') for i in range(1, max_op_count + 1)])
  opcodes = operation['Value'][2:] * op_count
  
  return slot_warmup_code + args_pushes + opcodes


def main():
  fire.Fire(ProgramGenerator, name='generate')


if __name__ == '__main__':
  main()
