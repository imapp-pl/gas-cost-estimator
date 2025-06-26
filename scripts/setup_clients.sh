working_path="$(dirname $(dirname $(dirname $(realpath $0))))/gas-cost-estimator-clients"
if [ $# -eq 1 ]; then
    working_path=$1
fi

echo "Installing clients to: $working_path"

# # if you want to  redo the setup, delete the gas-cost-estimator-clients directory
# # rm gas-cost-estimator-clients -rf
# # if you want to redo a specific client, only delete the corresponding directory

mkdir -p $working_path
mkdir -p $working_path/build


# EvmOne
if [ ! -d "$working_path/evmone" ]; then
    cd $working_path
    mkdir -p build/evmone
    git clone --recurse-submodules -b benchmark-bytecode-execution2 https://github.com/JacekGlen/evmone.git --depth 1
    cd evmone
    cmake -S . -B build -DEVMONE_TESTING=ON -DCMAKE_BUILD_TYPE:STRING=RelWithDebInfo
    cmake --build build --parallel --config RelWithDebInfo --target evmone-bench
    cp -f build/bin/evmone-bench ../build/evmone/
fi

# Go Ethereum
if [ ! -d "$working_path/go-ethereum" ]; then
    cd $working_path
    mkdir -p build/geth
    git clone https://github.com/ethereum/go-ethereum.git --depth 1
    cd go-ethereum
    go run build/ci.go install ./cmd/evm
    cp -f build/bin/evm ../build/geth/
fi

# Erigon
if [ ! -d "$working_path/erigon" ]; then
    cd $working_path
    mkdir -p build/erigon
    git clone -b release/2.60 https://github.com/erigontech/erigon.git --depth 1
    cd erigon
    make evm.cmd
    cp -f build/bin/evm ../build/erigon/
fi

# EthereumJS
if [ ! -d "$working_path/ethereumjs-monorepo" ]; then
    cd $working_path
    mkdir -p build/erigon
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/ethereumjs-monorepo.git --depth 1
    cd ethereumjs-monorepo
    npm i
    cd packages/vm
    npm run build:benchmarks
    ncc build benchmarks/run.js -o ../../../build/ethereumjs/
fi

# Nethermind
if [ ! -d "$working_path/nethermind" ]; then
    cd $working_path
    mkdir -p build/nethermind
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/nethermind.git --depth 1
    cd nethermind/src/Nethermind/
    dotnet build -c Release ./Benchmarks.slnx -o out/
    cp -fr out/* ../../../build/nethermind/
fi

# Revm
if [ ! -d "$working_path/revm" ]; then
    cd $working_path
    mkdir -p build/revm
    git clone -b main https://github.com/bluealloy/revm.git --depth 1
    cd revm
    cargo build -p revme --profile release
    cp -f target/release/revme ../build/revm/
fi

# Besu
if [ ! -d "$working_path/besu" ]; then
    cd $working_path
    mkdir -p build/besu
    git clone -b benchmark-bytecode-execution https://github.com/lukasz-glen/besu.git --depth 1
    cd besu
    ./gradlew :ethereum:evmTool:installDist
    cp -fr ethereum/evmtool/build/install/evmtool ../build/besu/
fi
