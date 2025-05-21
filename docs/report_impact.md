## Gas Cost Changes Impact

The goal of this study is to assess the impact of changes provided by [EIP-7904.](https://github.com/ethereum/EIPs/pull/9454) .

### Tools

The work was performed by re-executing past blocks with modified EVM client that collects required data.
The choice of EVM solely depended on personal preferences,
it should not be considered as any recommendation.
Modified EVM code can be find [here](https://github.com/lukasz-glen/besu/tree/eip-7904) .

### Gas Usage Impact

EIP-7904 decreases gas cost of a number of opcodes and operations.
Specifically, transactions would consume less gas,
allowing more transactions to be included in a block while preserving the block gas limit, thereby increasing transaction
throughput.
This section investigates gas usage changes in terms of quantity.

#### Methodology

Past blocks are used as test data. 
Transactions and blocks are executed and information on executed opcodes and other operations
are collected.
Check the Gas Usage Vector section for details on the structure holding this data.
Using the collected data,
we calculate the total gas cost of a transaction or a block based on the updated gas cost schedule
from EIP-7904.
Note that the past transactions are not re-executed with updated gasometering
as this would affect the blockchain state updates.
Instead, calculations are performed aposteriori,
based solely on the collected data,
assuming the execution sequences remain identical.

This approach provides greater flexibility. 
Any changes in EIP-7904 can be easily applied to this assessment.
Similar assessments can be provided for other gas cost modifications
and data exploration on gas usage.

Low-level data are collected for each call (subcall)
because some gas cost factors are not additive,
for instance, memory expansion cost has quadratic dependence.
Gas costs are calculated for individual calls and then aggregated to obtain gas costs
for transactions and blocks.

Finally, we compare two figures: the original gas usage of a transaction,
and the calculated gas usage assuming EIP-7904.
So the assessment of tx throughput increment is based on the calculated block gas usage decrement
as this is the raw non-experimental data available.

#### Gas Usage Vector

Gas Usage Vector is a fine-grained decomposition of the gas usage to elementary coefficients.
Each coefficient refers to a quantity of a given component that increments gas usage.
Anything that increases gas usage should be reflected as one or more coefficients in Gas Usage Vector,
 including calldata, opcodes, precompiles, access lists, contract creation etc.
This allows to modify gas cost of opcodes and other operations and 
immediately check the results.

To get a better feeling of what is Gas Usage Vector, we give examples.
Each simple opcode, for instance, ADD, PUSH, ADDRESS, etc, refers to one coefficient. 
So if a call executes ADD ten times, then the ADD coefficient is 10.
If there is a formula, then we need more coefficients.
For instance, EXP cost is given with the formula
```text
EXP_OPERATION_BYTE_GAS_COST * numBytes + EXP_OPERATION_BASE_GAS_COST
```
So there are two coefficients: EXP_OPERATION_BYTE_GAS_COST and EXP_OPERATION_BASE_GAS_COST.
The first indicates the exponent byte size, and the latter indicates that EXP was executed.
A bit more complex formula is for BALANCE: the static cost is 0, and there is a cost
for the address access depending on whether the address is cold or warm.
So there are three coefficients: BALANCE, COLD_ACCOUNT_ACCESS_COST, WARM_ACCOUNT_ACCESS_COST.
If BALANCE is executed for a warm address, the coefficients update is (+1, 0, +1).
Note that the static cost for BALANCE is 0, the number of executions is counted anyway.
There are more complex formulas, for instance for SSTORE and CALL.
Briefly, Gas Usage Vector is how many ADDs were executed, how many words were passed to KECCAK256,
how many times cold addresses were accessed, how many non-zero bytes of calldata are stored etc.
Anything that is charged with gas or can be potentially charged.

To get a gas cost of a call we need Gas Cost Vector.
This defines a cost for a unit of every coefficient expressed in gas.
That would be 3 for ADD, 6 for a word pass to KECCAK256,
2600 for accessing a cold address, 16 for non-zero calldata byte, etc.
It is enough to multiply Gas Usage Vector by Gas Cost Vector to get the total call gas cost.

For each hard fork, there is a different Gas Cost Vector.
Updates provided with a hard fork, should be reflected in Gas Cost Vector.

There can be Gas Usage Vector for a single call, a single transaction or a block.
The vectors add additive with an exception:
the formula for memory cost is quadratic,  not linear.
So for memory expansion gas cost, it must be calculated on a per sub-call basis.

It turned out that it is possible to define common coefficients for all hard forks.
Even if some coefficients are absent for older hard forks,
the common denominator is feasible.
For instance the gas cost of (CALL, COLD_ACCOUNT_ACCESS_COST, WARM_ACCOUNT_ACCESS_COST)
is (700, 0, 0) for Spurious Dragon and (0, 2600, 100) for Berlin hard fork.
Note that CALL is the static gas cost for CALL opcode.

#### Development notes

The current implementation does not provide a full decomposition into Gas Usage Vector.
It is enough to satisfy the set goal. 
This section describes deficiencies.

SLOAD and SSTORE opcodes are not decomposed into coefficients.
Raw gas cost is reported instead. 
This is the case for some other complex situations that are not covered by EIP-7904.
If in the future there will be a need to cover a broader scope,
the implementation should be improved.

EOF and EIP-7702 and not supported fully.

The best approach to test gas cost schedule updates is to calculate deltas.
For instance, if a transaction executes ADD ten times and the gas cost is lowered
from 3 to 1, then the transaction gas cost is to be lowered by 20 gas.

#### Results

The examination was performed on the recent blocks, ~50k. 
We calculated the block gas usage decrement if EIP-7904 would be applied (`block_gas_diff`)
and compare it to the actual gas usage (`block_gas_usage`).

The average block gas usage dropped by ~10.51% , this is `sum(block_gas_diff)/sum(block_gas_usage)`.
The lowest observed gas usage % difference (`block_gas_diff/block_gas_usage`) is 0.71%, the greatest is 51.93% .
Only 1.6% of examined blocks have gas usage % difference greater than 20% .

The table below lists the top coefficients that incurred the greatest total gas usage decrement. 

| coefficient |  gas_diff   |  quantity   |
|-------------|-------------|-------------|
|       JUMPI | 17,575,400,880 | 1,952,822,320 |
|        JUMP | 12,533,484,698 | 1,790,497,814 |
|       PUSH1 |  9,133,930,312 | 4,566,965,156 |
|       PUSH2 |  8,021,974,936 | 4,010,987,468 |
| WARM_ACCOUNT_ACCESS_COST |  5,039,345,585 |    53,045,743 |
|       SWAP1 |  4,533,386,998 | 2,266,693,499 |
|        DUP2 |  3,913,028,646 | 1,956,514,323 |
|         ADD |  3,466,653,000 | 1,733,326,500 |
|        DUP1 |  2,998,253,260 | 1,499,126,630 |
|        DUP3 |  2,952,426,624 | 1,476,213,312 |
|         POP |  2,442,509,113 | 2,442,509,113 |
| MEMORY_WORD_GAS_COST |  2,347,206,540 |   782,402,180 |
|      ISZERO |  2,241,865,852 | 1,120,932,926 |
|       SWAP2 |  2,109,683,478 | 1,054,841,739 |
|      MSTORE |  2,016,333,432 | 1,008,166,716 |
|         AND |  1,796,827,030 |   898,413,515 |
|       MLOAD |  1,687,732,210 |   843,866,105 |
|        DUP4 |  1,607,537,108 |   803,768,554 |
|         SUB |  1,317,892,654 |   658,946,327 |
|         MUL |  1,267,239,396 |   316,809,849 |
|       SWAP3 |  1,141,415,996 |   570,707,998 |
|          EQ |  1,046,211,858 |   523,105,929 |
|       PUSH4 |    986,790,438 |   493,395,219 |
|        DUP5 |    980,694,670 |   490,347,335 |
| PRECOMPILED_EC_PAIRING_PARAMETERS |    930,231,000 |        34,453 |
|          LT |    916,069,664 |   458,034,832 |
| EXP_OPERATION_BYTE_GAS_COST |    885,628,662 |    19,252,797 |
|       SWAP4 |    720,757,430 |   360,378,715 |
|         SHL |    706,087,098 |   353,043,549 |
|          GT |    667,116,384 |   333,558,192 |
|         DIV |    664,867,680 |   166,216,920 |
|         SHR |    634,539,262 |   317,269,631 |
|        DUP6 |    563,799,750 |   281,899,875 |
| PRECOMPILED_EC_MUL |    560,673,300 |       169,901 |
|      PUSH20 |    501,783,876 |   250,891,938 |

Blocks with significant block gas usage diff were studied in detail.
Interesting findings are presented.
Additionally, some transactions were verified against transaction traces.

Block 22382018 has 51.93% of gas usage difference. 
It includes four valid transactions, all of which are propagateRoot() of OpStateBridge contract.

| tx hash | gas used | gas diff | % gas diff |
|---------|----------|----------|------------|
| 0xb12f17c3c898063c913876ea10a0c36a846400126abc750da878ad5bc8bc9c41 | 1,209,332 | 803,942 | 66.4% |
| 0x9293eb3dfaacdf9d58e5d7fec8e937c966a18d7ef7bc720cbffa58a8cff5e155 | 1,187,242 | 788,053 | 66.3% |
| 0x0c924a77d95d8b0d50af6b8e295c5131d41ab0988e4d1a66a1666e677e6b1e5d | 1,209,243 | 804,258 | 66.5% |
| 0x7b56d49a9c8bff40b997c6a3d26271d6d5165cf4a4cb4e60a4046f6aa2888da1 | 1,187,325 | 788,493 | 66.4% |

Below is the list of opcodes that have top gas usage difference 
for the transaction 0xb12f17c3c898063c913876ea10a0c36a846400126abc750da878ad5bc8bc9c41 .

| coefficient | gas_diff | quantity   |
|-------------|----------|------------|
|          JUMP |   224,511 |    32,073 |
|          JUMPI |   173,943 |    19,327 |
|          PUSH2 |   102,818 |    51,409 |
|         DUP3 |    64,074 |    32,037 |
|          PUSH1 |    39,318 |    19,659 |
|         SWAP1 |    38,700 |    19,350 |
|          ISZERO |    25,806 |    12,903 |
|          LT |    25,606 |    12,803 |
|           SUB |    25,592 |    12,796 |
|          POP |    19,481 |    19,481 |
|           ADD |    13,432 |     6,716 |
|         DUP4 |    13,140 |     6,570 |
|         SWAP2 |    12,976 |     6,488 |
|         PUSH32 |    12,866 |     6,433 |

Block 22391630 has 41.66% of gas usage difference.
It has one significant transaction - 32,9 Mgas out of 35,98 Mgas block usage -
0x310909437b77352ce160a8585dcab413146b5b312d25b32336a3fee53e0062c0 .
The transaction's gas usage diff is 44.93%.
The transaction transfers 186 NFTs and executes 
enormous number of subcalls - 7074.

| coefficient | gas_diff | quantity | 
|-------------|----------|----------|
|          JUMPI |  2,167,821 |   240,869 | 
|          JUMP |  2,055,256 |   293,608 | 
|          PUSH1 |  1,201,706 |   600,853 | 
|          PUSH2 |  1,125,150 |   562,575 | 
|         WARM_ACCOUNT_ACCESS_COST |    723,710 |     7,618 | 
|           ADD |    598,738 |   299,369 | 
|         DUP2 |    576,302 |   288,151 | 
|          POP |    505,698 |   505,698 | 
|         SWAP1 |    479,950 |   239,975 | 
|         DUP1 |    465,124 |   232,562 | 
|         DUP3 |    370,344 |   185,172 | 
|         MEMORY_WORD_GAS_COST |    352,236 |   117,412 | 
|         SWAP2 |    349,168 |   174,584 | 
|          MSTORE |    327,636 |   163,818 | 
|          AND |    298,970 |   149,485 | 
|          ISZERO |    282,642 |   141,321 | 
|         SWAP3 |    218,532 |   109,266 | 
|         DUP5 |    208,508 |   104,254 | 
|          MLOAD |    205,560 |   102,780 | 
|         DUP4 |    202,548 |   101,274 | 
|           SUB |    146,314 |    73,157 | 
|          PUSH4 |    140,298 |    70,149 | 
|          EQ |    132,558 |    66,279 | 
|         SWAP4 |    130,250 |    65,125 | 
|         DUP6 |    114,340 |    57,170 | 
|          CALLDATALOAD |    100,902 |    50,451 | 
|          GT |    100,204 |    50,102 | 

Typical transactions were investigated to illustrate
impact on regular user activity.

| Transaction | gas used | gas diff | % gas diff |
|-------------|----------|----------|------------|
| USDC transfer | 45,160 | 1,438 | 3.18% |
| USDT transferFrom | 48,518 | 1,332 | 2.74% |
| Uniswap V2 swap | 112,478 | 12,235 | 10.87% |
| Ethena Stake | 69,793 | 4,206 | 6.02% |
| Commit Verification Layer Zero | 76,844 | 5,743 | 7.47% |

### Backwards Compatibility

Backwards Compatibility for this work means that
changes provided by EIP-7904 will not break any existing contract.
It needs to be defined: what is the positive/negative result of verification, 
what are the means to examine contracts.
The task requires some heuristics.

Instead of smartcontract analysis, including static analysis, 
another approach is adopted, based on empirical data.
Each transaction is re-executed in the same context but with modified gasometering
according to EIP-7904.
So we have the original execution of a transaction and the simulation with a modified gasometer.
Re-execution in the same context means that at the beginning the simulation has 
the same blockchain state as the original transaction.
Then the execution outcomes are compared.

Note that different outcomes do not mean automatically that the contract is broken.
Further investigation may be required to diagnose a cause.
This is another work to be done and it requires case by case approach - 
it is not covered by this report.

#### Methodology

The existing blocks are re-executed and included transactions are re-executed
in parallel with two gasometers: the original and the simulation.
The simulation applies the changes defined by EIP-7904.
The procedure is as follows;

1. The next transaction is read.
2. The transaction is executed with the simulation gasometer.
3. The blockchain state update is recorded.
4. The blockchain state is reset. The transaction receipt is not included. Used gas is not accounted for.
5. The transaction is executed with the original gasometer.
6. The blockchain state update is recorded.
7. The blockchain state update is committed.
8. Two blockchain state updates are compared.

Note that these two blockchain state updates are different because 
the account balances are different at the end of a transaction.
So a more subtle approach is required.

Comparison of blockchain state updates is difficult.
Two executions, the original and simulation, almost certainly result
in two different states.
A simplified heuristic is implemented.
We start with the transaction status:

- If the simulation tx status is SUCCESS and the original tx status is SUCCESS,
then the comparison is GOOD.
- If the simulation tx status is FAILED and the original tx status is FAILED,
then the comparison is GOOD.
- If the simulation tx status is SUCCESS and the original tx status is FAILED,
then the comparison is UNKNOWN.
- If the simulation tx status is FAILED and the original tx status is SUCCESS,
then the comparison is BAD.

The outcome BAD indicates that the transaction must be verified against
EIP-7904 changes.
The outcome UNKNOWN seems to be an improvement, but in some cases may need verification.

There are cases where a transaction almost always results with SUCCESS.
For instance, so-called gasless transaction performs a wrapped transaction internally
and the status of the internal call is just recorded in a log instead of being propagated.
For that reason, our heuristic is extended to validate subcalls also.
So the whole tree of subcalls is compared.

