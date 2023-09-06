cd ../..
mkdir gas-cost-estimator-clients -p
cd gas-cost-estimator-clients

if [ ! -d "evmone" ]; then
    git clone --recurse-submodules https://github.com/imapp-pl/evmone
fi

if [ ! -d "go-ethereum" ]; then
    git clone https://github.com/imapp-pl/go-ethereum
fi

if [ ! -d "ethereumjs-monorepo" ]; then
    git clone -b evm_gas_cost_stage_3 https://github.com/imapp-pl/ethereumjs-monorepo.git
fi

if [ ! -d "erigon" ]; then
    git clone -b imapp_benchmark https://github.com/imapp-pl/erigon.git
fi

if [ ! -d "nethermind" ]; then
    git clone -b evm_gas_cost_stage_3 https://github.com/imapp-pl/nethermind
fi

if [ ! -d "revm" ]; then
    git clone -b evm_gas_cost_stage_3 https://github.com/imapp-pl/revm.git
fi

if [ ! -d "besu" ]; then
    git clone -b benchmarking https://github.com/imapp-pl/besu.git
fi
