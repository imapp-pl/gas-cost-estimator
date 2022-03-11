from math import ceil

"""
Common tools for program generation. To be organized if needed, for now just bag of functions.
"""
    

def generate_single_marginal(single_op_pushes, arg_bit_sizes, operation, op_count):
  """
  
  """
  arity = int(operation['Removed from stack'])
  nreturns = int(operation['Added to stack'])

  # i.e. 23 from 0x23
  opcode = operation['Value'][2:4]
  popcode = "50"

  has_parameter = True if 'Parameter' in operation and operation['Parameter'] else False
  if has_parameter:
    opcode += operation['Parameter']

  MAX_INSTRUCTIONS = 60
  # support up to 60 instructions
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

  bytecode = ''.join(empty_pushes + pushes + middle + pops)

  # just in case
  assert interleaved_op_and_pops_count * nreturns + end_pop_count == total_pop_count
  assert interleaved_op_and_pops_count >= 0
  assert end_pop_count >= 0

  return bytecode
