## REVM

### Installation and running

1. Rust and Cargo installation:

    ```curl https://sh.rustup.rs -sSf | sh```
   
2. Cloning repo
    ```
    cd src/instrumentation_measurement
    git clone -b evm_gas_cost_stage_3 git@github.com:imapp-pl/revm.git
    ```

3. Running

    From the `src/instrumentation_measurement/revm/bins/revm-test` directory:
    ```
    `echo "602060070260F053600160F0F3" | cargo bench --bench criterion_bytecode`
    ```   
