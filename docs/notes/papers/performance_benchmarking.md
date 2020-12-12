## Performance Benchmarking of Smart Contracts to Assess Miner Incentives in Ethereum

Amjad Aldweesh, Maher Alharby, Ellis Solaiman, Aad van Moorsel

https://www.researchgate.net/publication/328908738_Performance_Benchmarking_of_Smart_Contracts_to_Assess_Miner_Incentives_in_Ethereum

Paper focuses on finding real contracts with highest overall Gas/CPU ratio.

### Notes

1. Motivation to cite: " More-over, if certain smart contracts are known not to be attractive,transactions  using  that  smart  contract  would  not  be  executedby  miners" - alignment of gas costs impacts dependability of miner work
2. Intention similar to `gas-cost-estimator`: "We envisage that such abenchmark could be run periodically, on a variety of softwareand  hardware  platforms,  to  demonstrate  to  the  community  ifand how well costs and benefits are aligned within Ethereum"
3. Not sure why contract creation is investigted in the context of CPU time. It isn't surprising, that CPU/gas is 6x compared to execution
4. Environment: PyEthApp on a MacBook
5. It can be argued, that it would be hard to "prefer" high-yielding contracts at the expense of low-throughput contracts, b/c it's hard to predict accurately, which contracts are called by a tx.
