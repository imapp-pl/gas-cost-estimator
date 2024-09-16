cd ../../..

# if you want to  redo the setup, remove the gas-cost-estimator-clients directory
# rm gas-cost-estimator-clients -rf
# if you want to redo a specific client, only remove the corresponding directory

mkdir gas-cost-estimator-clients -p
cd gas-cost-estimator-clients

# EvmOne
if [ ! -d "evmone" ]; then
    git clone --recurse-submodules https://github.com/imapp-pl/evmone --depth 1
fi

# Go Ethereum
if [ ! -d "go-ethereum" ]; then
    mkdir -p build/geth
    git clone https://github.com/ethereum/go-ethereum.git --depth 1
    cd go-ethereum
    go run build/ci.go install ./cmd/evm
    cp -f build/bin/evm ../build/geth/
    cd ..
fi

# Erigon
if [ ! -d "erigon" ]; then
    mkdir -p build/erigon
    git clone -b release/2.60 https://github.com/erigontech/erigon.git --depth 1
    cd erigon
    make evm.cmd
    cp -f build/bin/evm ../build/erigon/
    cd ..
fi

# EthereumJS
if [ ! -d "ethereumjs-monorepo" ]; then
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/ethereumjs-monorepo.git --depth 1
    cd ethereumjs-monorepo
    npm i
    cd packages/vm
    npm run build:benchmarks
    cd ../../..
fi

if [ ! -d "nethermind" ]; then
    mkdir -p build/nethermind
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/nethermind.git --depth 1
    cd nethermind/src/Nethermind/
    /usr/bin/dotnet build -c Release ./Benchmarks.sln -o out/
    cp -f out/* ../../../build/nethermind/
    cd ../../../
fi

if [ ! -d "revm" ]; then
    mkdir -p build/revm
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/revm.git --depth 1
    cd revm
    cargo build -p revme --profile release
    cp -f target/release/revme ../build/revm/
    cd ..
fi

if [ ! -d "besu" ]; then
    git clone -b benchmarking https://github.com/imapp-pl/besu.git --depth 1
fi
