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
Currently, gas cost is determined on a per-OPCODE basis, that is, every OPCODE interpreted by the EVM/eWASM has a predetermined gas cost (or its gas cost is expressed as a function of instruction's arguments).
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

This report and the entire "Gas Cost Estimator" project are focusing on a subset of EVM/eWASM OPCODEs.
The OPCODEs in this subset (see [Appendix B: OPCODEs subset](#appendix-b-opcodes-subset) have in common that they do not include any instructions which access the Ethereum storage (e.g. `SSTORE`, `SLOAD` etc.).
On one hand, the focus on only purely computational instructions is intended and desirable, as seen from the point of view whereby the importance of on-chain computations will increase, while the extensive use of Ethereum storage will diminish.
This is driven by the current influx of L2-scalability solutions, which only store the minimum amount of data, putting the burden of providing data on the transaction senders and the burden of validating it on the smart contract.
**TODO find ref**.
On the other hand, we intend to consider extending the method devised here to storage-bound instructions in the future as well.

### Standardization

One of the factors that contribute to the challenge which gas cost estimation presents is the inherent multitude of environments involved.

By environments in this context we mean:
  - different implementations of the Ethereum node (and EVM/eWASM in consequence), done in different programming languages and with different mindsets.
  - different hardware on which this software is ran; this is exacerbated by the requirement towards the software to run reliably on both server-grade hardware and consumer-grade desktops alike
  - different operating systems.

Given the inclusive nature of Ethereum, we are required to examine and include in the analysis the entire spectrum of these environments and determine how much does the environment impact the estimated gas costs. It is desirable, and is intended to be considered in the Stage II of the project, that the method devised here is reasonably easily applicable in those varying environments.
To this end, the approach must be well documented and reproducible by the community.

### Anticipation of Stage II

This report anticipates the completion of Stage II of the project.
Given that, we focus on setting forth a plan and strategy for conducting the future measurements and analysis, rather than providing answers or recommendations for gas cost adjustments straight away.

## 4. Preliminary work and findings of Stage I

None of the quantitative results obtained at Stage I of this research are final nor should be quoted.
There are many caveats and detail work yet to be done, which will impact the final results and conclusions.
As a consequence, we are phrasing our preliminary findings as questions that need to be considered in Stage II.

At Stage I a survey of existing literature and related work was done. We defer writing a full section on this to the Stage II paper.

### Preliminary method

During the execution of Stage I, preliminary experiments and analysis were performed in order to explore the dynamics of computational effort which OPCODEs of EVM/eWASM exhibit.
The intention of this exploration was to propose a method for gas cost estimation, which would be further advanced and validated in Stage II.

The method consists of three separate domains:
1. **Program generation** - entails generation of EVM/eWASM bytecode programs which will be executed in order to gather measurements
2. **Instrumentation and measurement** - entails the process of running the generated programs in a controlled environment and performing various measurements
3. **Analysis** - entails the process of statistical analysis and validation of the obtained measurement data

In the following subsections, the preliminary implementation of these three domains will be briefly described.
Refer to the section (**TODO ref**) for the planned approach to complete these implementations in Stage II.

#### Preliminary program generation

For Stage I we used the "Simplest valid program" approach.
This set of programs will have one program per OPCODE and it will be a smallest and simplest program which successfully executes the instructions and stops.
Additionally to this, we excluded several OPCODEs, which treatment should be polished out in Stage II (`JUMP`, `JUMPI`, `RETURNDATACOPY`).
We also neglected the entire dimension of arguments supplied to the OPCODEs execution (e.g. `SHA3`), which have substantial impact on the computational cost.

The source code for preliminary program generation employed can be seen **TODO reference**.

#### Preliminary instrumentation and measurement

For Stage I we used the "measure all" approach for individual EVM/eWASM instructions.
We measured the entire iteration of the interpreter main loop for every instruction in terms of wall clock (nanosecond precision, monotonic) duration.
We took care to provide "fair" measurements for all OPCODEs and all EVM/eWASM implementations involved, to minimize factors that would be exogenous to the OPCODE execution, and could impact its measurement.
This in particular will require additional polishing out in Stage II, as per [notes left here](https://github.com/imapp-pl/gas-cost-estimator/blob/master/docs/notes/execution_comparison.md), [here](https://github.com/imapp-pl/gas-cost-estimator/blob/master/docs/notes/instrumentation_measurement/evmone.md), [here](https://github.com/imapp-pl/gas-cost-estimator/blob/master/docs/notes/instrumentation_measurement/geth.md) and [here](https://github.com/imapp-pl/gas-cost-estimator/blob/master/docs/notes/instrumentation_measurement/openethereum.md).

Additional to measuring the OPCODE execution time we measure the duration of the capture of time itself.
This is motivated by the fact that (especially for the highly performant EVM/eWASM implementations) the execution of a single instruction of the interpreter takes an very small amount of time.
To preserve the realistic proportion between the cost of "cheap" and "expensive" OPCODEs, we need to account for the overhead of the time measurement itself.

The instrumentation and measurement were performed for three environments:
1. `geth` **TODO reference** **TODO version etc**
2. `envmone` **TODO reference** **TODO version etc**
3. `openethereum` **TODO reference** **TODO version etc**

all running on the same but unspecified hardware (to be rectified in Stage II).

Each measurement was performed in a sequence of N (`sampleSize`) runs within the same OS process and such sequences were repeated M times, each time bringing up a new OS process.

For the environment which has garbage collection (`Go/geth`), the automatic garbage collection was turned off and manually triggered before each program run.

The implementation of the preliminary instrumentation and measurement can be seen **TODO reference**

#### Preliminary analysis

For Stage I we limited the analysis to graphical representation of the gathered measurements and calculating a few simple statistics, aiming to draw initial conclusions about the feasibility of the instrumentation and measurement approach for Stage I.

Simplifying, the following steps were performed on the measurement data:
- **Timer overhead adjustment** - offset the duration measurements for OPCODEs by an estimate of the timer overhead, proper to the environment (`geth`, `evmone`, `openethereum`)
- draw simple minimums/maximums/means/quantiles etc., boxplots
- **Implementation-relative measurements** - express the instruction duration in multiples of mean duration of a selected "pivot OPCODE", so that we can analyze the relative distribution of computational cost of OPCODEs within each of the environments. This is motivated by the natural fact that implementations vary greatly in overall performance, and differences of cost of OPCODEs would be lost, if treated in absolute terms.
- assess the impact of warm-up by plotting out the dynamics of OPCODE durations as a function of the consecutive number of run within the same sample (OS process)
- do simple analysis of the dynamics of the timer overhead

### Preliminary findings

We deliberately defer the presentation of findings in detail until the Stage II, to not jump to conclusions based on results drawn from unfinished tools.

Instead, we will present the questions that will be especially interesting to answer in the continuation of this research.

#### Q1: Can we devise a one-size-fits-all set of OPCODE gas costs?

After visually comparing the implementation-relative measurements (see **TODO reference** above), we suspect that at the current state of EVM/eWASM implementations, it might be challenging to propose gas costs to OPCODEs, which would apply equally well to all.

E.g., from the preliminary measurement data we saw that, for `evmone` and `openethereum`, several arithmetic OPCODEs (range from `DIV` to `MULMOD`) are consequently more expensive to execute than the pivot OPCODE.
This is however not the case for `geth`.
This means that, given these results are accurate, which is to be further confirmed in Stage II, we might not expect a single good set of gas costs for all the OPCODEs in question, unless there is a parallel effort made to optimize the costly OPCODEs in selected implementations.

#### Q2: is measuring of individual instructions feasible?

The obtained results led us to the conclusion that measuring of individual instructions can be feasible.
However, care must be taken to perform validations of the assumption that the lack of timer precision or its overhead, nor the inclusion of timer function calls itself, don't introduce "unfairness" to the measurements collected.
Refer to the validation techniques planned for Stage II analysis in **TODO ref section approach etc** for ideas on tackling this.
There, we will also list possible fallback plans in case there is evidence that the noise and overhead present in this method of measurement is unacceptable.

#### Q3: How can we explore the entire program space to capture all sources of variability of OPCODEs computational cost

The main intention of the research presented here is to obtain relative comparison of costs of OPCODEs, accounting for the sources of variability that are already represented by the current gas cost schedule.
An example of such variability is that the gas cost of a `SHA3` OPCODE is a function of the size of its arguments, which naturally impact the computational cost of the operation.

It is tempting to search for sources of variability unaccounted for in the current gas schedule.
A hypothetical example of such situation would be one, where, for example, `PUSH1` operation became more expensive, after having been repeated multiple times in the program.

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

#### Q6: How to standardize the gas cost estimation procedure?

As noted earlier, we envision that an added feature of the research could be a standard procedure to estimate gas costs in other environments.
Similar attempts have been made in **TODO reference**.

See section (**TODO ref approach and plan**) for the plan how to facilitate standardization.

## 5. Approach and plan for Stage II

We will proceed with the research in Stage II in a highly iterative fashion.
If the findings gathered invalidate the assumptions, the approach and plan will be adjusted.

### Goal of Stage II

Propose a method of giving an accurate proposition of the EVM/eWASM gas costs for every one of the subset of EVM OPCODEs, as well as define what "accurate" means and how to assess it.

The method should be feasible for various implementations/hardware etc. and have "good properties".
Ideally, the method should become a standard (framework) for profiling EVM implementations in terms of OPCODE gas costs.

Accurate and with good properties, in the context of an estimate of OPCODE gas cost, mean:
  - it is proportional to the OPCODE's computational cost, or otherwise balanced when compared to other OPCODEs,
  - it is modeled to explain the variation in computational cost coming from different circumstances and/or parameters,
  - it is adequate for various implementations and environments _OR_,
  - it can be clearly stated, when no such value exists because of differences in implementations,
  - it should have the measurement overhead and noise under control and "fair" for all OPCODEs.

### Program generation

In this section we describe the approach to sample EVM/eWASM program generation.

Programs will be generated directly as bytecode to be supplied to the EVM/eWASM for execution.

#### Properties of program generation

When generating our programs we want to ensure the following:

1. **uniform coverage** - we want programs to cover the space of OPCODEs completely, so that all the OPCODEs are modeled appropriately and "fairly".
    - impact of values on stack is captured,
    - impact of circumstances where the instructions appear and their "surroundings" is captured.
2. **little measurement noise** - we want programs to be such that noise is limited.
    - in particular we want to be able to tell, if factors external to the OPCODE execution impact the measurement,
    - i.e. we want to separate "good variance" from "bad variance." The former means variance that represents variability in computational cost inherent to the OPCODE execution. The latter means noise introduced by inadequate measurement and external factors.
3. **feasibility of measurement** - we want programs to be easily supplied to various EVM/eWASM implementations and measurement harnesses we devise.

At Stage II, we plan to compile a detailed rundown of the specifics of each OPCODE, to be taken into account when using in program generation and then instrumentation, since some OPCODEs have special traits which should be kept in mind (e.g. `CALLDATASIZE` reads from the calldata input to EVM/eWASM execution, `BALANCE` might depend on the balance of the account checked).

The final approach to generate programs will be devised in an iterative manner, so as to arrive at the simplest solution which gives good results.

To start the design iterations, we have the following possible alternatives:

#### Simplest valid program

**NOTE** This has already been implemented in Stage I, pending some minor fixes.

This set of programs will have one program per OPCODE and it will be a smallest and simplest program which successfully executes the instructions and stops.

#### Simplest valid program with customizable stack/arguments

This is an extension of the "Simplest valid program" approach, where we'll allow to generate programs which execute their OPCODEs with different arguments, so that we can enact their behavior to cover the scope of variability that the current gas schedule allows for (e.g. various sizes of the input for the `SHA3` OPCODE).

#### Simplest valid program with simple surroundings

Before a full-fledged support for exploring various surroundings and their impact on the execution of a given OPCODE, we can provide a simplified probe of the topic.

In this approach, we will generate programs same as in "Simplest valid program" approach, but:
  - prepend and/or append a sequence of fixed arbitrary bytecodes, to put the analyzed OPCODE in the "middle" of the program, and/or
  - multiply the OPCODE with its stack management companions.

Such programs can then be used for initial exploration of the impact of surroundings.

#### Looped execution with stack balancing

See [Benchmarking EVM Instructions by @chfast](https://notes.ethereum.org/@chfast/benchmarking-evm-instructions) (**TODO ref**).

This approach will be very useful to validate the individual instruction measurements with whole-program measurements.

#### Completely randomized with stack balancing

This is an extension of the "Simplest valid program" approach, where we'll generate random programs, mixing instructions of all OPCODEs from the subset, that only are known to execute successfully due to correct stack balancing.

This approach will be very useful to validate the individual instruction measurements with whole-program measurements ("measure total").
Also it will be applicable as the first step towards exploring the sources of variability of OPCODE cost driven by various contexts in which these OPCODEs are executed.

#### Automated, adaptive generation

This is somewhat similar to the approach from the ["Broken metre" paper](https://arxiv.org/pdf/1909.07220.pdf) (**TODO make ref**), which describes a genetic algorithm minimizing the gas throughput (gas/second).
Pursuing this possibility is an optional expansion to the scope of the research, which will be considered at Stage II.

We could modify this idea to run a genetic algorithm (or any other adaptive method with an objective function) maximizing our desired properties, i.e.:
  - maximize variance (information) captured in the measurement of a particular OPCODE, in particular circumstances (particular `program`, particular location)
  - minimize variance (noise) coming from different environments
  - maximize uniformity

This could also be useful to discover the impact of circumstances ("surrounding") (**TODO unify language circumstances, surrounding, context**), where a particular OPCODE can exhibit much different computational burden, depending on where it is located in the program.

One challenge is how to model OPCODEs with variable size of parameters (i.e. `SHA3`): they would have unbounded values and also unbounded variance, if not modeled correctly.
We could model as `t = c + a*x`, `c` constant, `x` size, `a` coefficient to model.
Then, instead of most variance/information about `t`, we want most information on `c` and `a`.

### Instrumentation and measurement

In this section we describe the approach to instrumentation and measurement of sample program execution.

We will execute an EVM/eWASM program, with one chosen form of instrumentation and measurement enabled:

1. **trace OPCODEs and arguments** - produces a list of OPCODEs for all instructions executed in a program, along with their relevant arguments (stack, memory). This will be used to know what were the instructions executed during a single run of a program.
2. **measure all** - (individual instruction measurement) produces a list of measurements per instruction, in order of execution, _for all instructions in the program_.
3. **measure one** - (individual instruction measurement, optional) produce a single measurement for a chosen instruction, i.e. "measure Nth instruction from start of the program".
4. **measure total** - (whole-program measurement) produce a single overarching measurement for the entire program execution.
4. **measure batch** - (hybrid measurement, optional) produce a single measurement for a sequence of same OPCODEs, according to metadata passed to the instrumentation code (e.g. `{measure_from_instruction: 123, measure_to_instruction: 234}` will measure 111 adjacent instructions as if they were one)

When we speak of measurements, we will be measuring the wall clock time.
Measurements of CPU cycles using TSC (`RDTSC`, `gotsc` etc.) might be used for validation and comparison.

#### Measurement "fairness" and coverage

As already started in Stage I effort, we will further polish out the "fairness" of measurements for all OPCODEs and all EVM/eWASM implementations involved, to minimize factors that would be exogenous to the OPCODE execution, and could impact its measurement.

In particular, but not limited to, we will take care that in each environment and for each OPCODE, the scope of measured execution is as similar as possible, so that the results are comparable.

We will also make sure, and elaborate on, to represent as closely as possible the scope of execution to that which is proper to the EVM/eWASM functioning within an operating Ethereum node.

A particular facet of this is the approach to garbage collection.
We can continue to turn the garbage collector off and trigger manually outside of measured scope, as we did in Stage I, in case it is established, that this approach is "fair" for all OPCODEs, that is we miss out the impact of OPCODEs on garbage collection and impact of garbage collection on OPCODE computations evenly.
Alternatively we can leave the garbage collection on by default and factor its impact into our analysis.

#### Individual measurement vs entire program execution measurement

The main question regarding the measurement of (CPU-bound) computational cost of instructions is, whether it is the individual instruction execution to be measured or an entire program execution, consisting of multiple instructions.

In the former, we measure each iteration of the inner loop of the EVM/eWASM interpreter.
[See Stage I preliminary results](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration.nb.html) for an example application of this approach.

**Pros**

- measurement is more granular and allows us to analyze the measurements without worrying about statistical errors,
- in particular, it allows for granular discrimination between cost of OPCODEs located in various circumstances ("surroundings").

**Cons**

- need to be careful about timer precision and overhead (preliminary results try to account for it).

In the latter approach we measure the entire execution of the EVM/eWASM interpreter loop, [see for example here](https://notes.ethereum.org/@chfast/benchmarking-evm-instructions).

**Pros**

- impact of timer precision and overhead on the measurements is much less problematic,
- program execution resembles production operation more, there are no instrumentation calls within the interpreter loop.

**Cons**

- couples the intrinsic effect of instruction circumstances with their statistical impact on the estimator outcome,
- must be more careful about program generation, to not have a dataset with adverse statistical properties (e.g. we'd need a very homogenous set of generated programs, which is hard given the need to balance the stack),
- the need to do stack balancing, which consists in injecting `PUSH...` (`DUP...`) and `POP` instructions will interfere with the estimator values. (**TODO ref to gh convo with `chfast`**)

**Plan for Stage II:** Use individual instructions as the estimator and the entire program measurement as validation.
Our goal metric can be, how closely does the estimate coming from individual measurements can model the cost of an entire program.

In case individual measurements method is deemed unacceptable, following fallback plans are possible:
  - for very cheap OPCODEs, substitute individual instruction occurrences (e.g. `ISZERO`) with sequences of many instructions with pre-balanced stack (e.g. `DUP1 x 99, ISZERO x 100`) and use the "measure batch" instrumentation,
  - use a binomial or similar model to extract the duration of an event shorter than the timer resolution (**TODO ref to paper Platform Independent Timing of Java Virtual Machine Bytecode Instructions**),
  - use CPU cycles as a proxy of computational cost, instead of wallclock duration.

#### Timer overhead adjustment

The reading of a timer has itself an overhead. In a sequence of steps:

```
t0 = timer.now()
measured_code...
t1 = timer.now()
```

what is really measured is both the `measured_code` and `timer.now()`, latter being the overhead of the timer.
Since in our case for **individual instructions** measurements, `measured_code` sometimes executes within a few nanoseconds, it is necessary to take extra care to ensure that the timer overhead is as small as possible, and to account for it in the analysis step.

We do that within our [preliminary results](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration.nb.html) by subtracting an estimate of the overhead for all environments (`Go/geth`, `C/evmone`, `Rust/OpenEthereum`).

The [estimation of timer overhead is done in these preliminary results](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration_timers.nb.html).
As the timer overhead estimate we use the minimum observed duration between two `timer.now()`s, one immediately after the other.

Moving forward, we are planning to continue adjusting for the timer overhead, with the following improvements:
- we'll monitor and register the timer overhead during the OPCODE measurements. This is motivated by the observation from the preliminary results, that the timer overhead measured exhibits periodic bumps. We will consider filtering out the measurements where the measure timer overhead was above a given threshold,
- we should also separately conduct a statistical test that for every OPCODE, a measurement of the timer overhead is significantly smaller than the timer overhead, or prepare a similar argument **TODO ref validation section**.

#### Repetition and accounting for warm-up

We will repeat the execution a number of times, within the same instance of the EVM/eWASM environment (e.g. OS process etc.).
Every such repetition will be called a **run**.

Measurements for initial runs have been detected to be larger, and they might either be discarded or kept.

It will be explored, whether normal node operation exhibits such "initial conditions" regularly or not.
Regardless, all OPCODEs should receive fair treatment in this aspect.

### Analysis

In this section we outline the approach to analyzing the obtained measurement data.
Questions that the analysis stage should strive to answer:

1. Is the choice of sample programs adequate?
2. Is the method of measurement adequate?
3. What is the gas cost estimation for every OPCODE analyzed?
4. What is the quality of the particular gas cost estimation?
5. What are the differences of gas cost estimations for various implementations, and how these might be addressed?

#### Implementation-relative measurements

When comparing measurements coming from different implementations (or hardware environments) it is useful to compare using measurements expressed in multiples of mean duration of a selected "pivot OPCODE" (or mean across all OPCODEs, but this is probably less reliable). See [preliminary analysis here](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration.nb.html) for the values obtained in this fashion.
For the preliminary analysis, the OPCODE `COINBASE` was chosen arbitrarily, this choice will be revisited.

We'll use implementation-relative measurements whenever we want to compare the relative proportions of OPCODE measurements between environments (mainly different implementations).

#### Estimation validation and exploration

Here we outline the choice of options for validations to do on the obtained measurements.

1. **compare OPCODE measurement statistics between themselves and between different implementations** - inspect the means/quantiles/variances/distributions and look for abnormalities, list out and attempt to explain them.
1. **compare individual instruction vs entire program execution** - see how well does the former predict the latter (see [Individual measurement vs entire program execution measurement](#Individual-measurement-vs-entire-program-execution-measurement))
2. **analyze individual OPCODEs dynamics** - generate a multitude of programs whereby the OPCODE is ran in varying circumstances. See if the measurement error is random and we're accounting for all the dynamics of computational cost of the OPCODE.
3. **cross-environment OPCODE validation** - check OPCODEs which have drastically different relative estimates in different implementations/hardwares, look into whether the reason is intrinsic to the implementation/hardware or is due to error.
4. **impact on gas cost schedule** - estimate the gas costs, calibrate to the excluded OPCODEs and compare with current gas schedule. Repeat for estimations from various environments and methods. Analyze the impact of gas cost adjustments.
3. **historical validation** - check against blockchain history under normal conditions where the node is ran (see [Instrumenting and measuring the computations from blockchain history](#Instrumenting-and-measuring-the-computations-from-blockchain-history))
4. **cross-timer validation** - capture all results using an alternative CPU cost proxy (e.g. instead of `runtimeNano` use `gotsc` CPU cycles), see how they compare.

#### Instrumenting and measuring the computations from blockchain history

For an additional validation of the gas cost estimates, we consider instrumenting and measuring a fragment of the blockchain.

The problem arises from the fact that our gas cost estimator is prepared only for a subset of instructions (in particular, no IO/storage instructions).
We will consider calibrating these together by picking a "pivot OPCODE", whose gas cost would remain unchanged, and adjusting gas cost for all other OPCODE from the analyzed subset to match relative difference in cost to the pivot OPCODE.

Next we could:
1. Calculate the gas cost for a sequence of real blocks, using such adjusted gas costs.
2. Capture a coarse measurement of resources consumed to validate those blocks (e.g. time per block, time per transaction).
3. Assess how well does the adjusted gas schedule model the consumed resources.

### Standardization

The standardization effort will be done in the three domains:
- **Program generation** - this being the simplest one, as it doesn't directly depend on the environment. The requirement is here that program generation is well documented and easily pluggable into the rest of the stack. To this end standard program generating scripts will be devised, along with standard input/output data formats,
- **Instrumentation and measurement** - here data standards for output/input will be proposed as well. On the other hand a ruleset for each of the measurement methods will be designed, where the standard instruction measurement guidelines will be given,
- **Analysis** - a suite of scripts to visualize and validate the measurement data will be given. Due to the exploratory nature of this domain, this is treated as more optional. Ideally, a script which takes program and measurement data as input and presents all the plots and statistics used to validate the process as output, could be designed.

## Appendix A: detailed task list

In here, we collect a tentative list of various tasks and todos to complete in Stage II, which were identified during the completion of Stage I.
This list _is not_ an exhaustive work breakdown structure for Stage II, as well as some of these tasks might be deemed unnecessary or optional (denoted "(opt)") during the execution of Stage II.

Refer to the other sections for details on the tasks.

1. Program generation tasks
    1. Compile a detailed rundown of the specifics of each OPCODE
    2. Allow to customize stack/arguments
    4. Generate programs with simple surroundings added to a single OPCODE
    3. Generate programs with looped execution with stack balancing
    4. (opt) Generate random programs with stack balancing
    5. (opt) Generate programs via automated, adaptive generation
    6. Redesign input/output data structures, document and standardize
    7. Make program generation easily pluggable into the rest of the stack, standardize and document
2. Instrumentation and measurement tasks
    1. Allow to trace OPCODEs and arguments via instrumentation
    3. Improve, make "fair" and ensure full coverage of execution for the "measure all" instrumentation
    2. (opt) Allow to do "measure one" instrumentation for instruction by index
    4. Allow to do "measure total" instrumentation fairly and with full coverage of execution
    5. (opt) Allow to do "measure batch" instrumentation
    5. (opt) Possibly adjust the instrumentation to doing the modelling of duration via the binomial model
    6. (opt) Try and compare alternative wallclock timers (e.g. PAPI)
    7. (opt) Provide full support for CPU cycles using TSC libraries
    8. Write down the instrumentation and measurement standard ruleset
    9. (opt) Try further lowering the overhead of wallclock timers
    10. Provide consistent treatment of warm-up
    11. Analyze warm-up conditions versus normal EVM/eWASM operation within an Ethereum node
    12. Support gathering of timer overhead measuremnts during OPCODE measurements
    13. Support for instrumentation in at least one another eWASM implementation
    14. Rethink the approach to garbage collection for environments that have one
3. Analysis tasks
    1. Tidy and improve structure of the existing analysis code in R, allow for its extensibility
    1. Improve the visualization method to check distributions of measurements per OPCODE and environment (frequency plots used in Stage I are not useful)
    1. Look into the extreme outliers in OPCODE measurements, if they are still present after rectifying the instrumentation stack
    1. Revisit the choice of the pivot OPCODE for implementation-relative measurements, describe criteria for this choice
    1. Allow analysis of OPCODE measurements coming from programs in which their execution has been parametrized (via arguments, context, surroundings)
    2. Explore validation methods proposed
    3. Implement automated scripts for the chosen validation methods
    4. (opt) Implement (or adapt an existing implementation or existing data sets, if they exist) validation via blockchain history
    5. Give recommendations for any gas cost adjustments which could be safely done at current stage (i.e. ones which are reasonable consistently between all environments measured)
    6. Identify OPCODEs which will not have a gas cost suitable for all environments and try to find the cause and recommend optimizations
    6. Answer "Q1: Can we devise a one-size-fits-all set of OPCODE gas costs?"
    7. Provide a quantitative argument (e.g. a statistical test) that for every OPCODE, measurement of the timer overhead is significantly smaller
    7. Answer "Q2: is measuring of individual instructions feasible?"
    8. (opt) Devise scoring functions which can be used to adaptively generate programs
    8. (opt) Provide a performant implementations of the scoring functions which can be reasonably plugged into an search algorithm for adaptive program generation
    8. (opt) Answer "Q3: How can we explore the entire program space to capture all sources of variability of OPCODEs computational cost"
    9. Answer "Q4: How should warm-up be treated?"
    10. (opt) Answer "Q5: How to fairly treat EVM/eWASM implementations with JIT capabilities?"
    11. (opt) Answer "Q6: How to standardize the gas cost estimation procedure?"
4. Hardware and environment diversity tasks
    1. Provision and run measurements on a machine in the cloud
    2. Provision and run measurements on representative consumer-grade machines of various kinds
5. Standardization tasks
    5. Ensure easy application of the automated scripts for validation methods, document
6. Documentation tasks
    1. Write full section on Related Work, from sources gathered in Stage I and Stage II

## Appendix B: OPCODEs subset (**TODO**)

## Acknowledgements (**TODO**)

## References (**TODO**)

[1] [https://etherscan.io/block/11660498](https://etherscan.io/block/11660498)
