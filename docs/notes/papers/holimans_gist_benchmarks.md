## "gist and PR from `holiman`"

Martin Holst Swende `holiman`

https://gist.github.com/holiman/7153e088af8941379cf21c0e4610d51f
(and the original [PR with discussion](https://github.com/ethereum/go-ethereum/pull/21207))

### ELI5

This is an estimation of the cost (effort) done to _switch context_ when calling a precompiled contract using STATICCALL.
[EIP-2046](https://eips.ethereum.org/EIPS/eip-2046) intends to lower STATICCALL for precompileds from 700 to 40.
The gist assesses this change in `geth`.

### How it measured & instrumented?

It's not instrumented.

The measurement is done by doing an infinite loop in the program and seeing how much time until it depletes `100MGas` (look at the `... ns/op` - this is the time how long the "depletion" needs - the less, the more overpriced the operation is. Don't look at the preceding integer value, this is just golang benchmark stuff).
The "right" gas cost of context switching is found, when this time is equal when you do the context switch (`staticcall-identity`) or not do it (`loop`), but only balance the stack with POPs.

It is ran by [golang benchmarks](https://golang.org/pkg/testing/#hdr-Benchmarks), which measures the loop.
Inside it works similar to `runtime.Execute` which we're using, but could be a useful example of how to strip down the `runtime.Execute` in the future.

In the discussion in the [original PR](https://github.com/ethereum/go-ethereum/pull/21207) there's a thread of how the "other" ops (JUMP. PUSH, POP etc) contribute and distort the result.

### Takeaways

1. Entirely different way to measure effort.
2. Seeking to _balance_ operations - to equate gas spent on equally hard computations. (should cite when explaining motivation **TODO**)
3. `holiman`'s approach (compare using gas depletion, rather than numbers of the loop being iterated) couples the measurement with the gas cost and effort for the accompanying ops (JUMP, PUSH, POP). If we do measurements per operation via instrumentation, we're doing something opposite.
4. [This is linked](https://github.com/matter-labs/openethereum/commit/77471a1d08a0f088dfd3b30802036b3e0fbb38a6) in the discussion. Possibly useful cheatsheet for OpenEthereum
