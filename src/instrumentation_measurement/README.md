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


### Preparing Go Etherum Benchmark
Compile benchmark program
```
cd geth_benchmark\tests\imapp_benchmark
go build
```

### Preparing Nethermind
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