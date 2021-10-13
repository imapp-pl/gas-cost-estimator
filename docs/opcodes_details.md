# Rundown of OPCODE details

This file contains a detailed rundown of all EVM OPCODEs concerned, with notes on their specifics and what to watch our for.

Based on `src/program_generator/data/opcodes.csv` and `src/program_generator/data/selection.csv`.

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

See `ADDRESS`

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

### Parameters

- size of the code?

## `0x39,CODECOPY`

`0x39,CODECOPY,"2 + 3 * (number of words copied, rounded up)",,3,0,Copy code running in current environment to memory.,2 is paid for the operation plus 3 for each word copied (rounded up).`

see `CALLDATACOPY`, everything is same just the data is from the code not input

## `0x3a,GASPRICE`

`0x3a,GASPRICE,2,base,0,1,Get price of gas in current environment.,`

- **geth**: Data is in `interpreter.evm.GasPrice`. It is then loaded from BigInt
- **evmone**: Data is in `state.host.get_tx_context().tx_gas_price` - is getting this always costing the same? **TODO**
- **openethereum**: Data is in `self.params.gas_price.clone()`

### Parameters

Size of the value could have impact (b/c it's loaded from BigInt for `geth` at least)

## `0xfe,INVALID`

`0xfe,INVALID,NA,,NA,NA,Designated invalid instruction.,`

- **geth**: not defined, will short-circuit with `ErrInvalidOpCode` and not be added to the measurements CSV
- **evmone**: sets execution state to invalid instruction and does nothing
- **openethereum**: returns Done with BadInstruction, does nothing.

can be dropped

