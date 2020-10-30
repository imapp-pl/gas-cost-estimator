Broken Metre:Attacking Resource Metering in EVM

1. mining contract history to detect outliers, gas cost vs resources (CPU & RAM)
2. low-throughput contracts, contracts that cost too little gas to execute
    1. throughput = gas/second
3. references to follow:
    1. and the gas cost has also been reviewedseveral times [11], [40] to increase the cost of the under-pricedinstructions.
4. programs  where  the  cache  influences  exe-cution time by an order of magnitude
    1. TODO
5. hardware setup:
    1. We run all of the experiments on a Google CloudPlatform  (GCP)  [31]  instance  with  4  cores  (8  threads)  IntelXeon at 2.20GHz, 8 GB of RAM and an SSD with a 400MB/sthroughput.  The  machine  runs  Ubuntu  18.04  with  the  Linuxkernel version 4.15.0.
6. Garbage Collection - watch out for - they decided to use _aleth_
7. Our  measurement  framework  is  open-sourced2and
    1. TODO  https://github.com/danhper/aleth/tree/measure-gas
8. time and memory measurement:
    1. Weuse a nanosecond precision clock to measure time and measureboth the time taken to execute a single smart contract and thetime  to  execute  a  single  instruction.  To  measure  the  memoryusage of a single transaction, we override globally thenewanddeleteoperators and record all allocations and deallocationsperformed by the EVM execution within each transaction. Weensure that this is the only way used by the EVM to performmemory allocation.
    2. measure  memory,  we  computethe difference between the total amount of memory allocatedand  the  total  amount  of  memory  deallocated
    3. For CPU, we use  clock  time  measurements  as  a  proxy  for  the  CPU  usage.
    4. Finally,  for  storage  usage,  we  count  the  number  of  EVMwords (256 bits) of storage newly allocated per transactions.
9. modelling:
    1. ~millions of data points
    2. Pearson score for correlation, gas vs resource
    3. multivariate correlation, gas vs principal components of resources
    4. capturing large variance is important
