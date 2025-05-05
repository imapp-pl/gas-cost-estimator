
### Gas Cost Changes Impact

The goal is to assess the impact of changes provided by EIP-7904 on gas usage.
In particular, transactions would be less gas consuming so tx throughput would increase
as more transactions could be included in a block preserving the block gas limit.

#### Methodology

Past blocks are considered as test data. 
Transactions and blocks are executed and information on executed opcodes and other operations
are collected.
Check the Gas Usage Vector section for details on the structure that holds that data.
With the collected data,
we calculate the total gas cost of a transaction or a block with updated gas cost schedule
according to changes provided by EIP-7904.
Note that the past transactions are not re-executed with updated gasometering
as it would affect the transactions results in terms of blockchain state updates.
The calculations are rather performed aposteriori,
they are based only on the collected data,
so it is assumed that the execution sequences are exactly the same.

This approach provides greater flexibility. 
Any changes in EIP-7904 can be easily applied for this assessment.
Similar assessments can be provided for other gas cost modifications
and data exploration on gas usage.

Low level data are collected for each call (subcall)
because some gas cost factors are not additive,
for instance memory expansion cost has quadratic dependence.
Gas cost is calculated for the calls, then they are aggregated
to obtain gas cost for transactions and for the blocks.

Finally, we compare two figures: the original gas usage of a transaction,
and the calculated gas usage assuming EIP-7904.
So the assessment of tx throughput increment is based on the calculated block gas usage decrement
as this is the raw non-experimental data available.

#### Gas Usage Vector

Gas Usage Vector is a fine grained decomposition of the gas usage to elementary coefficients.
Each coefficient refers to a quantity of a given component that increments gas usage.
Anything that increases gas usage should be reflected as one or more coefficients in Gas Usage Vector,
including calldata, opcodes, precompiles, access lists, contract creation etc.
This allows to modify gas cost of opcodes and other operations and 
immediately check the results.

To get a better feeling what is Gas Usage Vector, we give examples.
Each simple opcode, for instance ADD, PUSH, ADDRESS, etc, refers to one coefficient. 
So if a call executes ADD ten times, then the ADD coefficient is 10.
If there is a formula, then we need more coefficients.
For instance, EXP cost is given with the formula
```text
EXP_OPERATION_BYTE_GAS_COST * numBytes + EXP_OPERATION_BASE_GAS_COST
```
So there are two coefficients: EXP_OPERATION_BYTE_GAS_COST and EXP_OPERATION_BASE_GAS_COST.
The first indicates the exponent byte size, the latter indicates that EXP was executed.
A bit more complex formula is for BALANCE: the static cost is 0, and there is a cost
for the address access depending on whether the address is cold or warm.
So there are three coefficients: BALANCE, COLD_ACCOUNT_ACCESS_COST, WARM_ACCOUNT_ACCESS_COST.
If BALANCE is executed for a warm address, the coefficients update is (+1, 0, +1).
Note that the static cost for BALANCE is 0, the number of executions is counted anyway.
There are more complex formulas, for instance for SSTORE and CALL.
Briefly, Gas Usage Vector is how many ADDs were executed, how many words were pass to KECCAK256,
how many times cold addresses were accessed, how many non zero bytes of calldata is stored etc.
Anything that is charged with gas or can be potentially charged.

To get a gas cost of a call we need Gas Cost Vector.
This defines a cost for a unit of every coefficient expressed in gas.
That would be 3 for ADD, 6 for a word pass to KECCAK256,
2600 for accesssing a cold address, 16 for non zero calldata byte, etc.
It is enough to multiply Gas Usage Vector by Gas Cost Vector to get total call gas cost.

For each hard fork, there is a different Gas Cost Vector.
Updates provided with a hard fork, should be reflected in Gas Cost Vector.

There can be Gas Usage Vector for a single call, a single transaction or a block.
The vectors add additive with an expection:
the formula for memory cost is quadratic,  non linear.
So for memory expansion gas cost, it must be calculated on per sub-call basis.

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
If in the future there will be a need to cover broader scope,
the implementation should be improved.

EOF and EIP-7702 and not supported fully.

The best approach to test gas cost schedule updates is to calculate deltas.
For instance, if a transaction executes ADD ten times and gas cost is lowered
from 3 to 1, then the trasaction gas cost is to be lowered by 20 gas.

### Backwards Compatibility

Backwards Compatibility for this work means that
changes provided by EIP-7904 will not break any existing contract.
It needs to be defined: what is positive/negative result of verification, 
what are means to examine contracts.
The task requires some heuristics.

Instead of smartcontract analysis, including static analysis, 
another approach is adopted, based on empiric data.
Each transaction is re-executed in the same context but with modified gasometering
according to EIP-7904.
So we have the original execution of transaction and the simulation with modified gasometer.
Re-exucution in the same context means that at the beginning the simulation has 
the same blockchain state as the original transaction.
Then the execution outcomes are compared.

Note that different outcomes does not mean automatically that the contract is broken.
Further investigation may be require to diagnose a cause.
This is another work to be done and it requires case by case approach - 
it is not covered by this report.

#### Methodology

The existing blocks are re-executed and included transactions are re-executed
in parallel with two gasometers: the original and simulation.
The simulation applies the changes defined by EIP-7904.
The procedure is as follows;

1. The next transaction is read.
2. The transaction is executed with the simulation gasometer.
3. The blockchain state update is recorded.
4. The blockchain state is reset. The transaction receipt is not included. Used gas is not accounted.
5. The transaction is executed with the original gasometer.
6. The blockchain state update is recorded.
7. The blockchain state update is commited.
8. Two blockchain state updates are compared.

Note that these two blockchain state updates are different because 
the account balances are different at the end of transaction.
So more subtle approach is required.

#### Development notes

Comparison of blockchain state updates is difficult.
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
