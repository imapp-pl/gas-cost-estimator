import csv
import random
from math import ceil

import constants

"""
Common tools for program generation. To be organized if needed, for now just bag of functions.
"""
    

def generate_single_marginal(single_op_pushes, operation, op_count):
  """
  The number of pushes in single_op_pushes must be equal to arity.
  The returned program has the same number of empty pushes, pushes and pops regardless op_count.
  """
  nreturns = int(operation['Added to stack'])

  # i.e. 23 from 0x23
  opcode = operation['Value'][2:4]
  popcode = "50"

  has_parameter = True if 'Parameter' in operation and operation['Parameter'] else False
  if has_parameter:
    opcode += operation['Parameter']

  # support up to 60 instructions
  MAX_INSTRUCTIONS = 60
  assert op_count <= MAX_INSTRUCTIONS
  
  total_pop_count = MAX_INSTRUCTIONS * nreturns
  # support up to 60 ternary instructions
  push_count = MAX_INSTRUCTIONS * 3
  # ...but before the pushes intended for `operation`, put "void" pushes to ensure all the pops can pop regardless of the remainder of the program
  empty_push_count = total_pop_count

  interleaved_op_and_pops_count = max(op_count - 1, 0)
  end_pop_count = total_pop_count - interleaved_op_and_pops_count * nreturns

  # start generation
  bytecode = ''

  # If this is an OPCODE accessing memory, we pre-allocate 128KB of memory at the very beginning
  initial_mstore = initial_mstore_bytecode() if operation['Mnemonic'] in constants.MEMORY_OPCODES else ''
  bytecode += initial_mstore
    
  empty_pushes = ["6000"] * empty_push_count
  bytecode += ''.join(empty_pushes)
  pushes = single_op_pushes * ceil(push_count / arity(operation)) if arity(operation) > 0 else []
  bytecode += ''.join(pushes)

  if operation['Mnemonic'] in ["JUMP", "JUMPI"]:
    # JUMPs don't return anything, we don't POP it, so assertion
    assert nreturns == 0

    empty_combos_count = MAX_INSTRUCTIONS - op_count
    for _ in range(0, op_count):
      bytecode += jump_opcode_combo(bytecode, opcode)
    for _ in range(0, empty_combos_count):
      bytecode += jump_opcode_combo(bytecode, None)
  else:
    if op_count == 0:
      middle = []
      pops = [popcode] * total_pop_count
      bytecode += ''.join(middle + pops)
    elif op_count >= 1:
      middle = [opcode] + ([popcode] * nreturns + [opcode]) * interleaved_op_and_pops_count
      bytecode += ''.join(middle)
      pops = [popcode] * end_pop_count
      bytecode += ''.join(pops)

  # just in case
  assert interleaved_op_and_pops_count * nreturns + end_pop_count == total_pop_count
  assert interleaved_op_and_pops_count >= 0
  assert end_pop_count >= 0

  return bytecode


# Generates the combination of OPCODEs needed to perform a JUMP
# `bytecode` so far, needed to generate a correct JUMPDEST pc
# `opcode` - is that of JUMP or JUMPI. If None, will not put the opcode in at all
def jump_opcode_combo(current_bytecode, opcode):
  current_pc = len(current_bytecode) // 2
  if opcode:
    jumpdest_pc = current_pc + 1 + 3 + 1  # PUSH3, pushed 3 bytes, jump
    return byte_size_push(3, jumpdest_pc) + opcode + '5b'
  else:
    jumpdest_pc = current_pc + 1 + 3  # PUSH3, pushed 3 bytes, no jump here!
    return byte_size_push(3, jumpdest_pc) + '5b'


def prepare_opcodes(opcodes_file):
  with open(opcodes_file) as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    opcodes = {i['Value']: i for i in reader}

  return _fill_opcodes_push_dup_swap(opcodes)


def get_selection(selection_file):
  with open(selection_file) as csvfile:
    reader = csv.DictReader(csvfile, delimiter=' ', quotechar='"')
    return [i['Opcode'] for i in reader]


        
def _fill_opcodes_push_dup_swap(opcodes):
  pushes = constants.EVM_PUSHES
  dups = constants.EVM_DUPS
  swaps = constants.EVM_SWAPS

  pushes = _opcodes_dict_push_dup_swap(pushes, [0] * len(pushes), [1] * len(pushes), parameter='00')
  opcodes = {**opcodes, **pushes}
  # For dups and swaps the removeds/addeds aren't precise. "removed" is how much is required to be on stack
  # so it must be pushed there once. "added" is how much is really added "extra"
  dups = _opcodes_dict_push_dup_swap(dups, range(1, len(dups)), [1] * len(dups))
  opcodes = {**opcodes, **dups}
  swaps = _opcodes_dict_push_dup_swap(swaps, range(2, len(swaps)+1), [0] * len(swaps))
  opcodes = {**opcodes, **swaps}
  return opcodes

def _opcodes_dict_push_dup_swap(source, removeds, addeds, parameter=None):
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

# Returns a single MSTORE8 accompanied with pushes, causing pre-allocation of all the memory at program's disposal
# 6000 - PUSH1 the zero (the byte to store)
# 630001ffff - PUSH4 128KB-worth-of-bytes minus one byte
# 53 - MSTORE8
def initial_mstore_bytecode():
  return "6000630001ffff53"

def arity(operation):
  # We're not analyzing JUMPs for destination arg cost, so pretend it's not there. We're pushing it in the main
  # generation loop.
  if operation["Mnemonic"] == "JUMP":
    return 0
  elif operation["Mnemonic"] == "JUMPI":
    return 1
  else:
    return int(operation["Removed from stack"])


def random_byte_size_push(byte_size):
  value = random.getrandbits(8*byte_size)
  return byte_size_push(byte_size, value)

def byte_size_push(byte_size, value):
  value = hex(value)
  value = value[2:]
  if len(value) < 2*byte_size:
    value = (2*byte_size-len(value))*'0' + value
  # byte_size is also the OPCODE variant
  op_num = 6 * 16 + byte_size - 1  # 0x60 is PUSH1
  op = hex(op_num)[2:]
  return op + value