`opcodes.csv` from https://github.com/djrtwo/evm-opcode-gas-costs/blob/master/opcode-gas-costs_EIP-150_revision-1e18248_2017-04-12.csv
  - UPDATE: RETURNDATASIZE and RETURNDATACOPY from the EIP
  - it's still missing PUSH/DUP/SWAP opcodes in standard format, so the script fills this in
  - UPDATE: REVERT from the EIP

`selection.csv` from specs of "EVM Gas Cost Estimator.pdf"

----

`opcodes_ewasm.csv` from specs of  "EVM Gas Cost Estimator.pdf" with corrections (dropping a stray `f64` instruction).
  - stack requirements taken from [webassenbly.github.io page](https://webassembly.github.io/spec/core/appendix/index-instructions.html)
  - parameters added

`selection_ewasm_from_spec.csv` from specs of "EVM Gas Cost Estimator.pdf"

`selection_ewasm.csv` taken from the above, limited to selection provided by `chfast`, excluding irrelevant flow control meta-instructions.

`selection_ewasm_first_pass.csv` taken from the above, excluding memory instructions and `64` bit instructions for a working first draft program generation
  - UPDATE: `0xC0 i32.extend8_s`, `0xC1 i32.extend16_s` return `Error: EVM: Internal error: Error deserializing contract code (UnknownOpcode(192))` (and `193` resp.) from `openethereum` Ewasm, dropping them for first pass
