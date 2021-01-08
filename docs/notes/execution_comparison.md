### Execution Comparison

This document will analyze and compare the exact flow of execution of the interpreter loop, and how is its computational cost measured.

The goal is to know, whether the measurements, as compared between various EVM implementations and various opcodes, are collected in a "fair" fashion.

For now, we focus on the individual OPCODE measurements, which we used in preliminary exploration.
**TODO** repeat this for whole-program measurements, if we do them.

### Notes

1. `geth` incorporates a lot of setup which gets measured along with the _first_ instruction. Later this is worked around for programs, where only a single instruction is interesting, by prepending a throw-away `PUSH1`, wherever the interesting instructions would be the first one. `evmone` and `OpenEthereum` don't have this.
    - **TODO** this should be fixed by moving the `CaptureStart` in a forked `go-ethereum` implementation
2. In order to ensure standardization and portability, easy and succinct rules of how to measure should be devised, so that such comparisons aren't necessary in the future
3. `evmone` does a preprocessing step `analysis.cpp`, which slightly skewes measurements - some of the effort to do some opcodes will be "put" under "intrinsic opcode `BEGINBLOCK`" executing at the end of each code block. `geth` and `OpenEthereum` don't have this
4. `evmone` perceivably measures _only_ the execution of the opcode, but this is not the case, as in `evmone` all logic done in the main interpreter loop in `geth` is done deeper down the call stack. The only thing "excluded" from measurement is the `while` loop condition:
    ```
    while (instr != nullptr)
    ```
