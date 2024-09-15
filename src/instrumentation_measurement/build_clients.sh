cd ../../../gas-cost-estimator-clients

# build Nethermind
# cd nethermind/src/Nethermind/Nethermind.Benchmark.Runner
# dotnet build -c Release -o ../../../../build/nethermind
# cd ../../../..

# build Erigon
cd erigon
make evm.cmd
mkdir -p ../build/erigon
cp build/bin/evm ../build/erigon/
cd ..

# build geth
cd go-ethereum
go run build/ci.go install ./cmd/evm
mkdir -p ../build/geth
cp build/bin/evm ../build/geth/
cd ..
