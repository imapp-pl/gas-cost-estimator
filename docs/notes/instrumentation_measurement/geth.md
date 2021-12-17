# Instrumentation and measurement using `go-ethereum` (`geth`)

### Simple instrumenter

A simple instrumenter (`instrumenter.go`) (to be further developed and research according to this doc) to be found [here](/src/interumentation_measurement/geth).

NOTE: `instrumenter.go` has been obsoleted and removed. We use instrumentation manually injected in `go-ethereum` interpreter loop code.

### Take aways

1. `Tracer` interface (and `StructLogger` being a template implementation) is a good instrumenter
    - shouldn't introduce much overhead on the per-instruction level of the interpreter loop
    - we should investigate the overhead of some operations before entering the interpreter loop happening after `CaptureStart` (see rough notes)
    - we should remember to implement or `Tracer` so that it's operation has smallest overhead (e.g. make sure it doesn't suddenly allocate stuff after N instructions, or produce other fluctuations). We should have steps in the Analysis toolbox that would detect such problems.
    - it should be relatively easy to write a `Tracer` implementation which does what we want
    - we're removing all storage and stack tracking. Storage is out of scope and stack we'll do with the vanilla `StructLogger` (if necessary); it requires access to `vm` package internals. Same with memory and return data tracing for consistency
2. New tasks (**TODO**):
    - tidy up `main.go` and `instrumenter.go` code, possibly draft some simple unit test before adding more functionality
    - properly fork and manage the `go-ethereum` dependency
    - investigate the overhead of some operations before entering the interpreter loop happening after `CaptureStart` (see rough notes). Remove these operations and compare measurements. If necessary, implement a fork of `go-ethereum` where the impact is minimized
    - ensure `Tracer` implementation has negligible and even overhead (e.g. make sure it doesn't suddenly allocate stuff after N instructions, or produce other fluctuations)
    - improve the timing used (`runtimeNano` is used already) according to  [`exploration_timers.Rmd`](/src/analysis/exploration_timers.Rmd)
    - (optional) implement an Analysis tool to detect problems with uneven overhead of instrumentation (e.g. every program has Nth instruction exceedingly costly, because our `Tracer` is doing something)
    - (for Stage II) implement a `Tracer` satisfying all the criteria
    - (for Stage II) ensure the `steps%1000` line (see rough notes below) doesn't affect us
3. `Tracer.CaptureState` layout in `interpreter.go` must be altered, because otherwise time measurements captured will be skewed (measure two neighboring instructions mixed)
4. Care must be taken with warm-up.
    - If you warm up with tracing off, weird effects happen - first traced execution of `SHA3` gets a huge result.
    - Warm-up still doesn't alleviate the effect of multiple occurrence of `SHA3` instruction in a single program - first one is always more costly.

### Notes on `time.Time` precision and monotonicity

1. `time.Since` is handled by monotonic time, as we use it, since go 1.9 [time.Time](https://golang.org/pkg/time/#Time), [discussion](https://github.com/golang/go/issues/12914#issuecomment-277335863), [monotonic clocks](https://golang.org/pkg/time/#hdr-Monotonic_Clocks)
2. from [here](https://stackoverflow.com/questions/14610459/how-precise-is-gos-time-really) we get:
    ```
    $ go run ./src/instrumentation_measurement/clock_resolution_go/main.go
    Monotonic clock resolution is 1 nanoseconds
    ```
3. I tested the overhead of that `clock_gettime` with `time.Since()` (and a trick one: `runtimeNano`):
   - overhead is 10 times smaller using `time.Since`, and even smaller using `runtimeNano`
   - investigate: sometimes both overheads are smaller, sometimes both are bigger, up to 3 fold.
       - it might be worthwhile to measure and record the overhead on every OpCode, in case the overhead suffers from such long-running fluctuations <- yes, we're going to do that
   - overhead of golang's timers analyzed in [`exploration_timers.Rmd`](/src/analysis/exploration_timers.Rmd)

#### Timer takeaways

- timers have periods of better behavior and worse behavior; we might want to filter out measurements from the "worse periods"
- `runtimeNano` seems to be the least overhead overall. Switching from `time.Now` to `runtimeNano` allowed us to measure a quickest opcode execution at 52ns, compared to 67ns with `time.Now`. It's enough to look at the code of [`time.Now`](https://golang.org/src/time/time.go) to see how much it does before capturing time.
- timers seem to require a lot of warm-up
- we will be monitoring the timers during opcode measurements, the noise introduced by that shouldn't be large
- more in [`exploration_timers.Rmd`](/src/analysis/exploration_timers.Rmd) or [quick preview of notebook results](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration_timers.nb.html)

### Notes on execution


What is being run except EVM excecution, as measured by `CaptureStart`/`End` (everything between `CaptureStart` and beginning of the interpreter main loop, in `master` branch `go-ethereum`):
- (source: `github.com/ethereum/go-ethereum/core/vm/evm.go:210`, `func (evm *EVM) Call`)
- check boolean `isPrecompile`
- get code from the in-memory StateDB
- `if len(code) == 0`
- `NewContract` and some assignments
- `contract.SetCallCode`
- some getting and setting of evm.interpreter magic in `run`
- minor checks and assignments at the beginning of `func (in *EVMInterpreter) Run`
- `mem`, `stack`, `returns`, (`callContext` too?) allocations
- if we want the first instruction to have a precise measurement (not necessary with current program generation), `CaptureStart` must be [moved](https://github.com/imapp-pl/go-ethereum/tree/wallclock)

What is going on between `CaptureState`s (every opcode):
- (normal interpreter operation, but "unfair") `if steps%1000 == 0 && atomic.LoadInt32(&in.evm.abort) != 0` (only if we go over 1000 instructions in programs)
- `logged, pcCopy, gasCopy = false, pc, contract.Gas` if tracing is on
- (normal interpreter operations):
    - `op = contract.GetOp(pc)`
    - `operation := in.cfg.JumpTable[op]`
    - `if sLen := stack.len(); sLen < operation.minStack`
    - `else if sLen > operation.maxStack`
    - `if in.readOnly && in.evm.chainRules.IsByzantium` (more checks if readOnly is true, **TODO**: make fair)
    - `if !contract.UseGas(operation.constantGas)` and the inside (static gas cost)
    - `if operation.memorySize != nil` and inside (memory pre-calculations)
    - `if operation.dynamicGas != nil` and inside (dynamic gas cost)
    - `if memorySize > 0` and inside (memory resizing)
    - `res, err = operation.execute(&pc, in, callContext)`
    - `if operation.returns` and inside (return value capturing)
    - `switch {` for final end condition
- (moved after `execute` in current fork) `in.cfg.Tracer.CaptureState(...)` tracing itself, just before `execute` of an opcode
- `logged = true` if tracing is on

### Execution environment

Please see Dockerfile.geth file to learn how to prepare the environment.


### Rough notes

1. https://pkg.go.dev/github.com/ethereum/go-ethereum@v1.9.23/core/vm#EVMInterpreter - revisit this, but doesn't give an immediate answer on how to do what we want to do
2. https://pkg.go.dev/github.com/ethereum/go-ethereum@v1.9.23/core/vm/runtime#example-Execute - bingo
    - this is used in `instrumenter.go` see there for usage
    - `GOGC=off` seems to necessary have some stability of measurements, together with forcing garbage collection on every sample. **TODO** consider measuring with normal garbage collection and its effects on measurements.
    - apparently this does many more things than we want to monitor, see next points
3. A better approach is to:
    - run via `runtime.Execute`
    - configure a `StructLogger` (or other `Tracer` implementation, see `github.com/ethereum/go-ethereum/core/vm/logger.go`)
    - how to configure that?
        - `EVMInterpreter.cfg.Tracer` holds this, `cfg` is `vm.Config`, see `github.com/ethereum/go-ethereum/core/vm/interpreter.go`
        - that is configurable via `vm.NewEVMInterpreter`
        - ...and via `vm.NewEVM`
        - ...and that in turn via `runtime.Config` under `EVMConfig`, hooray
        - remember to enable `vm.Config.Debug = true` - it looks like it won't impact anything else
4. Final `STOP` instruction - where does it come from:
    - most likely `github.com/ethereum/go-ethereum/core/vm/contract.go:163`
5. (**TODO**) we should, and are able to, measure the impact of calldata input, especially on calldata-specific OPCODEs.
    `runtime.Execute` allows us to do this via `input`: `func Execute(code, input []byte, cfg *Config)`
