
## Gas Cost Changes Impact

### Methodology

#### Gas Usage Vector

Gas Usage Vector is a decomposition of the gas usage to elementary coefficients.
Each coefficient refers to a quantity of a given component that increments gas usage.
Anything that increases gas usage should be reflected as one or more coefficients in Gas Usage Vector,
including calldata, opcodes, precompiles, access lists, contract creation etc.

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

