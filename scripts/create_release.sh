#!/bin/bash

if [ $# -eq 1 ]; then
    working_path=$1
fi

# Set working path and version
version=0.1.0
working_path="$(dirname $(dirname $(dirname $(realpath $0))))/gas-cost-estimator-clients"
while getopts "v:p:" option; do
    case $option in
    v)
        version=$OPTARG
        ;;
    p)
        working_path=$OPTARG
        ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done
mkdir -p $working_path
mkdir -p $working_path/build
mkdir -p $working_path/release

echo "Creating Gas Cost Estimator Version: $version"
echo "Installing clients to: $working_path"

# Install required libraries for cross-compilation
sudo apt-get install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
sudo apt-get install mingw-w64

# # EvmOne
cd $working_path
if [ ! -d "$working_path/evmone" ]; then
    cd $working_path
    mkdir -p build/evmone
    git clone --recurse-submodules -b benchmark-bytecode-execution2 https://github.com/JacekGlen/evmone.git --depth 1
fi

cd evmone

cmake -S . -B build -DEVMONE_TESTING=ON -DCMAKE_BUILD_TYPE:STRING=RelWithDebInfo
cmake --build build --parallel --config RelWithDebInfo --target evmone-bench
mkdir -p $working_path/build/linux-amd64/evmone
cp -f build/bin/evmone-bench $working_path/build/linux-amd64/evmone/

cat <<EOL > linux-arm64-toolchain.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)
EOL
cmake -S . -B build-arm64 -DEVMONE_TESTING=ON -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_TOOLCHAIN_FILE=linux-arm64-toolchain.cmake
cmake --build build-arm64 --parallel --config RelWithDebInfo --target evmone-bench
mkdir -p $working_path/build/linux-arm64/evmone
cp -f build-arm64/bin/evmone-bench $working_path/build/linux-arm64/evmone/

# # Go Ethereum
cd $working_path
geth_tag_name=$(curl -s https://api.github.com/repos/ethereum/go-ethereum/releases/latest | jq -r .tag_name)
geth_commit=$(curl -s https://api.github.com/repos/ethereum/go-ethereum/git/refs/tags/$geth_tag_name | jq -r .object.sha | cut -c 1-8)
echo "Downloading Go Ethereum $geth_tag_name for commit $geth_commit"
geth_version=${geth_tag_name:1} # skip leading 'v' in tag name

curl -O "https://gethstore.blob.core.windows.net/builds/geth-alltools-linux-amd64-$geth_version-$geth_commit.tar.gz"
mkdir -p build/linux-amd64/geth
tar -xzf geth-alltools-linux-amd64-$geth_version-$geth_commit.tar.gz -C build/linux-amd64/geth --wildcards '*/evm' --strip-components=1

curl -O "https://gethstore.blob.core.windows.net/builds/geth-alltools-linux-arm64-$geth_version-$geth_commit.tar.gz"
mkdir -p build/linux-arm64/geth
tar -xzf geth-alltools-linux-arm64-$geth_version-$geth_commit.tar.gz -C build/linux-arm64/geth --wildcards '*/evm' --strip-components=1

curl -O "https://gethstore.blob.core.windows.net/builds/geth-alltools-darwin-amd64-$geth_version-$geth_commit.tar.gz"
mkdir -p build/darwin-amd64/geth
tar -xzf geth-alltools-darwin-amd64-$geth_version-$geth_commit.tar.gz -C build/darwin-amd64/geth --wildcards '*/evm' --strip-components=1

curl -O "https://gethstore.blob.core.windows.net/builds/geth-alltools-darwin-arm64-$geth_version-$geth_commit.tar.gz"
mkdir -p build/darwin-arm64/geth
tar -xzf geth-alltools-darwin-arm64-$geth_version-$geth_commit.tar.gz -C build/darwin-arm64/geth --wildcards '*/evm' --strip-components=1

curl -O "https://gethstore.blob.core.windows.net/builds/geth-alltools-windows-amd64-$geth_version-$geth_commit.zip"
mkdir -p build/windows-amd64/geth
unzip -q geth-alltools-windows-amd64-$geth_version-$geth_commit.zip
cp geth-alltools-windows-amd64-$geth_version-$geth_commit/evm.exe build/windows-amd64/geth/evm.exe

rm geth-alltools-*-$geth_version-$geth_commit.* -rf

# # Erigon
cd $working_path
erigon_tag_name=$(curl -s https://api.github.com/repos/erigontech/erigon/releases/latest | jq -r .tag_name)
echo "Downloading Erigon $erigon_tag_name"

mkdir -p build/linux-amd64/erigon
erigon_download_url="https://github.com/erigontech/erigon/releases/download/$erigon_tag_name/erigon_${erigon_tag_name}_linux_amd64v2.tar.gz"
curl -O "$erigon_download_url"  -L
tar -xzf erigon_${erigon_tag_name}_linux_amd64v2.tar.gz -C build/linux-amd64/erigon --wildcards '*/evm' --strip-components=1
tar -xzf erigon_${erigon_tag_name}_linux_amd64v2.tar.gz -C build/linux-amd64/erigon --wildcards '*/libsilkworm_capi.so' --strip-components=1

mkdir -p build/linux-arm64/erigon
erigon_download_url="https://github.com/erigontech/erigon/releases/download/$erigon_tag_name/erigon_${erigon_tag_name}_linux_arm64.tar.gz"
curl -O "$erigon_download_url"  -L
tar -xzf erigon_${erigon_tag_name}_linux_arm64.tar.gz -C build/linux-arm64/erigon --wildcards '*/evm' --strip-components=1

# EthereumJS
cd $working_path
if [ ! -d "$working_path/ethereumjs-monorepo" ]; then
    cd $working_path
    mkdir -p build/erigon
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/ethereumjs-monorepo.git --depth 1
fi
cd ethereumjs-monorepo
npm i
cd packages/vm
npm run build:benchmarks
ncc build benchmarks/run.js -o ../../../build/ethereumjs/

cd $working_path/build
mkdir -p linux-amd64/ethereumjs
cp -r ethereumjs/* linux-amd64/ethereumjs/
mkdir -p linux-arm64/ethereumjs
cp -r ethereumjs/* linux-arm64/ethereumjs/
mkdir -p darwin-amd64/ethereumjs
cp -r ethereumjs/* darwin-amd64/ethereumjs/
mkdir -p darwin-arm64/ethereumjs
cp -r ethereumjs/* darwin-arm64/ethereumjs/
mkdir -p windows-amd64/ethereumjs
cp -r ethereumjs/* windows-amd64/ethereumjs/

# Nethermind
cd $working_path
if [ ! -d "$working_path/nethermind" ]; then
    cd $working_path
    mkdir -p build/nethermind
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/nethermind.git --depth 1
fi

cd nethermind/src/Nethermind/Nethermind.Benchmark.Runner
dotnet publish Nethermind.Benchmark.Runner.csproj -c Release -r linux-x64 -o $working_path/build/linux-amd64/nethermind/
dotnet publish Nethermind.Benchmark.Runner.csproj -c Release -r linux-arm64 -o $working_path/build/linux-arm64/nethermind/
dotnet publish Nethermind.Benchmark.Runner.csproj -c Release -r osx-x64 -o $working_path/build/darwin-amd64/nethermind/
dotnet publish Nethermind.Benchmark.Runner.csproj -c Release -r osx-arm64 -o $working_path/build/darwin-arm64/nethermind/
dotnet publish Nethermind.Benchmark.Runner.csproj -c Release -r win-x64 -o $working_path/build/windows-amd64/nethermind/

# Revm
cd $working_path
if [ ! -d "$working_path/revm" ]; then
    cd $working_path
    mkdir -p build/revm
    git clone -b benchmark-bytecode-execution https://github.com/imapp-pl/revm.git --depth 1
fi
cd revm
# linux-amd64
mkdir -p $working_path/build/linux-amd64/revm
cargo build -p revme --profile release
cp -f target/release/revme $working_path/build/linux-amd64/revm/

# linux-arm64
rustup target add aarch64-unknown-linux-gnu
mkdir -p $working_path/build/linux-arm64/revm
RUSTFLAGS="-C linker=aarch64-linux-gnu-gcc" cargo build -p revme --profile release --target aarch64-unknown-linux-gnu
cp -f target/aarch64-unknown-linux-gnu/release/revme $working_path/build/linux-arm64/revm/

# windows-amd64
rustup target add x86_64-pc-windows-gnu
mkdir -p $working_path/build/windows-amd64/revm
RUSTFLAGS="-C linker=x86_64-w64-mingw32-gcc" cargo build -p revme --profile release --target x86_64-pc-windows-gnu
cp -f target/x86_64-pc-windows-gnu/release/revme.exe $working_path/build/windows-amd64/revm/

# Besu
cd $working_path
if [ ! -d "$working_path/besu" ]; then
    cd $working_path
    mkdir -p build/besu
    git clone -b evmtoolAddSamplesOption https://github.com/lukasz-glen/besu.git --depth 1
fi

cd besu
./gradlew :ethereum:evmTool:installDist
mkdir -p $working_path/build/linux-amd64/besu
cp -fr ethereum/evmtool/build/install/evmtool $working_path/build/linux-amd64/besu/
mkdir -p $working_path/build/linux-arm64/besu
cp -fr ethereum/evmtool/build/install/evmtool $working_path/build/linux-arm64/besu/
mkdir -p $working_path/build/darwin-amd64/besu
cp -fr ethereum/evmtool/build/install/evmtool $working_path/build/darwin-amd64/besu/
mkdir -p $working_path/build/darwin-arm64/besu
cp -fr ethereum/evmtool/build/install/evmtool $working_path/build/darwin-arm64/besu/
mkdir -p $working_path/build/windows-amd64/besu
cp -fr ethereum/evmtool/build/install/evmtool $working_path/build/windows-amd64/besu/

# Create release
archs=(linux-amd64 linux-arm64 darwin-amd64 darwin-arm64 windows-amd64)
scripts_path="$(dirname $(realpath $0))"
mkdir $working_path/release-dist
for arch in ${archs[@]}; do
    release_path=$working_path/release/gas-cost-estimator_v${version}_${arch}
    mkdir -p $release_path/gas-cost-estimator-clients/build
    cp -r $working_path/build/$arch/* $release_path/gas-cost-estimator-clients/build/
    cp -r $scripts_path/measure_* $release_path/
    rsync -ap --exclude='.*' --exclude='stage3' --exclude='docs/' $(dirname $scripts_path) $release_path/

    cd $release_path
    if [ $arch == "windows-amd64" ]; then
        zip -rq ../../release-dist/gas-cost-estimator_v${version}_${arch}.zip .
    else
        tar -czf ../../release-dist/gas-cost-estimator_v${version}_${arch}.tar.gz .
    fi
done