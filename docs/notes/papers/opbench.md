## OpBench: A CPU Performance Benchmark for Ethereum Smart Contract Operation Code

Amjad Aldweesh, Maher Alharby, Maryam Mehrnezhad, Aad van Moorsel

https://www.researchgate.net/publication/336007166_OpBench_A_CPU_Performance_Benchmark_for_Ethereum_Smart_Contract_Operation_Code

### Takeaways

1. The approach is similar to our current
2. We can expand and provide added value by:
    - doing OpenEthereum, ewasm
    - focus on gas schedule alignment and implementation discrepancies detection
    - providing a more standardized procedure to implement instrumentation, e.g. caveats and requirements for a standardized measurement, generic scripts to conduct analysis on other implementations/environments
    - running without the need for stack balancing and contract deployment, by executing in an artificial EVM setup
    - validating and combining with other kinds of measurements, by conducting a detailed statistical analysis of the data

### Notes

1. Optimize EVM execution by miners, by benchmarking different environments. "As  a  consequence,a  miner  would  want  to  choose  a  platform  that  optimizes  thereward for the used energy. The benchmark presented in thispaper, when carried out for different platforms, willhelp selectthe best platform."
2. But also allow to choose "fattest" contracts to execute. "Our opcode benchmark would assist in decidingwhich smartcontracts  to  execute"
3. Lastly - alignment of reward and cost
4. How it is measured? repeatedly single opcode: "In  particular,  since  indi-vidual  opcodes  take  very  little  time  to  execute,  OpBench1
executes opcodes repeatedly, taking care of stack managementchallenges  that  result  from  the  small  size  EVM stack".
    - measuring every opcode (?). "The computation time of each bytecode is recorded"
    - but execution takes place in a full contract deployed
    - "set a timer before and after the executionof each opcode on the EVM."
    - for `PyEVM` they use [timeit](https://docs.python.org/3/library/timeit.html), which:
        - turns off GC
        - runs setup
        - suggest to only use `min` on the timing vector, not mean/stddev
    - there is a claim, that benchmarking on a higher (not opcode, but entire contract) level is not sufficient, around citation [15]
        - followed citation [15] in [`performance_benchmarking.md`](./performance_benchmarking.md)
5. Program generation: "we  generate  the bytecode for a fully executable smart contract, which contains repeated bytecode instances of the opcode intended to be measured,  as  well  as  the  required PUSHs and POPs opcodes  to successfully manipulate the EVM stack. "
    - for selected opcodes they do different versions for different sizes of the data manipulated
    - for selected opcodes ("Formula-based", 6 of them) they craft custom approaches
    - Stack Management: for example for ADD, they do PUSH, PUSH, ADD, POP repeatedly
6. Advertises the approach to be portable to other implementations.
7. "to  the  best  of  ourknowledge,  there  is  no  prior  systematic  approach  suggestedfor performance benchmarking of Ethereum opcodes"
8. Paper seems to focus on miner rewards coming from the gas schedule, instead of network security, balanced execution or enabling execution on consumer hardware.
9. Paper claims that gas schedule from the yellow paper does not provide a basis for it, but the basis was there (maybe it was not cited in YP) - see the old spreadsheet
10. References to follow:
    - (done irrelevant) GASPER again, as in "Broken Metre"
