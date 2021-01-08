### Execution Comparison

This document will analyze and compare the exact flow of execution of the interpreter loop, and how is its computational cost measured.

The goal is to know, whether the measurements, as compared between various EVM implementations and various opcodes, are collected in a "fair" fashion.

For now, we focus on the individual OPCODE measurements, which we used in preliminary exploration.
**TODO** repeat this for whole-program measurements, if we do them.

### Notes

1. `geth` incorporates a lot of setup which gets measured along with the _first_ instruction. Later this is worked around for programs, where only a single instruction is interesting, by prepending a throw-away `PUSH1`, wherever the interesting instructions would be the first one. `evmone` and `OpenEthereum` don't have this.
    - **TODO** this should be fixed by moving the `CaptureStart` in a forked `go-ethereum` implementation 
