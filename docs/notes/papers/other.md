## Other resources which might be useful

1. Ethereum yellow paper - worth a quick scan, holds an (up-to-date?) list of opcodes in EVM with descriptions and details
2. https://ethereum.org/en/developers/docs/evm/ - just basics to ramp up with
3. https://www.ethervm.io/ - reference for EVM opcodes + Decompiler
4. https://medium.com/swlh/getting-deep-into-evm-how-ethereum-works-backstage-ab6ad9c0d0bf - nice intro for a broader perspective how EVM works
5. https://docs.google.com/spreadsheets/d/1m89CVujrQe5LAFJ8-YAUCcNK950dUzMQPMJBxRtGCqs/edit#gid=0 - "1.0 gas costs" spreadsheet - ilustrates the original calculations to get gas costs. Seems to work like this:
    - calculate how much effort can a single block be (e.g. take x time max, leave y memory footprint, take z storage for block history etc.) - see cells L5-L10. Call this _block effort_limit_
    - set an arbitrary _block gas limit_
    - express the cost of a unit this effort (e.g. a microsecond of computation) in gas using the block gas limit and block effort limit
    - measure footprint of each opcode (how?) in these dimensions - see columns B-G
    - express this footprint in gas - see column H
6. https://github.com/wolflo/evm-opcodes - source for `www.ethervm.io`, but with a nice compilation of gas cost formulas from the yellow paper. Not exactly sure about up-to-dateness, e.g. it mentions 700 for STATICCALL, while other sources 40 (after EIP-2046)
7. https://dave.cheney.net/high-performance-go-workshop/dotgo-paris.html - some materials on go profiling and benchmarks. Not immediately useful but:
    - tips on profiling with garbage collector
    - compiler optimization traps
    - avoiding appending (**TODO** ensure we don't)


## Other resources scanned, which aren't relevant to us

1. http://bergel.eu/MyPapers/Soto20a-FuzzingSolidity.pdf - "Fuzzing to Estimate Gas Costs of Ethereum Contracts" - irrelevant; is about comparing Solidity static gas cost estimation and estimation using fuzzing testing.
1. The `evmjit` story (which I stumbled upon [here](https://ethresear.ch/t/evm-performance/2791))- the idea seemed to be to replace patterns of operations with "bulk" operations, e.g. a bunch of static PUSH instructions before a `CALL` to become a single meta-instruction. _It would be of great significance_ to our results, but seems to be discontinued (in `geth` codebase there's no occurrences, similar for `OpenEthereum`, [this is not active](https://github.com/ethereum/evmjit) and then [this](https://github.com/ethereum/go-ethereum/issues/2365#issuecomment-275493369)).
1. ethresear.ch - search for `evm cpu`, `evm gas`, check tags: https://ethresear.ch/c/evm-ewasm/26, https://ethereum-magicians.org/tag/evm, https://ethereum-magicians.org/tag/evm-evolution, https://ethereum-magicians.org/tag/opcodes
    - nothing relevant in here:
        - https://ethresear.ch/t/running-deep-learning-on-evm/899
        - https://ethresear.ch/t/evm-performance/2791/18 (but interesting read about EVM vs ewasm in general
        - https://ethresear.ch/t/dynamic-gas-costs/4375/4 (dynamic opcode pricing via consensus)
        - https://ethresear.ch/t/verifiable-precompiled-contracts/7242
        - https://ethresear.ch/t/evm-idea-add-access-to-overflow-carry-sign-and-zero-flags-to-reduce-gas-use/782/5
        - https://ethresear.ch/t/eth2-authenticated-data-structures-and-gas-costs/6487
        - https://ethresear.ch/t/client-side-solidity-evm/4605/5
        - https://github.com/pirapira/awesome-ethereum-virtual-machine - great list of resources, but nothing immediately useful. Revisit
        - https://ethereum-magicians.org/t/eip-1109-remove-call-costs-for-precompiled-contracts/447/14
        - https://ethereum-magicians.org/t/eip-1884-repricing-for-trie-size-dependent-opcodes/3024/38
1. https://www.codeproject.com/Articles/8672/Virtual-Machine-Opcode-Resolution-Performance-Test - "Virtual Machine Opcode Resolution, Performance Tests"
1. http://mural.maynoothuniversity.ie/6432/1/JP-Relating-Static.pdf - "Relating Staticand Dynamic Measurements for the Java Virtual Machine Instruction Set"
1. https://www.researchgate.net/publication/3929823_Measurement_and_Analysis_of_Runtime_Profiling_Data_for_Java_Programs - "Measurement and Analysis of Runtime Profiling Data for Java Programs"
1. https://stackoverflow.com/questions/37740081/bytecode-instruction-cost - "Bytecode instruction cost" - SO thread for Python, nothing useful
## search queries
1. ftp://ftp.cs.wisc.edu/paradyn/technical_papers/paradynJ.pdf - "Performance Measurement of Dynamically Compiled Java Executions"

"virtual machine instruction measurement" and variations using: "java" / "clr cil" / "comparison" / "benchmark",

measure bytecode instructions performance -"platform independent timing of java"

time vs instruction count correlation
