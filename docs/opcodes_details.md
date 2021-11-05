# Rundown of OPCODE details

This file contains a detailed rundown of all EVM OPCODEs concerned, with notes on their specifics and what to watch our for.

Based on `src/program_generator/data/opcodes.csv` and `src/program_generator/data/selection.csv`.

## Takeaways

See below for a detailed OPCODE-by-OPCODE description of parameters and concerns.
This is a proposed list of things to tackle, in order from important to negligible:

- parametrize values on the stack taken for stack-only operations, see sections `0x01,ADD`, `0x0a,EXP`
- parametrize amount of memory allocation using memory read/write OPCODEs, see section `0x52,MSTORE`
- parametrize `JUMP` AND `JUMPI` calls circumstances, see their sections
- parametrize `JUMPDEST` calls circumstances, see section
- parametrize amount of memory copying and padding, see sections `0x37,CALLDATACOPY`, `0x39,CODECOPY`, `0x3e,RETURNDATACOPY`
- parametrize size of the stack, see sections `0x50,POP` `0x60,PUSH1` `0x80,DUP1`
- parametrize amount of memory allocation using OPCODEs other than MLOAD, see sections `0x37,CALLDATACOPY`, `0x39,CODECOPY`, `0x3e,RETURNDATACOPY`, `0xf3,RETURN`
- parametrize context values, see sections `0x30,ADDRESS` `0x32,ORIGIN` `0x33,CALLER` `0x34,CALLVALUE` `0x3a,GASPRICE` `0x41,COINBASE`
  - in particular parametrize BigInt-based variables: `0x3a,GASPRICE`, `0x34,CALLVALUE`

## `0x00,STOP`

`0x00,STOP,0,zero,0,0,Halts execution.,`

- **geth**: does completely nothing
- **evmone**: sets execution state to success and does nothing
- **openethereum**: sets execution state to done and does nothing

can be dropped

## `0x01,ADD` and other binary/ternary arithmetic/logical OPCODEs

The "simple" ones

```
0x01,ADD,3,verylow,2,1,Addition operation,
0x02,MUL,5,low,2,1,Multiplication operation.,
0x03,SUB,3,verylow,2,1,Subtraction operation.,
0x04,DIV,5,low,2,1,Integer division operation.,
0x05,SDIV,5,low,2,1,Signed integer division operation (truncated).,
0x06,MOD,5,low,2,1,Modulo remainder operation,
0x07,SMOD,5,low,2,1,Signed modulo remainder operation.,
0x08,ADDMOD,8,mid,3,1,Modulo addition operation.,
0x09,MULMOD,8,mid,3,1,Modulo multiplication operation.,
0x0b,SIGNEXTEND,5,low,2,1,Extend length of two’s complement signed integer.,
0x10,LT,3,verylow,2,1,Less-than comparison.,
0x11,GT,3,verylow,2,1,Greater-than comparison.,
0x12,SLT,3,verylow,2,1,Signed less-than comparison.,
0x13,SGT,3,verylow,2,1,Signed greater-than comparison.,
0x14,EQ,3,verylow,2,1,Equality comparison.,
0x15,ISZERO,3,verylow,1,1,Simple not operator.,
0x16,AND,3,verylow,2,1,Bitwise AND operation.,
0x17,OR,3,verylow,2,1,Bitwise OR operation,
0x18,XOR,3,verylow,2,1,Bitwise XOR operation.,
0x19,NOT,3,verylow,1,1,Bitwise NOT operation.,
0x1a,BYTE,3,verylow,2,1,Retrieve single byte from word,
0x1b,SHL,3,verylow,2,1,Left shift operation,
0x1c,SHR,3,verylow,2,1,Logical right shift operation,
0x1d,SAR,3,verylow,2,1,Arithmetic (signed) right shift operation,
```

They pop and push, or pop and peek and then modify stack in-place.

### Parameters

2 or 3 values on the stack, should not have impact on cost.

## `0x0a,EXP`

`0x0a,EXP,(exp == 0) ? 10 : (10 + 10 * (1 + log256(exp))),,2,1,Exponential operation.,"If exponent is 0, gas used is 10. If exponent is greater than 0, gas used is 10 plus 10 times a factor related to how large the log of the exponent is."`

### Parameters

2 values on the stack. Second (`exponent`) will have impact on cost (exponentiation by squaring in all 3 impls).

## `0x30,ADDRESS`

`0x30,ADDRESS,2,base,0,1,Get address of currently executing account.,`

- **geth**: uses `uint256`'s `SetBytes`, but is setting 20 bytes always probably. The addresss is in `callContext.contract.Address()`.
- **evmone**: uses `memcpy` dependant on the address binary size, but the latter is 20 bytes always probably. The address is in `state.msg.destination`.
- **openethereum**: not sure, probably same as others. The address is in `self.params.address.clone()`

### Parameters

Value (non-zeroness) of the address, e.g. `0x0` vs nonzero address? probably not, as zero-address are likely still represented as full 20 bytes in all impls.

So none.

## `0x32,ORIGIN`

`0x32,ORIGIN,2,base,0,1,Get execution origination address.,`

See `ADDRESS`

- **geth**: Data is in `interpreter.evm.Origin.Bytes()`
- **evmone**: Data is in `state.host.get_tx_context().tx_origin` - is getting this always costing the same? **TODO**
- **openethereum**: Data is in `self.params.origin.clone()`

## `0x33,CALLER`

`0x33,CALLER,2,base,0,1,Get caller address.,`

- **geth**: Data is in `callContext.contract.Caller().Bytes()` - is getting this always costing the same? **TODO**
- **evmone**: Data is in `state.msg.sender`
- **openethereum**: Data is in `self.params.sender.clone()`

## `0x34,CALLVALUE`

`0x34,CALLVALUE,2,base,0,1,Get deposited value by the instruction/transaction responsible for this execution.,`

- **geth**: Data is in `callContext.contract.value`. It is then loaded from BigInt
- **evmone**: Data is in `state.msg.value`
- **openethereum**: Data is in `self.params.value`. It is then unpacked from some special type

### Parameters

Size of the value could have impact (b/c it's loaded from BigInt for `geth` at least)

## `0x35,CALLDATALOAD`

`0x35,CALLDATALOAD,3,verylow,1,1,Get input data of current environment.,`

- **geth**: Data is in `callContext.contract.Input`.
- **evmone**: Data is in `state.msg.input_data`.
- **openethereum**: Data is in `self.params.data`.

### Parameters

Things might depend on `state.msg.input_size` and if the `offset+32` fits into the `input_size`. 
**TODO** does the cost vary if incomplete chunk of data is read?

## `0x36,CALLDATASIZE`

`0x36,CALLDATASIZE,2,base,0,1,Get size of input data in current environment.,`

- **geth**: Data is in `len(callContext.contract.Input)`.
- **evmone**: Data is in `state.msg.input_size`.
- **openethereum**: Data is in `self.params.data.as_ref().map_or(0, |l| l.len())`. Will `None` in `data` have different cost? probably negligible.

no comments here, I can't imagine sizing could depend on anything.

## `0x37,CALLDATACOPY`

`0x37,CALLDATACOPY,"2 + 3 * (number of words copied, rounded up)",,3,0,Copy input data in current environment to memory.,2 is paid for the operation plus 3 for each word copied (rounded up).`

- **geth**: Data is in `callContext.contract.Input`. It is copied to a memory spot depending on the offset `callContext.memory.Set(memOffset64...`, so `memory` is also an input
- **evmone**: Data is in `state.msg.input_data` / `state.msg.input_size`. Memory in `state.memory`
- **openethereum**: Data is in `self.params.data`. Memory in `self.mem`

### Parameters

- size of data actually copied (depends on the contents of input and the memory offsets)
- amount of memory allocated
- amount of padding done

## `0x38,CODESIZE`

`0x38,CODESIZE,2,base,0,1,Get size of code running in current environment.,`

- **geth**: Data is in `len(callContext.contract.Code)`
- **evmone**: Data is in `state.code.size()`
- **openethereum**: Data is in `self.reader.len()`

no comments here, I can't imagine sizing could depend on anything.

## `0x39,CODECOPY`

`0x39,CODECOPY,"2 + 3 * (number of words copied, rounded up)",,3,0,Copy code running in current environment to memory.,2 is paid for the operation plus 3 for each word copied (rounded up).`

- **geth**: Data is in `callContext.contract.Code`
- **evmone**: Data is in `state.code`
- **openethereum**: Data is in `self.reader.code`

see `CALLDATACOPY`, everything is same just the data is from the code not input

## `0x3a,GASPRICE`

`0x3a,GASPRICE,2,base,0,1,Get price of gas in current environment.,`

- **geth**: Data is in `interpreter.evm.GasPrice`. It is then loaded from BigInt
- **evmone**: Data is in `state.host.get_tx_context().tx_gas_price` - is getting this always costing the same? **TODO**
- **openethereum**: Data is in `self.params.gas_price.clone()`

### Parameters

Size of the value could have impact (b/c it's loaded from BigInt for `geth` at least)

## `0x3d,RETURNDATASIZE`

`0x3d,RETURNDATASIZE,2,,0,1,Pushes the size of the return data buffer onto the stack,`

- **geth**: Data is in `len(interpreter.returnData)`
- **evmone**: Data is in `state.return_data.size()`
- **openethereum**: Data is in `self.return_data.len()`

no comments here, I can't imagine sizing could depend on anything.

## `0x3e,RETURNDATACOPY`

`0x3e,RETURNDATACOPY,"3 + 3 * ceil(amount / 32)",,3,0,This opcode has similar semantics to CALLDATACOPY, but instead of copying `

- **geth**: Data is in `interpreter.returnData`
- **evmone**: Data is in `state.return_data`
- **openethereum**: Data is in `self.return_data`

see `CALLDATACOPY`, everything is same just the data is from the code not input

## `0x41,COINBASE` and friends

`0x42,TIMESTAMP`, `0x43,NUMBER`, `0x44,DIFFICULTY`, `0x45,GASLIMIT` all follow COINBASE's example, just picking different fields from the same structures.

`0x41,COINBASE,2,base,0,1,Get the block’s beneficiary address.,`

- **geth**: Data is in `interpreter.evm.Context.Coinbase.Bytes()`
- **evmone**: Data is in `state.host.get_tx_context().block_coinbase`
- **openethereum**: Data is in `ext.env_info().author.clone()`

## `0x50,POP`

`0x50,POP,2,base,1,0,Remove item from stack.,`

### Parameters

- size of the stack?

## `0x51,MLOAD`

`0x51,MLOAD,3,verylow,1,1,Load word from memory.,`

no comments here

## `0x52,MSTORE` and the 8bit friend

`0x52,MSTORE,3,verylow,2,0,Save word to memory,`
`0x53,MSTORE8,3,verylow,2,0,Save byte to memory.,`

### Parameters

- amount of memory allocated (depending on the store index requested)

## `0x56,JUMP`

`0x56,JUMP,8,mid,1,0,Alter the program counter,`

- **geth** - just validates and sets PC, simple
- **evmone** - the code block pre-processing might heavily impact cost (ask PB **TODO**)
- **openethereum** - jumptable is initialized on first JUMP!

### Parameters

- first vs subsequent jumps, esp. for large jumptables. **TODO**: specify this better.
- size of jumptable

## `0x57,JUMPI`

`0x57,JUMPI,10,high,2,0,Conditionally alter the program counter.,`

JUMPI only differs by checking the condition on the stack.
Similar comments apply

### Parameters

- same as for JUMP
- whether the jump actually happens or not!

## `0x58,PC`

`0x58,PC,2,base,0,1,Get the value of the program counter prior to the increment corresponding to this instruction.,`

no comments here

## `0x59,MSIZE`

`0x59,MSIZE,2,base,0,1,Get the size of active memory in bytes.,`

no comments here, I can't imagine sizing the memory variable could depend on anything.

## `0x5a,GAS`

`0x5a,GAS,2,base,0,1,"Get the amount of available gas, including the corresponding reduction for the cost of this instruction.",`

Implementation differ due to different approaches to gas tracking, but I don't see any hidden parameters to account for.

## `0x5b,JUMPDEST`

`0x5b,JUMPDEST,1,,0,0,Mark a valid destination for jumps,`

- **geth** noop
- **evmone** not a noop, flushes some gas calculations for the code block. Note - JUMPDEST is rewriten to a `evmone`-specific OPX_BEGINBLOCK
- **openethereum** noop

### Parameters

- the size of preceeding/following code block

## `0x60,PUSH1` and friends

`0x60 -- 0x7f,PUSH*,3,verylow,0,1,Place * byte item on stack. 0 < * <= 32,`

- **geth** `PUSH1` is a special case
- **evmone** `PUSH1`-`PUSH8` are special optimized cases. Also the push contents seem to be prepared in the analysis step
- **openethereum** -

### Parameters

- cost can be slightly different, if PUSHx doesn't have x bytes left in the code. Not sure if this is worth measuring though (**TODO**)

## `0x80,DUP1` and friends, cousin `0x90,SWAP1` and his friends too

`0x80 -- 0x8f,DUP*,3,verylow,*,* + 1,Duplicate *th stack item. 0 < * <= 16,`
`0x90 -- 0x9f,SWAP*,3,verylow,* + 1,* + 1,Exchange 1st and (* + 1)th stack items.,`

straightforward in all impls. No comments.

## `0xf3,RETURN` and `0xfd,REVERT`

`0xf3,RETURN,0,zero,2,0,Halt execution returning output data.,`
`0xfd,REVERT,,,2,0,End execution, revert state changes, return data mem[p…(p+s)),`

- **evmone** - does a check_memory (**TODO** clarify with PB) and also does a micro-optimization for `size == 0`

### Parameters

needs clarifying the above TODO

## `0xfe,INVALID`

`0xfe,INVALID,NA,,NA,NA,Designated invalid instruction.,`

- **geth**: not defined, will short-circuit with `ErrInvalidOpCode` exception and not be added to the measurements CSV
- **evmone**: sets execution state to invalid instruction and does nothing
- **openethereum**: returns Done with BadInstruction, does nothing.

can be dropped

## Misc notes

- `BEGINSUB, JUMPSUB and RETURNSUB` are implemented in `openethereum` and `geth`, but they're only proposed in a pending https://eips.ethereum.org/EIPS/eip-2315.