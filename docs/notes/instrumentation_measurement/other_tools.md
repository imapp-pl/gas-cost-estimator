Notes on other tools for instrumentation & measurement

### Takeaways

Nothing relevant/useful yet

### Rough notes

1. http://wingtecher.com/themes/WingTecherResearch/assets/papers/saner-evm.pdf - "
EVM*: From Offline Detection to OnlineReinforcement for Ethereum Virtual Machine"
    - Not relevant to us, instrumentation for aborting of dangerous txs in the EVM. Not this kind of instrumentation we need.
2. https://www.researchgate.net/publication/331789943_Analysis_of_Ethereum_Smart_Contracts_and_Opcodes - "Analysis of Ethereum Smart Contracts and Opcodes"
    - Not relevant to us, just analysis of frequency of opcodes in the verified contracts (static)
3. https://ethereum.stackexchange.com/questions/4446/instrumenting-evm - "Instrumenting EVM"
    - _Maybe useful_ - "To do this, you need to define a VM log collector, which implements StructLogCollector. This function gets called on every step of the VM, and is provided with copies of the memory, stack, and modified parts of the storage, along with the program counter, current opcode...", this is for `go-ethereum`.
    - follow the Nick Johnsons link to etherquery
    - (done) revisit if `go-ethereum` specific measuring needs to be done using this
4. https://publik.tuwien.ac.at/files/publik_278277.pdf - "A Survey of Tools forAnalyzing Ethereum Smart Contracts" - mentions one tool for EVM instrumentation: ContractLarva
    - https://www.researchgate.net/publication/327834131_Monitoring_Smart_Contracts_ContractLarva_and_Open_Challenges_Beyond - ContractLarva
        - not relevant to us, Solidity level
