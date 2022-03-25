import csv
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
  arity = int(operation['Removed from stack'])
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
    
  empty_pushes = ["6000"] * empty_push_count
  pushes = single_op_pushes * ceil(push_count / arity) if arity > 0 else []

  if op_count == 0:
    middle = []
    pops = [popcode] * total_pop_count
  elif op_count >= 1:
    middle = [opcode] + ([popcode] * nreturns + [opcode]) * interleaved_op_and_pops_count
    pops = [popcode] * end_pop_count

  bytecode = ''.join([initial_mstore_bytecode()] + empty_pushes + pushes + middle + pops)

  # just in case
  assert interleaved_op_and_pops_count * nreturns + end_pop_count == total_pop_count
  assert interleaved_op_and_pops_count >= 0
  assert end_pop_count >= 0

  return bytecode


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
