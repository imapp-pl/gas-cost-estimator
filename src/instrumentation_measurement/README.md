# Running with program generator
From `instrumentation_measurement` directory:

```
python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --mode all --sampleSize=50 --nSamples=3 > ../../geth.csv
```
    
By default programs are executed in geth. To change EVM specify `--evm` parameter:

```
python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --mode all --sampleSize=50 --nSamples=3 --evm evmone > ../../evmone.csv
```

### Running measurements via `docker`

From the repo root.

Build (pick tag name as desired):
```
sudo docker build -t measurements-geth -f Dockerfile.geth .
```

Run:
```
sudo docker run --rm --privileged --security-opt seccomp:unconfined \
  -it measurements-geth \
  sh -c "cd src && python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --mode all --sampleSize=5 --nSamples=1"
```

For other EVMs use respective `Dockerfile`s and use the `--evm` flag on the `measure` command, e.g. `measure --evm openethereum`


# Test environment setup
## Go Etherum Benchmark
Compile benchmark program
```
cd geth_benchmark\tests\imapp_benchmark
go build
```
## Nethermind
Requirements:
- .Net Core 6.0

Make sure that all submodules are fetched:
```
cd nethermind_benchmark
git submodule update --recursive --remote --init
```

Compile benchmark program:
```
cd nethermind_benchmark\src
dotnet build -c Release .\Benchmarks.sln
```

# Benchmark methodology

## Tools
The goal of benchmarking mode is to use well known libraries that track performance in reliable and precise manner. They tend to produce reproducible results and help to avoid common pitfalls while measuring execution time. In our approach we use the following tools:
- Go Ethereum: [Go Testing](https://pkg.go.dev/testing#Benchmark) package
- Nethermind: [DotNetBenchmark](https://benchmarkdotnet.org/articles/overview.html)

These tools were selected as industry standards for respective languages. They all minimize influence and variability of: caching, warmups, memory allocation, garbage collection, process management, external programs impact and clock measurements.

## Results explanation
For each bytecode, benchmark is executed twice. The first time bytecode is prefixed with opcode 00 (STOP). This causes the program to terminate immediately on the first loop. The second time bytecode is executed as normal. This method is to assess the engine overhead for each program execution. Please see below for the description of what consists of overhead for each engine.
The benchmark results contain:
- iterations_count: How many times the benchmark library executed the program internally
- engine_overhead_time_ns: Estimated time of engine overhead
- execution_loop_time_ns: The actual loop over opcodes in the bytecode
- total_time_ns: The two values above summed up
- mem_allocs_count: Number of memory operations
- mem_allocs_bytes: Total bytes allocated

## Go Ethereum execution overhead analysis
The certain 'preparation' steps are executed with every bytecode. They are performed no matter how long or complicated the bytecode is. This tend to be constant, so the longer program takes, the more negligible it becomes.

Prepare environment and sender account (~7%)
```go
var (
	address = common.BytesToAddress([]byte("contract"))
	vmenv   = NewEnv(cfg)
	sender  = vm.AccountRef(cfg.Origin)
)
```

Get rule set London, Berlin, etc (~43%) (Note: this seems an obvious candidate for caching. Further analysis has to take place.)
```go
rules := cfg.ChainConfig.Rules(vmenv.Context.BlockNumber, vmenv.Context.Random != nil)
```

Create a state object. If a state object with the address already exists the balance is carried over to the new account (~16%)
```go
cfg.State.CreateAccount(address)
```

Set the execution code (~23%)
```
cfg.State.SetCode(address, code)
```

Take snapshot (~9%)
```go
snapshot := evm.StateDB.Snapshot()
```

## Nethermind execution overhead analysis
(Estimated times to follow)


Get rule set London, Berlin, etc
```csharp
_specProvider.GetSpec(state.Env.TxExecutionContext.Header.Number)
```

Initiate stack
```
vmState.InitStacks();
```

Take snapshot
```
_worldState.TakeSnapshot()
```