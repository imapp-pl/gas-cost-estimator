# Gas Schedule Proposal

> **_NOTE:_**  This document is a work in progress. The * denotes incomplete parts.

## Overview

Based on the current [reasearch](report_stage_iv.md) we propose a new gas cost schedule for the Ethereum Virtual Machine (EVM). The current gas schedule is based on the original [yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf) and has seldom been updated since the launch of the Ethereum mainnet. The current gas schedule has a number of issues that have been identified in the research. The proposed gas schedules aim to address these issues and provide a more accurate representation of the computational cost of EVM operations.

While the measurements in the Stage IV report are based on solid reasearch, the proposed gas cost schedule is more subjective. This is why we propose two different gas schedules: a conservative one and a radical one. Each having pros and cons. 

## Conservative Gas Schedule Proposal

The idea behind the conservative gas schedule is to limit changes only to the most mispriced elements. By doing so, we aim to minimize the impact on the existing ecosystem, while still improving security. This should be also easier to implement, as it requires less changes to the existing codebases in EVM clients.

The opcodes that are proposed to be changed are those that have been identified as mispriced in the research. 

| OPCODE | Name | Current Gas | Proposed Gas |
| ------------- | ------------- | ------------- | ------------- |
| 02 | MUL | 5 | 3 |
| 08 | MULMOD | 8 | 14 |
| 0A | EXP | static_gas = 10 <br/> dynamic_gas = 50 * exponent_byte_size | static_gas = 10 <br/> dynamic_gas = 20 * exponent_byte_size |
| 20 | KECCAK256 | static_gas = 30 <br/> dynamic_gas = 6 * minimum_word_size + memory_expansion_cost | static_gas = 50 <br/> dynamic_gas = 30 * minimum_word_size + memory_expansion_cost |
| 30 | ADDRESS | 2 | 5 |
| 33 | CALLER | 2 | 5 |
| 37 | CALLDATACOPY | static_gas = 3 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost | static_gas = 8 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost |
| 3E | RETURNDATACOPY | static_gas = 3 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost | static_gas = 8 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost |
| 47 | SELFBALANCE | 5 | 3 |
| 52 | MSTORE | static_gas = 3 <br/> dynamic_gas = memory_expansion_cost | static_gas = 5 <br/> dynamic_gas = memory_expansion_cost |
| 53 | MSTORE8 | static_gas = 3 <br/> dynamic_gas = memory_expansion_cost | static_gas = 5 <br/> dynamic_gas = memory_expansion_cost |
| 56 | JUMP | 8 | 3 |
| 57 | JUMPI | 10 | 5 |
| A0 | LOG0 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 35 <br/> dynamic_gas = 35 * topic_count + 8 * size + memory_expansion_cost |
| A1 | LOG1 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 35 <br/> dynamic_gas = 35 * topic_count + 8 * size + memory_expansion_cost |
| A2 | LOG2 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 35 <br/> dynamic_gas = 35 * topic_count + 8 * size + memory_expansion_cost |
| A3 | LOG3 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 35 <br/> dynamic_gas = 35 * topic_count + 8 * size + memory_expansion_cost |
| A4 | LOG4 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 35 <br/> dynamic_gas = 35 * topic_count + 8 * size + memory_expansion_cost |
| F1 | CALL | address_access_cost = 100 (warm address) | address_access_cost = 150 (warm address) |
| F4 | DELEGATECALL | address_access_cost = 100 (warm address) | address_access_cost = 150 (warm address) |
| FA | STATICCALL | address_access_cost = 100 (warm address) | address_access_cost = 150 (warm address) |
| F3 | RETURN | static_gas = 0 <br/> dynamic_gas = memory_expansion_cost | static_gas = 5 <br/>dynamic_gas = memory_expansion_cost |
| FD | REVERT | static_gas = 0 <br/> dynamic_gas = memory_expansion_cost | static_gas = 8 <br/>dynamic_gas = memory_expansion_cost |


| Precompile | Name | Current Gas | Proposed Gas |
| ------------- | ------------- | ------------- | ------------- |
| 01 | ECRECOVER | 3000 | 17000 |
| 06 | ECADD | 150 | 3500 |
| 07 | ECMUL | 6000 | 10000 |
| 0A | POINTEVAL | 50000 | 400000 |


## Radical Gas Schedule Proposal
The idea behind the radical gas schedule proposal is a complete overhaul of the current gas schedule. Rather than just changing the most mispriced opcodes, we propose to change all opcodes to better reflect the computational cost of the operations.

Let's run through the consequences of the radical gas schedule proposal. The cheapest operations are priced at 1 gas and we gradually increase the gas cost for more complex operations. As a result most arithmetic and basic opcodes will be much cheaper, i.e. valued at 1 rather than 3 or 5. Then all other operations will be adjusted accordingly, usually by lowering the gas cost. This matches some of the [sentiments](https://x.com/VitalikButerin/status/1849338545498210652) in the community.

> Client Implementation notes:
> In most implementations gas cost is hardcoded. Such radical changes to the gas schedule would require a configurable gas schedule in EVM clients. This would allow clients to easily switch between different gas schedules, but also different chains.

In this scenario the storage cost remains at the same level as this refects the network cost of storing data. Thus the radical gas schedule proposal expands the gap between the cost of storage and computation. This is a good thing as it makes it more expensive to store data than to compute it. Also the memory expansion cost remains the same to increase the security of the network.

Pros:
- The gas cost reflects the computational cost of the operations
- The larger gap between the cost of storage and computation promotes more efficient use of the network
- Configurable gas schedules are easier update in the future
- Configurable gas schedules can better match L2 chain requirements

Cons:
- EVM Clients need to implement configurable gas schedules

| OPCODE | Name | Current Gas | Proposed Gas |
| ------------- | ------------- | ------------- | ------------- |
|  | ADD | 3 | 1 |
|  | MUL | 5 | 1 |
|  | SUB | 3 | 1 |
|  | DIV | 5 | 2 |
|  | SDIV | 5 | 3 |
|  | MOD | 5 | 2 |
|  | SMOD | 5 | 3 |
|  | ADDMOD | 8 | 3 |
|  | MULMOD | 8 | 5 |
|  | EXP | static_gas = 10 <br/> dynamic_gas = 50 * exponent_byte_size | static_gas = 5 <br/> dynamic_gas = 10 * exponent_byte_size |
|  | SIGNEXTEND | 5 | 2 |
|  | LT | 3 | 1 |
|  | GT | 3 | 1 |
|  | SLT | 3 | 1 |
|  | SGT | 3 | 1 |
|  | EQ | 3 | 1 |
|  | ISZERO | 3 | 1 |
|  | AND | 3 | 1 |
|  | OR | 3 | 1 |
|  | XOR | 3 | 1 |
|  | NOT | 3 | 1 |
|  | BYTE | 3 | 1 |
|  | SHL | 3 | 2 |
|  | SHR | 3 | 2 |
|  | SAR | 3 | 2 |
| 20 | KECCAK256 | static_gas = 30 <br/> dynamic_gas = 6 * minimum_word_size + memory_expansion_cost | static_gas = 30 <br/> dynamic_gas = 15 * minimum_word_size + memory_expansion_cost |
|  | ADDRESS | 2 | 2 |
|  | ORIGIN | 2 | 1 |
|  | CALLER | 2 | 2 |
|  | CALLVALUE | 2 | 1 |
|  | CALLDATALOAD | 3 | 1 |
|  | CALLDATASIZE | 2 | 1 |
| 37 | CALLDATACOPY | static_gas = 3 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost | static_gas = 8 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost |
|  | CODESIZE | 2 | 1 |
|  | CODECOPY | 2 | 3 |
|  | GASPRICE | 2 | 1 |
|  | RETURNDATASIZE | 2 | 1 |
| 3E | RETURNDATACOPY | static_gas = 3 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost | static_gas = 8 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost |
|  | COINBASE | 2 | 1 |
|  | TIMESTAMP | 2 | 1 |
|  | NUMBER | 2 | 1 |
|  | DIFFICULTY | 2 | 1 |
|  | GASLIMIT | 2 | 1 |
|  | CHAINID | 2 | 1 |
|  | SELFBALANCE | 5 | 2 |
|  | POP | 2 | 1 |
|  | MLOAD | 3 | 2 |
| 52 | MSTORE | static_gas = 3 <br/> dynamic_gas = memory_expansion_cost | static_gas = 2 <br/> dynamic_gas = memory_expansion_cost |
| 53 | MSTORE8 | static_gas = 3 <br/> dynamic_gas = memory_expansion_cost | static_gas = 2 <br/> dynamic_gas = memory_expansion_cost |
|  | JUMP | 8 | 1 |
|  | JUMPI | 10 | 2 |
|  | PC | 2 | 1 |
|  | MSIZE | 2 | 1 |
|  | GAS | 2 | 1 |
|  | JUMPDEST | 1 | 1 |
|  | PUSHx | 3 | 1 |
|  | DUPx | 3 | 1 |
|  | SWAPx | 3 | 1 |
|  | MCOPY | 6 | 2 |
|  | MCOPY_COLD | 6 | 3 |
|  | PUSH0 | 2 | 1 |
|  | KECCAK256 | 36 | 56 |
|  | LOG0 | 375 | 14 |
|  | LOG1 | 750 | 23 |
|  | LOG2 | 1125 | 25 |
|  | LOG3 | 1500 | 27 |
|  | LOG4 | 1500 | 27 |
|  | EXTCODEHASH | 100 | 8 |
|  | EXTCODESIZE | 100 | 7 |
|  | EXTCODECOPY | 100 | 6 |
|  | CREATE | 32000 | 15 |
|  | CALL | 100 | 72 |
|  | STATICCALL | 100 | 65 |
|  | DELEGATECALL | 100 | 60 |
|  | RETURN | 0 | 3 |
|  | REVERT | 0 | 7 |


| Precompile | Name | Current Gas | Proposed Gas |
| ------------- | ------------- | ------------- | ------------- |
|  | ECRECOVER | 3100 | 7064 |
|  | SHA2-256 | 172 | 88 |
|  | RIPEMD-160 | 820 | 121 |
|  | IDENTITY | 118 | 67 |
|  | MODEXP | 300 | 205 |
|  | ECADD | 250 | 1497 |
|  | ECMUL | 6100 | 4286 |
|  | ECPAIRING79000 | 79100 | 43654 |
|  | ECPAIRING113000 | 113100 | 62280 |
|  | ECPAIRING181000 | 181100 | 99527 |
|  | ECPAIRING317000 | 317100 | 174058 |
|  | BLAKE2F | 112 | 79 |
|  | POINTEVAL | 50100 | 162097 |
