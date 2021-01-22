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



**TODO** iterative
**TODO** copy a lot from strategy.md

## Appendix A: detailed task list

## Appendix B: OPCODEs subset

## References

[1] [https://etherscan.io/block/11660498](https://etherscan.io/block/11660498)
