### Execution Comparison

This document will analyze and compare the exact flow of execution of the interpreter loop, and how is its computational cost measured.

The goal is to know, whether the measurements, as compared between various EVM implementations and various OPCODEs, are collected in a "fair" fashion.
"Fair" in this context mean not only (or not as much as) fairness between implementations, but rather _relatively fair treatment_ of all OPCODEs in all implementations.

For now, we focus on the individual OPCODE measurements, which we used in preliminary exploration.
**TODO (optional)** repeat this for whole-program measurements, if we do them.

### Notes

1. `geth` incorporates a lot of setup which gets measured along with the _first_ instruction. Later this is worked around for programs, where only a single instruction is interesting, by prepending a throw-away `PUSH1`, wherever the interesting instructions would be the first one. `evmone` and `OpenEthereum` don't have this.
    - **TODO** this should be fixed by moving the `CaptureStart` in a forked `go-ethereum` implementation. It should be placed deeper down the call stack, just before entering the first interpreter loop iteration
2. In order to ensure standardization and portability, easy and succinct rules of how to measure should be devised, so that such comparisons aren't necessary in the future. First draft (**TODO** polish out):
    - always measure the entire block of code which constitutes a single interpreter iteration
    - leave all preprocessing out
    - make sure all tracing/debugging is off, except what we need to trace. **TODO** `geth` measurement should be improved in this aspect, possibly move away from leveraging the `Tracer` interface
    - gather the measurements consistently. There should be no allocations done
    - look into whether preprocessing or similar optimizations don't "move effort" from one instruction to another, like `evmone` does
3. `evmone` does a preprocessing step `analysis.cpp`, which slightly skews measurements - some of the effort to do some OPCODEs will be "put" under "intrinsic OPCODE `BEGINBLOCK`" executing at the end of each code block. `geth` and `OpenEthereum` don't have this.
    - `BEGINBLOCK` (manifesting as `JUMPDEST` in OPCODE tracing) needs special attention in larger programs. We must come up with a way to handle it, since other implementations will not have this "intrinsic instruction". **TODO**
4. `evmone` perceivably measures _only_ the execution of the OPCODE (as opposed to `geth`), but this is not the case. In `evmone` all logic done in the main interpreter loop in `geth` is done deeper down the call stack.
5. `OpenEthereum` excludes the `while` loop condition used in the interpreter loop (`geth` and `evmone` include it). Similar fix for this for `evmone` has been done [here](https://github.com/imapp-pl/evmone/pull/2). [See also here](./instrumentation_measurement/openethereum.md)
5. `geth` and `evmone` measurements are written to a pre-allocated array on every instruction, while `OpenEthereum` write the CSV data straight to `stdout`, this might be slightly unfair **TODO** even out the measurement implementations
