# Gas Cost Estimator - Stage I Report

**Abstract**

We summarize the findings of the first stage of the "Gas Cost Estimator" research project. This research project aims to propose a method of estimating gas costs of EVM/eWASM OPCODEs (a subset of). In the Stage I Report we give a brief overview of state of research on the topic, explain the motivation of conducting this research and present some early conclusions from the preliminary exploration. Next, we elaborate on the next steps to perform in the Stage II of this research project. We argue that measuring of individual OPCODE execution duration is feasible and gives ample opportunity of analyzing the differences of computational cost of different OPCODEs and different EVM/eWASM implementations.

## 1. Introduction

EVM (Ethereum Virtual Machine) and eWASM (Ethereum flavored WebAssembly) are instrumental to the functioning of the Ethereum blockchain.
These components are responsible for carrying out the computations associated with transactions on the Ethereum blockchain, namely those related to the functioning of smart contracts.
Due to Turing completeness of their instruction sets, and the necessity to guarantee that computations can be securely performed in an open, distributed network, a halting mechanism must be provided.

The halting mechanism is provided thanks to gas, which is an Ethereum specific measure of computational cost incurred by the executing environment (Ethereum node connected to the network).
Gas is priced in Ether (the intrinsic value token of the Ethereum blockchain), each transaction has an allowance of gas prepaid by the transaction sender.
Every step of computation (as of writing, this corresponds to every bytecode instruction interpreted by EVM/eWASM) costs a small amount of gas, and if gas allowance is depleted, the computation is halted and its effects are reverted, except for the consumption of the entire gas allowance.
The gas consumed by computations performed is paid out as transaction fee (in Ether) to the miner, or their Eth2.0 counterpart, including the transaction.
The unused remainder of the prepaid gas allowance is returned back to the transaction sender.

The challenge with this mechanism is to determine adequate gas costs of bytecode instructions.
Currently, this is done on a per-OPCODE basis, that is, every OPCODE interpreted by the EVM/eWASM has a predetermined gas cost (or its gas cost is expressed as a function of instruction's arguments).
This report and the "Gas Cost Estimator" research project aims at devising a method to estimate adequate values for these OPCODE gas costs, by estimating and analyzing the relative computational cost of OPCODEs.

### Motivation

The importance of adequate gas costs arises from the nature of computations done on the Ethereum blockchain, and has been discussed by many authors.

It is intuitive that the parties participating in the network, who are responsible for validation of blockchain transactions and maintaining the state of the blockchain (miners in Eth1.0), are interested in fair pricing for the service they provide.
This is emphasized in **TODO find ref**.
Given however, that the transaction fee still is the minor part of PoW miner reward [1], the importance of this argument might be disputed.
It can also be stated, that it is the computational cost of PoW mining itself, which constitutes the major part of computational burden on the miner.

However, adequate gas cost of computation is paramount from the perspective of network security.
Gas cost is a natural deterrent from abusing the networks capacity.
If pricing of computations was inadequate, it would mean that there are operations in EVM/eWASM which are relatively underpriced, when compared to others.
This would in turn mean that adversarial actors could craft the transactions in a way which puts significant load on the network, at the same time paying disproportionately low transaction fees.
This situation opens the door to DoS attacks, which have happened and were given as main motivation for gas cost revisions in **TODO find ref**.

To add to this, there is the decentralization factor of having adequate gas costs.
The computations by EVM/eWASM components in Ethereum network nodes are performed by all nodes in the network, regardless of whether they are mining and earning transaction fees or not.
In the situation described above, the effect of the DoS attack extends to all participants of the network, most severely impacting less performant systems running on consumer hardware.
The ability of users running nodes on consumer hardware to keep up with the execution of transactions on the blockchain is very important for preserving the decentralized nature of Ethereum.
Such arguments are present in **TODO find ref**.

Another motivation for this work is the indirect effect gas costs of instructions have on smart contract code.
Since the optimization done on smart contract source and intermediate code is usually targeting minimization of gas expenditure of the users of the contract, inadequate gas costs attributed to instructions might lead to skewed optimization results, whereby an optimized smart contract bytecode is not optimal from the point of view of computational cost.

Another threat related to inadequate gas costs is mentioned in **TODO find ref**.
Authors argue that such inadequate costs may lead to entire smart contracts becoming imbalanced in terms of their computational costs versus the amount of fees deduced for transacting using these contracts.
This in turn could incentivize parties who include transactions in blocks (miners in Eth1.0) towards preferring certain contracts over other, in order to maximize their returns.
This could lead to a less predictable behavior of the fee market, from the network users' perspective.
Assuming that transactions can in fact be efficiently categorized in terms of which smart contracts they execute on, which is a non-trivial task, one should accept the possibility of such scenario.

This report and the entire "Gas Cost Estimator" proejct are focusing on a subset of EVM/eWASM OPCODEs.
The OPCODEs in this subset (see [Appendix B: OPCODEs subset](#appendix-b-opcodes-subset) have in common that they do not include any instructions which access the Ethereum storage (e.g. `SSTORE`, `SLOAD` etc.).
On one hand, the focus on only purely computational instructions is intended and desirable, as seen from the point of view whereby the importance of on-chain computations will increase, while the extensive use of Ethereum storage will diminish and become more relatively more expensive.
This is driven by the current influx of L2-scalability solutions, which only store the minimum amount of bytes, putting the burden of providing data on the transaction senders and the burden of validating it on the smart contract.
**TODO find ref**.
On the other hand, we intend to consider extending the method devised here to storage-bound instructions in the future as well.

### Standardization effort

One of the factors that contribute to the challenge which gas cost estimation presents is the inherent multitude of environments involved.

By environments in this context we mean:
  - different implementations of the Ethereum node (and EVM/eWASM in consequence), done in different programming languages and with different mindsets.
  - different hardware on which this software is ran; this is exacerbated by the requirement towards the software to run reliably on both server-grade hardware and consumer-grade desktops alike
  - different operating systems.

Since the inclusive nature of Ethereum, we are required to examine and include in the analysis the entire spectrum of these environments and determine how much does the environment impact the estimated gas costs.

It is desirable, and is intended to be considered in the Stage II of the project, that the method devised here is reasonably easily applicable in those varying environments.
To this end, the approach must be well documented and reproducible by the community.

### Anticipation of Stage II

As will be further detailed in **TODO reference**, this report anticipates the completion of Stage II of the project.
Given that, we focus on setting forth a plan and strategy for conducting the future measurements and analysis, rather than providing answers or recommendations for gas cost adjustments.

## 2. Related work

## 4. Preliminary work and findings of Stage I

Important notice to this section: all results obtained at the Stage I of this research are still not intended to be seen as final.
There are many caveats and detail work to be done, which will impact the final results.
As a consequence, we are phrasing our preliminary findings as questions that need to be considered in Stage II.

### Preliminary method

During the execution of Stage I, preliminary experiments and analysis were performed in order to explore the dynamics of computational effort which OPCODEs of EVM/eWASM exhibit.
The intention of this exploration was to propose a method for gas cost estimation, which would be further advanced and validated in Stage II.

The method consists of three separate domains:
1. **Program generation** - entails generation of EVM/eWASM bytecode programs which will be executed in order to gather measurements
2. **Instrumentation and measurement** - entails the process of running the generated programs in a controlled environment and performing various measurements
3. **Analysis** - entails the process of statistical analysis and validation of the obtained measurement data

In the following subsections, the preliminary implementation of these three domains will be briefly described.
Refer to the next section for the planned approach to complete these implementations in Stage II.

#### Preliminary program generation

For Stage I we used the "Simplest valid program" approach.
This set of programs will have one program per OPCODE and it will be a smallest and simplest program which successfully executes the instructions and stops.
Additionally to this, we exclude several OPCODEs which treatment should be polished out in Stage II (`JUMP`, `JUMPI`, `RETURNDATACOPY`).
We also fully neglect the breadth of arguments which can be supplied to the OPCODEs execution (e.g. `EXP`), which has substantial impact on the computational cost.

The source code for preliminary program generation employed can be seen **TODO reference**.

#### Preliminary instrumentation and measurement

For Stage I we used the "measure all" approach for individual EVM/eWASM instructions.
In this approach we measure the entire iteration of the interpreter main loop for every instruction in terms of wallclock (nanosecond precision, monotonic) duration.
We take care to provide "fair" measurements for all OPCODEs and all EVM/eWASM implementations involved, whereby there are no factors that would be exogenous to the OPCODE execution but would impact its measurement.
This however will require additional polishing out in Stage II, as well as a rigorous ruleset defining how these instrumentation and measurements shall be conducted.

Additional to measuring the OPCODE execution time we measure the duration of the capture of time itself.
This is motivated by the fact that (especially for the highly performant EVM/eWASM implementations) the execution of a single instruction of the interpreter takes an extremely small amount of time.
To preserve the realistic proportion between the cost of "cheap" and "expensive" OPCODEs, we need to account for the overhead of the time measurement itself.

The instrumentation and measurement were performed for three environments:
1. `geth` **TODO reference** **TODO version etc**
2. `envmone` **TODO reference** **TODO version etc**
3. `openethereum` **TODO reference** **TODO version etc**

all running on the same, but unspecified hardware (to be rectified and accounted for in Stage II).

Each measurement was performed in a sequence of N (`sampleSize`) runs within the same OS process and such sequences were repeated M times, each time bringing up a new OS process.

The implementation of the preliminary instrumentation and measurement can be seen **TODO reference**

#### Preliminary analysis

For Stage I we limited the analysis to graphical representation of the gathered measurements and drawing a few simple statistics, aiming to draw initial conclusions about the feasibility of the instrumentation and measurement approach for Stage I.

Simplifying, the following steps were performed on the measurement data:
- **Timer overhead adjustment** - offset the duration measurements for OPCODEs by an estimate of the timer overhead, proper to the environment (`geth`, `evmone`, `openethereum`)
- draw simple minimums/maximums/means/quantiles etc., boxplots
- **Implementation-relative measurements** - express the instruction duration in multiples of mean duration of a selected "pivot OPCODE", so that we can analyze the relative distribution of computational cost of OPCODEs within each of the environments. This is motivated by the natural fact that implementations vary greatly in overall performance, and differences of cost of OPCODEs would be lost if treated in absolute terms.
- assess the impact of warm-up by plotting out the dynamics of OPCODE durations as a function of the consecutive number of run within the same sample (OS process)
- analyze the dynamics of the timer overhead **TODO reference**

### Preliminary findings

We deliberately defer the presentation of findings in detail until the Stage II, to not jump to conclusions based on results drawn from unfinished tools.

Instead, will present the questions that will be especially interesting to answer in the continuation of this research.

#### Q1: Can we devise a one-size-fits-all set of OPCODE gas costs?

When visually comparing the implementation-relative measurements (see **TODO reference** above), we suspect that at the current state of EVM/eWASM implementations, it might be very challenging to propose gas costs to OPCODEs, which would apply equally well to all.

E.g., from the preliminary measurement data we saw that, for `evmone` and `openethereum`, several arithmetic OPCODEs (range from `DIV` to `MULMOD`) are consequently more expensive to execute than the pivot OPCODE.
This is however not the case for `geth`.
This means that, given these results are accurate, which is to be further confirmed in Stage II, we might not expect a single good set of gas costs for all the OPCODEs in question, unless there is a parallel effort made to optimize the costly OPCODEs in selected implementations.

#### Q2: is measuring of individual instructions feasible?

The obtained results led us to the conclusion that measuring of individual instructions can be feasible.
However, care must be taken to perform validations of the assumption that the lack of timer precision or its overhead, nor the inclusion of timer function calls itself, don't introduce "unfairness" to the measurements collected.
Refer to the validation techniques planned for Stage II analysis in **TODO ref section approach etc** for ideas on tackling this.

#### Q3: How can we explore the entire program space to capture all sources of variability of OPCODEs computational cost

The main intention of the research presented here is to obtain relative comparison of costs of OPCODEs, accounting for the sources of variability that are currently represented by the gas cost schedule.
An example of such variability is that the gas cost of a `SHA3` OPCODE is a function of the size of its arguments, which in turn naturally impacts the computational cost of the operation.

It is tempting to search for sources of variability unaccounted for in the current gas schedule.
A hypothetical example of such situation would be one where, for example, `PUSH1` operation became more expensive after having been repeated multiple times in the program.

#### Q4: How should warm-up be treated?

Preliminary results indicate that first OPCODEs to execute in the program, as well as first OPCODEs to execute in the context of an OS process, have a noticeable penalty in terms of execution duration.
This is a natural phenomenon usually referred to as warm-up in program benchmarking, and the usual treatment is discarding of the first batch of measurement samples.

We need to answer, what is the appropriate amount of warm-up executions which we want to discard, for the measurements to remain "fair" from the point of view of our goals.
A limiting factor here is that the timer code to collect duration measurements itself seems to exhibit a warm-up phase.

In any case, the treatment of warm-up will be such that measurements mimic normal operation of the EVM/eWASM modules within Ethereum nodes.

#### Q5: How to fairly treat EVM/eWASM implementations with JIT capabilities?

`evmone` optimizes its operation by performing a preprocessing step and offloading some computations to be done per code block, rather than per instruction.
As long as it is still functioning as an interpreter, and every instruction is executed separately, this isn't an obstacle.
It may only require the measuring of a single OPCODE in various contexts, allowing us to observe the variability of the OPCODEs cost (see Q3).

## 5. Approach and plan for Stage II

**NOTE** We plan to proceed with the research in Stage II in a highly iterative fashion.
If the findings gathered invalidate the assumptions, the approach and plan will be adjusted.

# Gas Cost Estimator approach strategy

Here we organize thoughts on different approaches to consider.
We focus on EVM for simplicity, but this should be substitutable by eWASM (Ethereum flavored WebAssembly) interpreters throughout the document.

### Goal

For the sake of this document, the goal is:

Propose a method of giving an accurate proposition of the EVM gas for every one of the subset of EVM OPCODEs (and define "accurate").

The method should be feasible for various implementations/hardware etc. and have "good properties".
Ideally, the method should become a standard (framework) for profiling EVM implementations in terms of OPCODE gas costs.

Accurate and good properties, in the context of OPCODE gas cost, mean:
  - it is proportional to its computational cost, or otherwise balanced when compared to other OPCODEs
  - it explains the variation in computational cost coming from different circumstances and/or parameters
  - it is adequate for various implementations and environments _OR_
  - it can be clearly stated when no such value exists because of differences in implementations
  - ideally, it should be possible to validate the estimated gas costs with at least one another method
  - it should have the overhead to measure time (or other aspects of computational cost) under control and "fair" for all OPCODEs

## Program generation

In this section we want to consider possible approaches to sample program generation.

### Properties of program generation

When generating our programs we want to ensure the following:

1. **uniform coverage** - we want programs to cover the space of OPCODEs completely, so that all the OPCODEs are modeled appropriately and "fairly".
    - impact of values on stack is captured (at least at the level of variation per OPCODE)
    - impact of circumstances where the instructions appear and their "surroundings" is captured
2. **little measurement noise** - we want programs to be such that noise is limited.
    - in particular we want to be able to tell, if factors external to the OPCODE traits can impact the measurement
    - i.e. we want to separate "good variance" from "bad variance." The former means variance that captures intrinsic differences in the resource that instructions consume. The latter means variance introduced by inadequate measurement and external factors.
3. **feasibility of measurement** - we want programs to be easily supplied to various EVM implementations and measurement harnesses we devise

The final approach to generate programs will be devised in Stage II in an iterative manner, so as to arrive at the simplest solution which gives good results.

To start the design iterations, we have the following possible alternatives:

#### Simplest valid program

**NOTE** This has already been implemented.

This set of programs will have one program per OPCODE and it will be a smallest and simplest program which successfully executes the instructions and stops.

#### Looped execution with stack balancing

See https://notes.ethereum.org/@chfast/benchmarking-evm-instructions

#### Completely randomized with stack balancing **TODO**

#### Automated, adaptive generation

This is somewhat similar to the approach from the ["Broken metre" paper](https://arxiv.org/pdf/1909.07220.pdf), which describes a genetic algorithm minimizing the gas throughput (gas/second).

We could modify this idea to run a genetic algorithm (or any other adaptive method with an objective function) maximizing our desired properties, i.e.:
  - maximize variance (information) captured in the measurement of a particular OPCODE, in particular circumstances (particular `program`, particular location)
  - minimize variance (noise) coming from different environments
  - maximize uniformity

This could also be useful do discover the impact of circumstances ("surrounding"), where a particular OPCODE can exhibit much different computational burden, depending on where it is located in the program.

One challenge is how to model OPCODEs with variable parameters (i.e. sha3): they would have unbounded values and also unbounded variance, if not modeled correctly.
  - could model as `t = c + a*x`, `c` constant, `x` size, `a` coefficient to model. Then, instead of most variance/information about `t`, we want most information on `c` and `a`.

## Instrumentation and measurement

In this section we want to consider possible approaches to instrumentation and measurement of sample program execution.
In this section, let's assume we're instrumenting and measuring a particular program.

### Possible ways of executing w/ instrumentation

We can execute an EVM program, with some form of instrumentation enabled.

The choice of which instrumentations are enabled is important, because we are suspecting it may impact the measurements obtained.
In case this is not significant impact, that's good news, but we must have a concrete way of deciding about this.

1. **instrument** - produces a list of OPCODEs in order of execution (this is the simplest one, because we expect for a particular program, this list is always identical - EVM's determinism)
2. **measure all** - produces a list of measurements per instruction, in order of execution, _for all instructions in the program_.
3. **measure one** - produce a single measurement for a chosen instruction, i.e. "measure Nth instruction from start of program"
4. **measure total** - produce a single overarching measurement for the entire program execution
    - for a single instruction we can then have a **measure inferred** value, whereby we deduct the _a priori_ known measurements of other instructions from the total. E.g. we have a value for `PUSH1` and for a `PUSH1, PUSH1, ADD` program we can infer a measurement of `ADD`.

When we speak of measurements, we have the following values in mind (to be decided):
1. **time** - wall clock time (the most universal and likely one)
2. **cycles** - CPU cycles using TSC (`RDTSC`, `gotsc` etc.)

### Individual measurement vs entire program execution measurement

The main question regarding the measurement of (CPU-bound) computational cost of instructions is, whether it is the individual instruction execution to be measured or an entire program execution, consisting of multiple instructions.

**Pros - individual instructions**

[See here](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration.nb.html) for preliminary results.

Here we measure the computational cost of each iteration of the inner loop of the EVM interpreter.
- measurement is more granular and allows us to analyze the measurements without worrying about statistical errors
- in particular, it allows for granular discrimination between cost of OPCODEs located in various circumstances ("surroundings")

**Cons**

- need to be careful about timer precision and overhead (preliminary results try to account for it)

**Pros - entire program measurement**

[See for example here](See https://notes.ethereum.org/@chfast/benchmarking-evm-instructions)

- impact of timer precision and overhead on the measurements is much less problematic
- program execution more resembling the production environment, no tracing/debug calls

**Cons**

- couples the intrinsic effect of instruction circumstances with their statistical impact on the estimator outcome
- must be more careful about program generation, to not have a dataset with adverse statistical properties (e.g. we'd need a very homogenous and random program generator, which is hard given the need to balance the stack)
- @chfast: for long running programs where "full" stack balancing is needed instructions are measured in groups which are difficult to split. I.e. every instruction increasing stack height must be countered by an instruction reducing the stack height. E.g. it is easy to measure the time of `DUP1 + POP` and `PUSH1 + POP` and you can also get time different of `PUSH1` and `DUP1`. But I don't see a way to get the time of `POP` from these or any other instruction pairs configurations.

**Proposition**

Use individual instructions as the estimator and the entire program measurement as validation.
Our goal metric can be how closely does the estimate coming from individual measurements can model the cost of an entire program

### Timer overhead adjustment

It is natural, that the reading of a timer has itself an overhead. In a sequence:

```
t0 = timer.now()
measured_code...
t1 = timer.now()
```
what is really measured is both the `measured_code` and `timer.now()`.
Since in our case for **individual instructions** measurements, `measured_code` sometimes executes within a few nanoseconds, it is necessary to account for the timer overhead.

We initially do that within our [preliminary results](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration.nb.html) by subtracting a rough estimate of the overhead for both environments.

The [estimation of timer overhead is done in these preliminary results](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration_timers.nb.html) (for now `geth`-only, but should be expanded for other environments).
The rough estimate is the mean duration between two `timer.now()`s, one immediately after the other.

For `evmone` we have temporarily used a guesstimate leveraging [these results](https://notes.ethereum.org/@chfast/benchmarking-evm-instructions), see the preliminary analysis for details.

Moving forward, we are planning to continue adjusting for the timer overhead with the remarks in [the preliminary exploration of timers](/home/user/sources/imapp/gas-cost-estimator/src/analysis/exploration_timers.Rmd) left at the end.

We should also separately conduct a statistical test that for every OPCODE, a measurement of the timer overhead is significantly smaller, or prepare a similar argument.

### Repetition

We should repeat the execution, regardless of the instrumentation enabled.
We call a single repetition of the program's execution, under the same harness and within the same instance/process etc. a **run**.

#### Discarding warm-up

Some initial measurements have been detected to be larger, and they might either be discarded or kept.

It should be explored, whether normal node operation exhibits such "initial conditions" regularly or not. (**TODO**)
Regardless, all OPCODEs should receive fair treatment in this aspect.

Practically, we keep all the measurements for all runs as a series, and decide on discarding/keeping at the Analysis stage.

### Example of measurement data

First draft, just to visualize the scope of data collected

|program_id|sample_id|run_id|instruction_id|measure_all_time_ns|measure_one_time_ns|timer_overhead_time_ns|
|----------|---------|------|--------------|-------------------|-------------------|----------------------|
|          |         | 34   |   58         |1234               |1204               | 300                  |
|          |         | 34   |   59         |1231               |1200               | 432                  |

- **program_id**
- **sample_id** - some form of identification of the entire sequence of runs
- **run_id** - sequence number of the repetition (to possibly discard warm-up runs etc.)
- **instruction_id** - sequence number of the instruction, necessary to correlate with OPCODE list
- **measure_all_time_ns** - if the measurement was a "measure all" - time it took to execute the instruction
- **measure_one_time_ns** - as above, if the measurement was a "measure one"
- **timer_overhead_time_ns** - **TODO new** an accompanying measurement of timer overhead done just after the timer capture for the instruction

On top of that, we also collect a per-run information:

|program_id|sample_id|run_id|measure_total_time_ns|
|----------|---------|------|---------------------|
|          |         |    34| 1234241             |

And some per-sample metadata:

|program_id|sample_id|instrumentation|environment   |
|----------|---------|------------------|-----------|
|          |   12    | "measure all"   | evmc-evmone|
|          |   13    | none            | evmc-evmone|

- **instrumentation** - what kinds of instrumentation where turned on during this sample
- **environment** - what kind of environment this ran on

The OPCODE "footprint" to accompany the measurement data is:

|program_id|instruction_id|OPCODE|arguments|stack|
|----------|--------------|-------------------|------|-----|
|          |   58         |PUSH1               | [15] | [] |
|          |   59         |ADD               | [] | [1234,1555]|

- **arguments** - the arguments passed along with the instruction
- **stack** - the values on the stack that the instruction consumed

### Instrumenting and measuring the computations from blockchain history

For an additional validation of the gas cost estimates, we could consider instrumenting and measuring a fragment of the blockchain.

The problem arises from the fact that our gas cost estimator is prepared only for a subset of instructions (in particular, no IO/storage instructions).
We could consider calibrating these together by picking a "pivot OPCODE", whose gas cost would remain unchanged, and adjusting gas cost for all other OPCODE from the analyzed subset to match relative difference in cost to the pivot OPCODE.

Next we could:
1. Calculate the gas cost for a sequence of real blocks, using such adjusted gas costs.
2. Capture a coarse measurement of resources consumed to validate those blocks (e.g. time per block, time per transaction).

**TODO** - check prior art on this - has this been done with vanilla gas cost values? E.g. to compare Ethereum implementations?

## Analysis

Questions that the analysis stage should strive to answer:

1. Is the choice of sample programs adequate?
2. Is the method of measurement adequate?
3. What is the gas cost estimation for every OPCODE analyzed?
4. What is the quality of the particular gas cost estimation?
5. What are the differences of gas cost estimations for various implementations, and how these might be addressed?

In order to explore the behavior of programs, measurements and environments, let's conduct a series of comparisons and analyzes.
List of tests:

1. Compare mean, variance, distribution for a single OPCODE with various forms of instrumentation enabled:
    - "measure all"
    - "measure one"
    - (optionally) "measure inferred" only, so no instrumentation
2. Compare mean, variance, distribution for a single (simple) OPCODE, coming from different sample programs (or possibly from different `run_id` or `instruction_id`, i.e. how the OPCODE behaves in different circumstances in terms of the program it is a part of)
3. Compare mean, variance, distribution for various OPCODEs in the same manner, see if there's a pattern?
4. Analyze measurement overheads by comparing sums of individual instruction measurements with total measurements.
5. Assume a set of example gas cost estimators and compare their results, should they be applied. Compare with todays gas costs for OPCODEs
    - Use blockchain history results to compare various gas cost estimators with resources usage (see above).

### Implementation-relative measurements

When comparing measurements coming from different implementations (or hardware environments) it is useful to compare using measurements expressed in multiples of mean duration of a selected "pivot OPCODE" (or mean across all OPCODEs, but this is probably less reliable). See [preliminary analysis here](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration.nb.html) for the initial pick of the pivot OPCODE.

### Detailed validation techniques

Here we outline the current options for validations to do to the obtained measurements.

1. **compare individual instruction vs entire program execution** - see how good the former is in predicting the latter (see [Individual measurement vs entire program execution measurement](#Individual-measurement-vs-entire-program-execution-measurement))
2. **analyze individual OPCODEs dynamics** - generate a multitude of programs whereby the OPCODE is ran in varying circumstances. See if the measurement error is random and we're accounting for all the dynamics of computational cost of the OPCODE.
3. **cross-environment OPCODE validation** - check OPCODEs which have drastically different relative estimates in different implementations/hardwares, decide whether the reason is intrinsic to the implementation/hardware or is measurement error
3. **historical validation** - check against blockchain history under normal conditions where the node is ran (see [Instrumenting and measuring the computations from blockchain history](#Instrumenting-and-measuring-the-computations-from-blockchain-history))
4. **cross-timer validation** - capture all results using an alternative CPU cost proxy (e.g. instead of `runtimeNano` use `gotsc` CPU cycles), see how they compare.
5. **validate distribution of measurements for individual OPCODEs** - they look weird, but this is probably due to the way we plot them now, this should be explained.

## Appendix A: detailed task list

## Appendix B: OPCODEs subset

## References

[1] [https://etherscan.io/block/11660498](https://etherscan.io/block/11660498)
