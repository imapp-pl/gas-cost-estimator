cd ../../gas-cost-estimator-clients

# build Nethermind
cd nethermind/src/Nethermind/Nethermind.Benchmark.Runner
dotnet build -c Release -o ../../../../build/nethermind
cd ../../../..

# build Erigon
cd erigon/tests/imapp_benchmark
go build -o ../../../build/erigon/ .
cd ../../../