## OpenEthereum

### Notes on execution

1. only `let result = self.step(ext);` is included under the measurement. To capture most of "the EVM normally does when executing" we should also capture **TODO**:
    - `loop {`
    - the entire `match result {`
        
    Proposed solution similar to what [this PR for `evmone` suggests](https://github.com/imapp-pl/evmone/pull/2)
2. what is in `self.step(ext)` except for the expected normal operation?
    - `self.do_trace = self.do_trace && ext.trace_next_instruction(`, with a comment about overhead, but `&&` shortcircuits and I'm assuming `self.do_trace` is false, so this is minor. It also is what normally the node would go through
    - similar comment on the `evm_debug!`

    Nothing out of the ordinary there
