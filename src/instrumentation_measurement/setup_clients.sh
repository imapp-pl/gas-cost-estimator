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
    git clone https://github.com/ethereum/go-ethereum.git --depth 1
    cd go-ethereum
    go run build/ci.go install ./cmd/evm
    mkdir -p ../build/geth
    cp -f build/bin/evm ../build/geth/
    cd ..
fi

# Erigon
if [ ! -d "erigon" ]; then
    git clone -b release/2.60 https://github.com/erigontech/erigon.git --depth 1
    cd erigon
    make evm.cmd
    mkdir -p ../build/erigon
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
    git clone -b evm_gas_cost_stage_3 https://github.com/imapp-pl/nethermind --depth 1
fi

if [ ! -d "revm" ]; then
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/revm.git --depth 1
    cd revm
    cargo build -p revme --profile release
    mkdir -p ../build/revm
    cp -f target/release/revme ../build/revm/
    cd ..
fi

if [ ! -d "besu" ]; then
    git clone -b benchmarking https://github.com/imapp-pl/besu.git --depth 1
fi
