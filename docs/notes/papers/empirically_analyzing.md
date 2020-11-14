## Empirically Analyzing Ethereum’s Gas Mechanism

Renlord Yang∗§, Toby Murray∗, Paul Rimba§, Udaya Parampalli∗

https://arxiv.org/pdf/1905.00553.pdf

### Thoughts

1. Good intro to cite the importance of accurate gas costs (node diversity)
2. Our work could pivot to focus on easy reproducibility and quick time to obtain results and using synthetic data, as opposed to historical data, which has its advantages.
3. All estimation work, including ours, balances between estimating intrinsic cost of computation and particular optimizations (or lack thereof) of particular node implementations
    - in other words: resolving gas cost discrepancies might be done by either updating gas cost of OPCODEs and by optimizing (or aligning optimizations between) node implementations
4. A synthetic approach (ours) is better versed to estimate gas cost under the assumption that transaction execution might be done concurrently on a single machine.

### Rough dump notes

1. predates Broken Metre, done independenly, similar conclusions
2. includes I/O and focuses on those costs
3. `aleth`-based same as Broken Metre
4. similar to our current approach, they trace every EVM instruction
5. approach to resource contention on the test machine: "We electedto  use  a  noisy  setup  for  Machine  B  as  it  is  representative  ofthe hardware choice used by a consumer user."
6. `BLOCKHASH` is the main offender, but it seems odd that it hasn't been optimized (maybe it has been in more popular node implementations?)
7. parallel transaction execution is mentioned in Related Work
