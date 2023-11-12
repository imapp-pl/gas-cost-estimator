# Gas Cost Estimator
_Stage 3 Report_

## Abstract
We summarize the findings of the third stage of the "Gas Cost Estimator" research project. Based on the previous research, we provide a methodology for reproducible estimation of gas fees for OPCODEs as defined in the Ethereum Yellow Paper. This stage introduces measurements for five additional EVM implementations, compares them with the previous results and sets out a methodology for

## Introduction and project scope
This project is the continuation of the previous stages of the Gas Cost Estimator. Please visit https://github.com/imapp-pl/gas-cost-estimator to find more information. After publishing our report from the second stage of the Gas Cost Estimator project we received feedback from the community. The community expressed the need to see other implementations being included in the research as well as to have the tooling automated and the benchmarks standardized.

In this stage we apply the method of estimating gas costs of EVM OPCODEs suggested in our previous work to other EVM implementations:
- Nethermind (https://github.com/NethermindEth/nethermind)
- EthereumJS (https://github.com/ethereumjs/ethereumjs-monorepo)
- Erigon (https://github.com/ledgerwatch/erigon)
- Besu (https://github.com/hyperledger/besu)
- Rust EVM (revm) (https://github.com/bluealloy/revm)

Also, we have improved the tooling so it is easier to reproduce the measurements. This work will be further continued in phase four, where we’ll deliver complete tooling, reproduction environment setup and measurement methods.

## Methodology

### Measurement approach

Our approach is to test each EVM implementation in isolation. That means that any host objects, storage access and other infrastructure elements are mocked. As a result, we had to exclude any OPCODEs that access storage. Also for consistency, we have excluded any OPCODEs introduced after The Merge.

### Factors impacting the results

Research and experiments in Stage II have shown the importance of removing uncontrollable and variable factors when estimating the cost of executing any given OPCODE. This includes:
- Caching on various levels, from processor to operating system to disk to EVM implementation
- Processor and hardware architecture
- Warm-up effect
- Operating System performance optimizations, pre-loading frameworks and libraries
- Operating System process priority and multithreading
- Garbage Collector impact
- Virtualization impact
- Node synchronization and data model impact

While we appreciate the fact that these factors might influence the final cost of the OPCODE executions, their unpredictable nature means that it is not possible to accurately assess the impact. As a result, it is down to the network node operator to ensure that the optimal environment conditions are provided to the running node or bear the additional cost.

In some cases node operators might intentionally provide sub-optimal environmental conditions, like running nodes on virtualized hardware, running multiple nodes on the same machine or running it on low-spec machines. This might be due to business or infrastructure specifics. As long as node operators are aware of the increased costs, this is not an issue.

To eliminate the unwanted and unpredictable impacts of the factors above, and to make the results more comparable, we made two decisions:
1. Any execution times are measured on 'bare' EVM engines. That means that for any client node implementation, we look at the code directly responsible for the BYTECODE execution. This bypasses any infrastructure code that might already exist for a client. Also often implementations have a concept of a 'host' that provides the EVM engine with external data, like accounts, code or storage. We mock those hosts or use minimal implementations where possible.
2. For any given programming language we use the most popular benchmarking tool, rather than try to manually take timings. While implementations and solutions for benchmarking tools differ from language to language, we believe that using standardized, well-tested and popular benchmarking frameworks gives the most trustworthy results.

An additional factor is what we call 'engine overhead'. This is the cost of time and resources incurred between receiving the BYTECODE by the engine and executing the first OPCODE. Some EVM implementations have minimal overhead required just to load the BYTECODE. While others use this opportunity to parse it, spin up the engine, pre-fetch required data and prepare any accounts required for execution. We believe that this cost is the true cost of the OPCODE execution and should be divided proportionally. This is done individually for each implementation.

### Environment setup

For all the measurements we used a reference machine with the following specifications:
- Intel® Core™ i5-13500
- 64 GB DDR4
- 2 x 512 GB NVMe SSD
- Ubuntu 22.04

The required tooling can be installed using:
```bash
./src/setup_tools.sh
```

The individual EVM implementations are setup using:
```bash
./src/clone_clients.sh
./src/build_clients.sh
```

### Results interpretation

The results for each EVM are obtained using various setups and benchmarking tools. They do not express the cost of a single opcode execution directly. Thus results between different EVMs cannot be compared, for instance, `ADD` for geth cannot be compared with `ADD` for EthereumJS. But results within a given EVM can be compared, for instance, `ADD` with `MUL` for geth.

The calculated costs need to be scaled, to get to a common denominator, so an alternative gas cost schedule based on all EVMs can be proposed. The choice of scaling factors is the first methodological decision. We refer to the calculated costs for each EVM to the current gas cost schedule. The scale we are looking for is the solution to the following minimization problem: find the scale that the scaled calculated costs of all OPCODEs are the closest to the current gas cost schedule in the l2 norm (sqrt of the sum of squared differences). Note that the scales are set independently for EVMs. There are three remarks for l2 norm calculations:
- From PUSH1, …, PUSH32 only PUSH1 is taken into account. There are 32 PUSH opcodes so they would have excessive impact. The same for DUPs and SWAPs. Note that for some EVMs calculated costs for PUSH1, …, PUSH32 are noticeably different.
- The current gas cost schedule is taken as counterweights. So EXP and ADD have the same impact, for instance.
- The variability of argument size (`measure arguments`) has not been included in the gas schedule proposal

The resulting estimated costs (scaled calculated costs) can be compared now and an alternative gas cost schedule can be proposed. This is the second methodological decision. We simply take the average of scaled calculated costs with equal weight for each EVM. The resulting costs are assessed with two factors:
- The relative difference. You can consider it as the percentage difference between the current gas cost schedule and the alternative gas cost schedule. The greater the value is, the more an opcode is underpriced or overpriced.
- The relative standard deviation. This is the standard deviation of scaled calculated costs of a given opcode for all EVMs, but divided by the current gas cost of an opcode to get a relative value. Note that a low value means that the majority of EVMs yield very similar scaled estimated costs for an opcode and that is good because the alternative cost is more reliable.

As the final step, the alternative gas cost schedule is assessed as the whole system. When can it be considered as ‘good’? We informally say that ‘good’ means it is informative: delivers clear and effective guidelines on how to improve the gas cost schedule. First, low values of the relative standard deviations make the whole alternative gas cost schedule more reliable. Second, opcodes can be divided into those that have similar alternative and current gas cost and those that are clearly underpriced or overpriced. It seems to be very handy if most of the opcodes would fall into the first group.

### Alternatives
The following alternatives have been considered:
1. When scaling calculated costs to scaled calculated costs, the same scale could be used for all EVMs. This alternative has been rejected because it would blur the actual differences and make the alternative gas cost schedule less informative.
1. Do Not use scaling at all but compare calculated costs directly. This alternative has been rejected because the differences between EVMs are too big and the alternative gas cost schedule would be less informative.
1. Scale, but rather than using all OPCODEs in the l2 norm, use the selected ones. This is similar to the approach taken in Stage II. This alternative has been rejected because it is not possible to objectively decide what OPCODEs to use for scaling.
1. When building the alternative schedule all EVMs are given the same weight. This could be adjusted so the weights depend on:
    - popularity: more popular EVMs have more impact on the alternative gas cost schedule
    - performance: more performant EVMs have more impact on the alternative gas cost schedule

### Final remarks
- The alternative gas cost schedule can be scaled again to have a better match with the current gas cost schedule.
- The relative standard deviation effectively depends on how calculated costs are scaled. The system could be optimized towards minimising the number of opcodes with significant deviation. The method presented in this paper seemed to be more straightforward for the authors.



## EVM Implementations results
In this chapter, we show the measurement approach for individual EVM implementations and then preset and analyze the results.


### Nethermind

*Setup*

Nethermind is developed in the .NET framework using C# language. Our benchmark is based on the existing solution and uses `DotNetBenchmark` library. In `Nethermind.Benchmark.Bytecode` project we have added a new benchmark class `BytecodeBenchmark` that contains the benchmarking methods. This uses an in-memory database for a minimal impact. The EVM engine is contained in `Nethermind.Evm` library. The host is minimal.

The benchmark code can be found at https://github.com/imapp-pl/nethermind/tree/evm_gas_cost_stage_3.

The following script executes benchmarks:

```bash
	python3 ./src/instrumentation_measurement/measurements.py measure --mode benchmark --input_file ./local/pg_marginal_full5_c50_step1_shuffle.csv --evm nethermind --sample_size 10
```

*Results*

Full details:
- [Measure marginal](./report_stage_iii_assets/nethermind_measure_marginal_single.html)
- [Measure arguments](./report_stage_iii_assets/nethermind_measure_arguments_single.html)

Sample results:

**Figure 1a: Execution time (`total_time_ns`) of all programs in measure marginal mode**

<img src="./report_stage_iii_assets/nethermind_marginal_all_no_outliers.png" width="700"/>&nbsp;

**Figure 1b: Execution time of `EXP` opcode in measure arguments mode, 2nd argument variable length**

<img src="./report_stage_iii_assets/nethermind_arguments_exp_arg1.png" width="700"/>&nbsp;

*Analysis*

Nethermind general characteristics of benchmark follow what is expected. Rather small differences between OPCODEs times suggest there is a rather large engine overhead. This could be removed from the results, before making further gas cost estimations.

A repeatable pattern can be observed in jump OPCODEs:

**Figure 2: Execution times of `JUMP` opcodes**
<img src="./report_stage_iii_assets/nethermind_marginal_odd_jump.png" width="700"/>&nbsp;

The first program with no `JUMP` instructions is significantly faster than the next one with one `JUMP` instruction. The follow-up programs behave in a normal linear fashion. The same is true for `JUMPDEST` and JUMPI opcodes.
This might suggest that invoking a single `JUMP` instruction initiates some engine functionality reused by any other `JUMP` instructions.
The EXP opcode is one of few that cost depends on the size of arguments. The other notable opcodes are `CALLDATACOPY`, `RETURNDATACCOPY`, and `CODECOPY`. In EXP case, there are two separate lines clearly visible. This indicates that the execution time, not only depends on argument size but also its value.


### EthereumJS

*Setup*

EtherumJS is written in TypeScript and executed in NodeJS environment. For benchmarks we use npm `benchmark` library. The EVM engine is contained in `@ethereumjs/evm` library. There is no concept of a host in EthereumJS, so we use a minimal implementation.

The benchmark code can be found at https://github.com/imapp-pl/ethereumjs-monorepo/tree/evm_gas_cost_stage_3.

The following script executes benchmarks:

```bash
	python3 ./src/instrumentation_measurement/measurements.py measure --mode benchmark --input_file ./local/pg_marginal_full5_c50_step1_shuffle.csv --evm ethereumjs --sample_size 10
```

*Results*

Full details:
- [Measure marginal](./report_stage_iii_assets/ethereumjs_measure_marginal_single.html)
- [Measure arguments](./report_stage_iii_assets/ethereumjs_measure_arguments_single.html)

Sample results:

**Figure 3a: Execution time (`total_time_ns`) of all programs**

<img src="./report_stage_iii_assets/ethereumjs_marginal_all_no_outliers.png" width="700"/>&nbsp;

**Figure 3b: Execution time of `EXP` opcode in measure arguments mode, 2nd argument variable length**

<img src="./report_stage_iii_assets/ethereumjs_arguments_exp_arg1.png" width="700"/>&nbsp;

**Figure 3c: Execution time of `ISZERO` opcode in measure arguments mode, 1st argument variable length**

<img src="./report_stage_iii_assets/ethereumjs_arguments_iszero_arg0.png" width="700"/>&nbsp;

*Analysis*

EthereumJS results are visibly slower than the rest and that's expected, though most of the measured times are in the expected range. One specific thing to note is that `PUSHx` opcodes are not constant, but times increase linearly with the number of bytes pushed. The same cannot be observed for DUPx and SWAPx opcodes. This might suggest that EthereumJS has a special implementation for `PUSHx` opcodes.
On the argument side, the `EXP` opcode behaves as expected. The execution time increases linearly with the size of the second argument. Again the separation into two different lines shows that the execution time depends not only on the size of the argument but also its value. The `ISZERO` opcode behaves in a similar fashion, but the execution time increases linearly with the size of the first argument.

### Erigon

*Setup*

Erigon shares some of the code-base with GoEthereum. We used GO's `testing` library for benchmarking, and the code can be found in `test/imapp_benchmark/imapp_bench.go`. We used an in-memory database for a minimal impact with a minimal host.

The benchmark code can be found at https://github.com/imapp-pl/erigon/tree/imapp_benchmark

The following script executes benchmarks:
```
	python3 ./src/instrumentation_measurement/measurements.py measure --mode benchmark --input_file ./local/pg_marginal_full5_c50_step1_shuffle.csv --evm erigon --sample_size 10
```

*Results*

Full details:
- [Measure marginal](./report_stage_iii_assets/erigon_measure_marginal_single.html)
- [Measure arguments](./report_stage_iii_assets/erigon_measure_arguments_single.html)

Sample results:

**Figure 4a: Execution time (`total_time_ns`) of all programs**

<img src="./report_stage_iii_assets/erigon_marginal_all_no_outliers.png" width="700"/>&nbsp;

**Figure 4b: Execution time of `EXP` opcode in measure arguments mode, 2nd argument variable length**

<img src="./report_stage_iii_assets/erigon_arguments_exp_arg1.png" width="700"/>&nbsp;

*Analysis*

Erigon's overall results follow the expected pattern. The engine overhead is rather small, which is expected from a Go implementation.

Again, `PUSHx` opcodes are not constant, but times increase linearly with the number of bytes pushed. The same cannot be observed for `DUPx` and `SWAPx` opcodes. This might suggest that Erigon has a special implementation for `PUSHx` opcodes.

When looking at individual OPCODEs, there is an interesting non-linear pattern in simple opcodes like `ADD`, `DIV`, `MULMOD`, etc. The first 3 executions are visibly faster than the following. The rest behave in a more linear fashion. The reason for this is not clear.

### Besu

*Setup*

Besu is developed in Java. We used JMH library for benchmarking. The EVM engine is contained in `besu-vm` library. This implementation utilizes the concept of a `MessageFrame`, which acts as a host object too.

The benchmark code can be found at https://github.com/imapp-pl/besu/tree/benchmarking.


*Results*

Full details:
- [Measure marginal](./report_stage_iii_assets/besu_measure_marginal_single.html)
- [Measure arguments](./report_stage_iii_assets/besu_measure_arguments_single.html)

Sample results:

**Figure 5a: Execution time (`total_time_ns`) of all programs**

<img src="./report_stage_iii_assets/besu_marginal_all_no_outliers.png" width="700"/>&nbsp;

**Figure 5b: Execution time of `EXP` opcode in measure arguments mode, 2nd argument variable length**

<img src="./report_stage_iii_assets/besu_arguments_exp_arg1.png" width="700"/>&nbsp;

*Analysis*

The timings for Besu are characterised by a rather significant scatter, even after removing outliers. This might be due to the JVM garbage collector, which is not controlled in our setup. Additionally, the engine overhead is rather large. We tried to remove it from the results, but the results were not consistent.

As seen on the charts, the execution times for `ADD`, `DIV` and `MULMOD` are not consistent. While the majority behaves in a linear fashion, there is a large portion that often takes longer. Again, we attribute it to the JVM garbage collector or other JVM internals.

The execution time for `EXP` increases linearly with the size of the second argument. Again the separation into two different lines shows that the execution time depends not only on the size of the argument but also its value. In contrast to other implementations, the second line has a constant slope.

### Rust EVM

*Setup*

Rust EVM is developed in Rust. We used `criterion` library for benchmarking. The EVM engine is contained in `revm` library. We used `DummyHost` as a host object for a minimal impact.

The benchmark code can be found at https://github.com/imapp-pl/revm/tree/evm_gas_cost_stage_3.


The following script executes benchmarks:
```
	python3 ./src/instrumentation_measurement/measurements.py measure --mode benchmark --input_file ./local/pg_marginal_full5_c50_step1_shuffle.csv --evm revm --sample_size 10
```

*Results*

Full details:
- [Measure marginal](./report_stage_iii_assets/revm_measure_marginal_single.html)
- [Measure arguments](./report_stage_iii_assets/revm_measure_arguments_single.html)

Sample results:

**Figure 6a: Execution time (`total_time_ns`) of all programs**

<img src="./report_stage_iii_assets/revm_marginal_all_no_outliers.png" width="700"/>&nbsp;

**Figure 6b: Execution time of `EXP` opcode in measure arguments mode, 2nd argument variable length**

<img src="./report_stage_iii_assets/revm_arguments_exp_arg1.png" width="700"/>&nbsp;

*Analysis*

Rust EVM results are very consistent and follow the expected pattern. The engine overhead is rather small, which is expected from a Rust implementation.

In some opcodes like `ADD`, `DIV` and `MULMOD` there is a visible pattern of the first execution being slower than the rest. After running the specific opcode for a few times, the execution time stabilizes. This might be due to some caching or other Rust internals.

This implementation does not have a separation of lines seen for the EXP arguments in other implementations.

## Conclusions

Full etails:
- [Analysis](./report_stage_iii_assets/final_estimation.html)
- [Alternative gas cost schedule](./report_stage_iii_assets/gas_schedule_comparison.csv)

The results for each individual EMV has been scaled and compared with the current gas cost schedule as per our methodology. 


**Figure 7: Scaled calculated costs in comparison to the nominal gas schedule**

<img src="./report_stage_iii_assets/final_all.png" width="700"/>&nbsp;


Calculating the averages, we get the following alternative gas cost schedule:

**Figure 8: Alternative gas schedule**

<img src="./report_stage_iii_assets/final_proposal.png" width="700"/>&nbsp;


This table present the full comparison between the current gas cost schedule and the alternative gas cost schedule. In the last column, we suggest a change if the difference is large enough and client variability allows it.

Opcode|Nominal Gas|Scaled Calculated Cost|Change %|Client Variability (Std Err %)|Change Suggested
:----- | ----: | -----: | ----: | -----: | :-----:
ADD|3|1.87|-37.71%|10.87%|Yes
MUL|5|3.79|-24.23%|19.83%|Yes
SUB|3|2.36|-21.44%|25.17%|Yes
DIV|5|3.38|-32.44%|23.02%
DIV expensive_cost|5|8.06|61.24%|18.16%
SDIV|5|5.01|0.19%|29.03%
SDIV expensive_cost|5|10.32|106.45%|20.26%
MOD|5|3.95|-21.00%|20.38%
MOD expensive_cost|5|8.69|73.70%|16.47%
SMOD|5|4.61|-7.90%|22.25%
SMOD expensive_cost|5|9.27|85.48%|17.34%
ADDMOD|8|5.57|-30.31%|24.75%
ADDMOD expensive_cost|8|13.52|68.99%|26.03%
MULMOD|8|8.64|7.95%|19.85%|Yes
MULMOD_expensive_cost|8|16.44|105.47%|18.71%
EXP|10|13.86|38.62%|14.17%
EXP_arg1_cost|50|21.84|-56.32%|20.94%
SIGNEXTEND|5|3.82|-23.62%|21.60%|Yes
LT|3|2.81|-6.30%|32.36%
GT|3|2.74|-8.72%|33.50%
SLT|3|2.11|-29.63%|14.32%
SGT|3|2.10|-29.97%|14.19%
EQ|3|2.26|-24.64%|26.02%
ISZERO|3|1.56|-48.04%|19.30%|Yes
AND|3|2.40|-20.04%|27.09%
OR|3|2.41|-19.54%|26.11%
XOR|3|2.43|-19.15%|26.52%
NOT|3|1.79|-40.34%|18.57%|Yes
BYTE|3|2.99|-0.21%|23.42%
SHL|3|3.11|3.71%|15.52%
SHR|3|3.18|6.10%|21.77%
SAR|3|3.78|26.15%|23.36%
ADDRESS|2|3.16|58.16%|23.87%|Yes*
ORIGIN|2|2.74|36.81%|29.00%|Yes*
CALLER|2|2.42|21.14%|22.15%
CALLVALUE|2|1.56|-21.78%|19.41%
CALLDATALOAD|3|2.55|-15.00%|16.10%
CALLDATASIZE|2|1.25|-37.63%|9.06%|Yes
CALLDATACOPY|2|6.75|237.63%|17.57%|Yes
CODESIZE|2|1.25|-37.32%|8.55%|Yes
CODECOPY|2|6.43|221.49%|16.38%|Yes
GASPRICE|2|1.88|-5.97%|29.41%
RETURNDATASIZE|2|1.32|-34.12%|10.92%|Yes
RETURNDATACOPY|3|6.41|113.82%|24.00%|Yes
COINBASE|2|3.07|53.29%|28.14%|Yes
TIMESTAMP|2|1.58|-20.87%|14.08%
NUMBER|2|1.59|-20.27%|13.46%
DIFFICULTY|2|2.83|41.71%|32.81%
GASLIMIT|2|1.60|-19.96%|12.87%
CHAINID|2|2.06|3.17%|27.41%
SELFBALANCE|5|8.01|60.22%|43.98%|Yes*
POP|2|1.06|-46.83%|17.14%
MLOAD|3|3.93|31.14%|14.38%
MSTORE|3|7.72|157.34%|28.72%|Yes
MSTORE8|3|3.12|3.87%|18.98%
JUMP|8|2.03|-74.68%|30.75%|Yes**
JUMPI|10|2.94|-70.56%|30.08%|Yes**
PC|2|1.14|-42.95%|10.19%|Yes
MSIZE|2|1.23|-38.53%|9.76%|Yes
GAS|2|1.20|-39.99%|8.60%
JUMPDEST|1|0.90|-10.41%|8.49%
PUSH1|3|2.05|-31.79%|34.68%
PUSH2|3|2.52|-15.97%|30.48%
PUSH3|3|2.65|-11.79%|29.64%
PUSH4|3|2.74|-8.63%|30.05%
PUSH5|3|2.86|-4.53%|31.82%
PUSH6|3|2.90|-3.42%|33.10%
PUSH7|3|3.09|2.91%|33.31%
PUSH8|3|3.12|3.83%|35.37%
PUSH9|3|3.22|7.37%|35.79%
PUSH10|3|3.30|10.15%|36.83%
PUSH11|3|3.45|14.88%|36.19%
PUSH12|3|3.53|17.82%|37.52%
PUSH13|3|3.60|19.90%|37.88%
PUSH14|3|3.74|24.69%|38.22%
PUSH15|3|3.88|29.17%|37.79%
PUSH16|3|3.88|29.43%|38.89%
PUSH17|3|4.04|34.68%|39.35%
PUSH18|3|4.18|39.35%|39.87%
PUSH19|3|4.28|42.74%|39.74%
PUSH20|3|4.33|44.46%|41.48%
PUSH21|3|4.40|46.82%|42.24%
PUSH22|3|4.53|50.93%|42.33%
PUSH23|3|4.65|55.15%|42.26%
PUSH24|3|4.69|56.36%|43.29%
PUSH25|3|4.76|58.68%|43.43%
PUSH26|3|4.97|65.65%|43.82%
PUSH27|3|5.00|66.79%|44.21%
PUSH28|3|5.09|69.63%|44.33%
PUSH29|3|5.17|72.38%|45.69%
PUSH30|3|5.24|74.54%|46.09%
PUSH31|3|5.42|80.72%|45.58%
PUSH32|3|5.42|80.68%|47.23%
DUP1|3|1.29|-56.94%|17.04%
DUP2|3|1.27|-57.58%|19.33%
DUP3|3|1.24|-58.75%|18.21%
DUP4|3|1.22|-59.27%|18.88%
DUP5|3|1.22|-59.46%|19.64%
DUP6|3|1.27|-57.67%|19.07%
DUP7|3|1.15|-61.63%|14.61%
DUP8|3|1.14|-62.04%|14.48%
DUP9|3|1.26|-57.92%|18.24%
DUP10|3|1.21|-59.77%|17.61%
DUP11|3|1.14|-62.00%|15.86%
DUP12|3|1.27|-57.59%|16.66%
DUP13|3|1.16|-61.18%|15.49%
DUP14|3|1.17|-61.11%|14.09%
DUP15|3|1.29|-56.85%|17.36%
DUP16|3|1.16|-61.32%|14.24%
SWAP1|3|1.45|-51.66%|15.97%
SWAP2|3|1.47|-50.92%|14.43%
SWAP3|3|1.47|-51.07%|14.16%
SWAP4|3|1.46|-51.41%|14.78%
SWAP5|3|1.44|-52.03%|16.43%
SWAP6|3|1.51|-49.79%|16.35%
SWAP7|3|1.61|-46.33%|17.06%
SWAP8|3|1.45|-51.60%|14.60%
SWAP9|3|1.44|-52.14%|16.21%
SWAP10|3|1.69|-43.61%|19.15%
SWAP11|3|1.42|-52.57%|15.01%
SWAP12|3|1.52|-49.42%|15.98%
SWAP13|3|1.52|-49.31%|16.78%
SWAP14|3|1.40|-53.19%|15.40%
SWAP15|3|1.70|-43.37%|21.62%
SWAP16|3|1.63|-45.50%|19.30%

Notes:

[*] - Alghouth the data suggest a change, but these particular OPCODEs were not supposed to generate such high costs, especially `SELFBALANCE`. More investigation needed.

[**] - With the introduction of new relative jumps and disallowing dynamic jumps (EIP-4750 and EIP-4200) these OPCODEs might become irrelevant.

> **Final Remark**
>
> The data clearly shows that some changes can be made to the current gas proposal. Still, any such changes should be carefully considered, as there are other factors not taken into account in this research: ease of implementation, backward compatibility, hard fork requirement, existing tooling, hardcoded values in auxiliary software, etc.
>
>The alternative gas cost schedule is a proposal and should be treated as such. We believe that the methodology presented in this report is a good starting point for further research and discussion.