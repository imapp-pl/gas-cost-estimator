## An Adaptive Gas Cost Mechanism for Ethereum  to Defend Against Under-Priced DoS Attacks

Ting Chen, Xiaoqi Li, Ying Wang, Jiachi Chen, Zihao Li, Xiapu Luo ,Man Ho Au and Xiaosong Zhang

https://arxiv.org/pdf/1712.06438.pdf

### Notes

1. "Emulation-based Measurement Framework" - how they measured the underpriced opcodes:
    - extract just `.execute` for a stripped-down execution. "various utility func-tions for supporting the execution." (it might be relevant in our case to _include_ those utility functions, since we want to measure node EVM implementations)
    - repeat and measure once "we run the interpretationhandler in the emulated environment millions of times, because a single run istoo  short  to  conduct  the  measurement"
    - synthesized environment: "If the operation ma-nipulates the stack/memory/storage, we synthesize the stack/memory/storagewith random length and generates random numbers as their items"
