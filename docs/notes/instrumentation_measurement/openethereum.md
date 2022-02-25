## Openethereum


### Installation and running

1. To build, run in the `bin/evmbin` directory of openethereum repository (submodule), at branch `wallclock` 
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


### Notes on execution

1. only `let result = self.step(ext);` is included under the measurement. To capture most of "the EVM normally does when executing" we should also capture **TODO**:
    - `loop {`
    - the entire `match result {`
        
    Proposed solution similar to what [this PR for `evmone` suggests](https://github.com/imapp-pl/evmone/pull/2)
2. what is in `self.step(ext)` except for the expected normal operation?
    - `self.do_trace = self.do_trace && ext.trace_next_instruction(`, with a comment about overhead, but `&&` shortcircuits and I'm assuming `self.do_trace` is false, so this is minor. It also is what normally the node would go through
    - similar comment on the `evm_debug!`

    Nothing out of the ordinary there
