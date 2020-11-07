# Gas Cost Estimator approach strategy

Here we organize thoughts on different approaches to consider.
We focus on EVM for simplicity, but this should be substitutable by eWASM throughout the document.

### Goal

For the sake of this document, the goal is:

Propose a method of giving an accurate proposition of the EVM gas for every one of the subset of EVM OPCODEs (and define meaning of "accurate").

The method should be feasible for various implementations/hardware etc. and have "good properties".
Ideally, the method should become a standard (framework) for profiling EVM implementations in terms of OPCODE gas costs.

**TODO** - define "accurate"
**TODO** - define "good properties" - what they are and how can we measure them / reason about them?

## Program generation

In this section we want to consider possible approaches to sample program generation.

### Properties of program generation

When generating our programs we want to ensure the following:

1. **uniform coverage** - we want programs to cover the space of OPCODEs completely, so that all the OPCODEs are modeled appropriately.
    - in particular all impact of values on stack is captured (at least at the level of variance per OPCODE)
2. **little measurement noise** - we want programs to be such that noise is limited.
    - in particular we want to be able to tell, if factors external to the OPCODE traits can impact the measurement
    - i.e. we want to separate "good variance" from "bad variance.". The former means variance that captures intrinsic differences in the resource that instructions consume. The latter means variance introduced by inadequate measurement and external factors.
3. **feasibility of measurement** - we want programs to be easily supplied to various EVM implementations and measurement harnesses we devise

### Questions

Q: how do you build the programs so that you can supply input values (arguments, stack, memory) to the OPCODEs measured?

Q: how does the measurement method impact the requirements for program generation? Can we decouple those?

Q: will manual, "best guess" generation of sample programs do, or should it be a result of some feedback loop (see also _Instrumentation and measurement_)
    - probably, if we find the "measure one" approach to give good results, manual will be good. Similar with "measure all", since it still measures instructions individually.
    - if we find that instructions cannot be reliably measured individually, and we have to revert to "measure total", it is likely that some algorithmic way of generating the sample program set is necessary.

### Additional ideas

1. "Broken metre" paper does a genetic algorithm minimizing the gas throughput (gas/second).
Could we modify this idea to run a genetic algorithm maximizing our desired properties, i.e.:
    - maximize variance (information) captured in the measurement of a particular OPCODE
    - minimize variance (noise) coming from different environments
    - maximize uniformity

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
    - for a single instruction we can then have a **measure pro-rated** value, whereby we "split" the measurement total into contributions proportional to the count of each OPCODE instructions (**NOTE** this way of counting might be controversial and requires a special approach to the sample program set)
    - for a single instruction we can then have a **measure inferred** value, whereby we deduct the _a priori_ known measurements of other instructions from the total. E.g. we have a value for `PUSH1` and for a `PUSH1, PUSH1, ADD` program we can infer a measurement of `ADD`.

When we speak of measurements, we have the following values in mind (to be decided):
1. **time** - wall clock time (the most universal and likely one)
2. **TODO**

### Repetition

We should repeat the execution, regardless of the instrumentation enabled.
We call a single repetition of the program's execution, under the same harness and within the same instance/process etc. a **run**.

Q: should some measurements for some runs be discarded (e.g. cache warm up etc.)? or is it more "accurate" to keep them?

Possibly, it is reasonable to keep all the measurements for all runs as a series, and decide on discarding/retention at the Analysis stage.

### Example of measurement data

First draft, just to visualize the scope of data collected

|program_id|sample_id|run_id|instruction_id|measure_all_time_ns|measure_one_time_ns|
|----------|---------|------|--------------|-------------------|-------------------|
|          |         | 34   |   58         |1234               |1204               |
|          |         | 34   |   59         |1231               |1200               |

- **program_id**
- **sample_id** - some form of identification of the entire sequence of runs
- **run_id** - sequence number of the repetition (to possibly discard warm-up runs etc.)
- **instruction_id** - sequence number of the instruction, necessary to correlate with OPCODE list
- **measure_all_time_ns** - if the measurement was a "measure all" - time it took to execute the instruction
- **measure_one_time_ns** - as above, if the measurement was a "measure one"

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

In order to explore the behavior of programs, measurements and environments, let's conduct a series of comparisons and analyzes.
List of tests:

1. Compare mean, variance, distribution for a single OPCODE with various forms of instrumentation enabled:
    - "measure all"
    - "measure one"
    - "measure pro-rated" or "measure inferred" only, so no instrumentation
2. Compare mean, variance, distribution for a single (simple) OPCODE, coming from different sample programs (or possibly from different `run_id` or `instruction_id`, i.e. how the OPCODE behaves in different circumstances in terms of the program it is a part of)
3. Compare mean, variance, distribution for various OPCODEs in the same manner, see if there's a pattern?
4. Analyze measurement overheads by comparing sums of individual instruction measurements with total measurements.
5. Assume a set of example gas cost estimators and compare their results, should they be applied. Compare with todays gas costs for OPCODEs
    - Use blockchain history results to compare various gas cost estimators with resources usage (see above).

**TODO** make these "compare" and "analyze" statements concrete.
