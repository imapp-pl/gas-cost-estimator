## Broken Metre:Attacking Resource Metering in EVM

### Thoughts

1. We originally wanted to separate sample program generation from model, and have them communicate via some form of an "API".
    - But what if we want to generate programs dynamically, based on a result from the model (as Broken Metre does)?
2. The "references to follow" hold some interesting reading about gas-exploration tools

### Rough dump notes

1. mining contract history to detect outliers, gas cost vs resources (CPU & RAM)
2. low-throughput contracts, contracts that cost too little gas to execute
    1. throughput = gas/second
3. references to follow:
    1. and the gas cost has also been reviewedseveral times [11], [40] to increase the cost of the under-pricedinstructions.
    2. our problem resembles  other  program  synthesistasks [33
    3. Chen etal.  [18]  propose  a  mechanism  where  contracts  using  a  singleinstruction  in  excess  would  be  penalised.
        - aimed at opportunistically punishing the abusing contracts (which do an excessively expensive operation)
    4. IMPORTANT: Yang et al. [58] have recently empiricallyanalysed  the  resource  usage  and  gas  usage  of  the  EVM  in-structions. They provide an in-depth analysis of the time takenfor  each  instructions  both  on  commodity  and  professionalhardware.
    5. Gas  Usage  Optimisation:Gasper  [17]  is  one  of  the  firstpaper which has focused on finding gas related anti-patterns forsmart contracts
    6. MadMax  [32]  is  a  static  analysis  tool  to  find  gas-focusedvulnerabilities
    7. Gastap [5] is a static analysis tool which allows to computesound  upper  bounds  for  smart  contracts
4. programs  where  the  cache  influences  exe-cution time by an order of magnitude
    1. This is about page cachin for IO-intensive operations - out of our scope
5. hardware setup:
    1. We run all of the experiments on a Google CloudPlatform  (GCP)  [31]  instance  with  4  cores  (8  threads)  IntelXeon at 2.20GHz, 8 GB of RAM and an SSD with a 400MB/sthroughput.  The  machine  runs  Ubuntu  18.04  with  the  Linuxkernel version 4.15.0.
    2. (Parity bare metal for comparison) more powerful bare-metal  machine  with  4  cores  (8  threads)  at  2.7GHZ,  32GB  ofRAM  and  an  SSD  with  540MB/s  throughput
6. Garbage Collection - watch out for - they decided to use _aleth_
7. Our  measurement  framework  is  open-sourced2and
    1. TODO  https://github.com/danhper/aleth/tree/measure-gas
8. time and memory measurement:
    1. Weuse a nanosecond precision clock to measure time and measureboth the time taken to execute a single smart contract and thetime  to  execute  a  single  instruction.  To  measure  the  memoryusage of a single transaction, we override globally thenewanddeleteoperators and record all allocations and deallocationsperformed by the EVM execution within each transaction. Weensure that this is the only way used by the EVM to performmemory allocation.
    2. measure  memory,  we  computethe difference between the total amount of memory allocatedand  the  total  amount  of  memory  deallocated
    3. For CPU, we use  clock  time  measurements  as  a  proxy  for  the  CPU  usage.
    4. Finally,  for  storage  usage,  we  count  the  number  of  EVMwords (256 bits) of storage newly allocated per transactions.
        1. for storage usage comparison they used `iotop`
9. modelling:
    1. ~millions of data points
    2. Pearson score for correlation, gas vs resource
    3. multivariate correlation, gas vs principal components of resources
    4. capturing large variance is important
10. sample program generation:
    1. This made it easier: The task we solve is different becausewe need to define “valid” but not “meaningful” programs andoptimise for a well-defined metric: gas throughput
    2. caveat: Second, instructions should not try to access random parts ofthe  EVM  memory,  otherwise  the  program  could  run  out  ofgas
    3. they excluded loops and infinite loops
    4. managing items on the stack is important - never pop too much!
11. TODO: is CALLDATACOPY an IO operation? we have it in our list but this paper tells us it is IO
12. Section IV.D and iV.E skipped
13. "long-term fixes" and how do we fit in?
    1. dynamic pricing from Chen et al. - unsure about feasability
    2. importance of stateless clients explained, relates to L2 scaling:
        1. The  key  ideais  that  instead  of  forcing  clients  to  store  the  whole  state,entity emitting transactions must send the transaction, the dataneeded by the transactions, and a proof that this data is correct
