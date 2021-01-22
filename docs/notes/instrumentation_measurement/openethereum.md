## Openethereum


### Installation and running

1. To build, run in the `evmbin` directory of openethereum repository (submodule), at branch `wallclock` 
    ```
    cargo build --release
    ```
    this should produce `openethereum-evm` binary in openethereum's `target/release/` directory.
    
2. Running
    
    ```
    ./target/release/openethereum-evm --code <bytecode> [--repeat <number of repetitions>] [--print-opcodes] [--measure-overhead]
    ```
    
    for example:
    ```
    ./target/release/openethereum-evm --code 602060070260F053600160F0F3 --repeat 2
    ```
    If `--measure-overhead` is passed, bytecode will not be executed. If `--print-opcodes` is passed, only one repetition will be executed (no matter what `--repeat` value is).   

    
