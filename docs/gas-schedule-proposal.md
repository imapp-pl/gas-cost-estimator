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
| 08 | MULMOD | 8 | 14 |
| 0A | EXP | static_gas = 10 <br/> dynamic_gas = 50 * exponent_byte_size | static_gas = 10 <br/> dynamic_gas = 20 * exponent_byte_size |
| 20 | KECCAK256 | static_gas = 30 <br/> dynamic_gas = 6 * minimum_word_size + memory_expansion_cost | static_gas = 50 <br/> dynamic_gas = 30 * minimum_word_size + memory_expansion_cost |
| 30 | ADDRESS | 2 | 5 |
| 33 | CALLER | 2 | 5 |
| 37 | CALLDATACOPY | static_gas = 3 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost | static_gas = 5 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost |
| 3E | RETURNDATACOPY | static_gas = 3 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost | static_gas = 5 <br/> dynamic_gas = 3 * minimum_word_size + memory_expansion_cost |
| 47 | SELFBALANCE | 5 | 3 |
| 52 | MSTORE | static_gas = 3 <br/> dynamic_gas = memory_expansion_cost | static_gas = 5 <br/> dynamic_gas = memory_expansion_cost |
| 53 | MSTORE8 | static_gas = 3 <br/> dynamic_gas = memory_expansion_cost | static_gas = 5 <br/> dynamic_gas = memory_expansion_cost |
|  | POP | 2 | 1 |
|  | PUSHx | 3 | 2 |
|  | DUPx | 3 | 2 |
|  | SWAPx | 3 | 2 |
| 56 | JUMP | 8 | 3 |
| 57 | JUMPI | 10 | 5 |
| 5C | TLOAD | 100 | 20 |
| 5D | TSTORE | 100 | 50 |
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
| 01 | ECRECOVER | 3000 | 12000 |
| 06 | ECADD | 150 | 3000 |
| 07 | ECMUL | 6000 | 10000 |
| 0A | POINTEVAL | 50000 | 300000 |

In above calculations the `memory_expansion_cost` is calculated as `3 * memory_word_count`. The `topic_count` is the number of topics in the log operation and `size` is the size of the data in the log operation.

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
- The radical changes may have unforeseen consequences

| OPCODE | Name | Current Gas | Proposed Gas |
| ------------- | ------------- | ------------- | ------------- |
|  | ADD | 3 | 1 |
|  | MUL | 5 | 1 |
|  | SUB | 3 | 1 |
|  | DIV | 5 | 1 |
|  | SDIV | 5 | 2 |
|  | MOD | 5 | 1 |
|  | SMOD | 5 | 2 |
|  | ADDMOD | 8 | 2 |
|  | MULMOD | 8 | 4 |
|  | EXP | static_gas = 10 <br/> dynamic_gas = 50 * exponent_byte_size | static_gas = 3 <br/> dynamic_gas = 5 * exponent_byte_size |
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
|  | SHR | 3 | 1 |
|  | SAR | 3 | 2 |
|  | ADDRESS | 2 | 2 |
|  | ORIGIN | 2 | 1 |
|  | CALLER | 2 | 1 |
|  | CALLVALUE | 2 | 1 |
|  | CALLDATALOAD | 3 | 1 |
|  | CALLDATASIZE | 2 | 1 |
|  | CALLDATACOPY | 2 | 3 |
|  | CODESIZE | 2 | 1 |
|  | CODECOPY | 2 | 3 |
|  | GASPRICE | 2 | 1 |
|  | RETURNDATASIZE | 2 | 1 |
|  | RETURNDATACOPY | 3 | 3 |
|  | COINBASE | 2 | 1 |
|  | TIMESTAMP | 2 | 1 |
|  | NUMBER | 2 | 1 |
|  | DIFFICULTY | 2 | 1 |
|  | GASLIMIT | 2 | 1 |
|  | CHAINID | 2 | 1 |
|  | SELFBALANCE | 5 | 1 |
|  | POP | 2 | 1 |
|  | MLOAD | 3 | 1 |
|  | MSTORE | 3 | 2 |
|  | MSTORE_COLD | 3 | 3 |
|  | MSTORE8 | 3 | 1 |
|  | JUMP | 8 | 1 |
|  | JUMPI | 10 | 1 |
|  | PC | 2 | 1 |
|  | MSIZE | 2 | 1 |
|  | GAS | 2 | 1 |
|  | JUMPDEST | 1 | 1 |
|  | PUSHx | 3 | 1 |
|  | DUPx | 3 | 1 |
|  | SWAPx | 3 | 1 |
|  | MCOPY | 6 | 2 |
|  | MCOPY_COLD | 6 | 2 |
|  | PUSH0 | 2 | 1 |
|  | KECCAK256 | static_gas = 30 <br/> dynamic_gas = 6 * minimum_word_size + memory_expansion_cost | static_gas = 30 <br/> dynamic_gas = 6 * minimum_word_size + memory_expansion_cost |
|  | LOG0 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 10 <br/> dynamic_gas = 5 * topic_count + 3 * size + memory_expansion_cost |
|  | LOG1 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 10 <br/> dynamic_gas = 5 * topic_count + 3 * size + memory_expansion_cost |
|  | LOG2 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 10 <br/> dynamic_gas = 5 * topic_count + 3 * size + memory_expansion_cost |
|  | LOG3 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 10 <br/> dynamic_gas = 5 * topic_count + 3 * size + memory_expansion_cost |
|  | LOG4 | static_gas = 375 <br/> dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost | static_gas = 10 <br/> dynamic_gas = 5 * topic_count + 3 * size + memory_expansion_cost |
|  | EXTCODEHASH | 100 | 6 |
|  | EXTCODESIZE | 100 | 5 |
|  | EXTCODECOPY | 100 | 5 |
|  | CREATE | 32000 | 182 |
|  | CALL | address_access_cost = 100 (warm address) | address_access_cost = 50 (warm address) |
|  | STATICCALL | address_access_cost = 100 (warm address) | address_access_cost = 50 (warm address) |
|  | DELEGATECALL | address_access_cost = 100 (warm address) | address_access_cost = 50 (warm address) |
|  | RETURN | static_gas = 0 <br/> dynamic_gas = memory_expansion_cost | static_gas = 2 <br/> dynamic_gas = memory_expansion_cost |
|  | REVERT | static_gas = 0 <br/> dynamic_gas = memory_expansion_cost | static_gas = 3 <br/> dynamic_gas = memory_expansion_cost |
|  | TLOAD | 100 | 5 |
|  | TSTORE | 100 | 7 |

| Precompile | Name | Current Gas | Proposed Gas |
| ------------- | ------------- | ------------- | ------------- |
|  | ECRECOVER | 3000 | 4382 |
|  | SHA2-256 | 72 | 40 |
|  | RIPEMD-160 | 720 | 71 |
|  | IDENTITY | 18 | 33 |
|  | MODEXP | 200 | 110 |
|  | ECADD | 150 | 937 |
|  | ECMUL | 6000 | 3060 |
|  | ECPAIRING79000 | 79000 | 21362 |
|  | ECPAIRING113000 | 113000 | 31213 |
|  | ECPAIRING181000 | 181000 | 50909 |
|  | ECPAIRING317000 | 317000 | 89881 |
|  | BLAKE2F | 12 | 51 |
|  | POINTEVAL | 50000 | 101109 |

In above calculations the `memory_expansion_cost` is calculated as `1 * memory_word_count`. The `topic_count` is the number of topics in the log operation and `size` is the size of the data in the log operation. The rescale factor is 0.5/1.704212172, based on the least expensive, non-trivial opcode `ISZERO`.

