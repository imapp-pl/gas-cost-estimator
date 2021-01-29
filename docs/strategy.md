# Gas Cost Estimator approach strategy

----

**NOTE: parts of this doc have been moved to the Stage I report. `strategy.md` may be a bit too speculative and obsolete/incomplete. Refer to the Stage I report first**

----

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

#### Completely randomized with stack balancing

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
