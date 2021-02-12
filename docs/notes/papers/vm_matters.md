## VM Matters: A Comparison of WASM VMs and EVMs in the Performance of Blockchain Smart Contracts

Shuyu Zheng, Haoyu Wang, Lei Wu, Gang Huang, Xuanzhe Liu

https://arxiv.org/pdf/2012.01032.pdf

### Notes

1. "conducts the first measurement study, to measure the performance on WASM VM and EVM for executing smart contracts on blockchain"
2. "To our surprise, the cur-rent WASM VM does not perform in expected performance. Theoverhead introduced by WASM is really non-trivial. Our resultshighlight the challenges when deploying WASM in practice, andprovide insightful implications for improvement space."
3. This paper includes comparison of EVM implementations, but does so on the highlevel to seek performance gaps of running smart contracts. We focus to find differences in patterns of relative computational costs that set implementations apart. "RQ2 A Comparison of EVM Engines.As there are several clientsthat support the execution of EVM bytecode, we are wonder-ingare there any performance gaps of running smart contractsamong them?"
4. This paper indicates the importance of 256bit/64bit versions of benchmarks for Ewasm. Not entirely sure what this means here, but this might be another dimension of variability for Ewasm
