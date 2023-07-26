## EthereumJS

### Installation and running

1. Building
    ```
    cd src/instrumentation_measurement
    git clone -b evm_gas_cost_stage_3 git@github.com:imapp-pl/ethereumjs-monorepo.git
    cd ethereumjs-monorepo
    npm i
    npm run build --workspaces
    cd packages/evm/
    npm run build:benchmarks
    chmod a+x ./benchmarks/benchmarkOpcodes.js
    ```
   
2. Running

    From the `src/instrumentation_measurement/ethereumjs-monorepo/packages/evm` package directory:
    ```
    node -max-old-space-size=4000 ./benchmarks/benchmarkOpcodes.js --sampleSize=2 602060070260F053600160F0F3
    ```   
    From the `src` directory:
    ```
    node -max-old-space-size=4000 ./instrumentation_measurement/ethereumjs-monorepo/packages/evm/benchmarks/benchmarkOpcodes.js --sampleSize=2 602060070260F053600160F0F3
    ```
