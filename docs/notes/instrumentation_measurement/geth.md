# Instrumentation and measurement using `go-ethereum` (`geth`)

### Simple instrumenter

A simple instrumenter (`instrumenter.go`) (to be further developed and research according to this doc) to be found [here](/src/interumentation_measurement/geth).

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
    - implement standardized output from instrumentation (as per [strategy.md](/docs/strategy.md))
    - investigate the overhead of some operations before entering the interpreter loop happening after `CaptureStart` (see rough notes). Remove these operations and compare measurements. If necessary, implement a fork of `go-ethereum` where the impact is minimized
    - ensure `Tracer` implementation has negligible and even overhead (e.g. make sure it doesn't suddenly allocate stuff after N instructions, or produce other fluctuations)
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
3. I tested the overhead of that `clock_gettime` with `time.Since()` (and a trick `runtimeNano`):
   - overhead is 10 times smaller using `time.Since`
   - investigate: sometimes both overheads are smaller, sometimes both are bigger, up to 3 fold. (rerun the `main.go`)
       - it might be worthwhile to measure and record the overhead on every OpCode, in case the overhead suffers from such long-running fluctuations <- yes, we're going to do that
   - overhead of golang's timers analyzed in [`exploration_timers.Rmd`](/src/analysis/exploration_timers.Rmd)



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
    - what is being run except EVM excecution, as measured by `CaptureStart`/`End`:
        - (source: `github.com/ethereum/go-ethereum/core/vm/evm.go:210`, `func (evm *EVM) Call`)
        - get code from the in-memory StateDB
        - NewContract
        - SetCallCode
        - some getting and setting of evm.interpreter magic in `run`
        - **TODO** consider moving the `CaptureStart` to a later stage for a tighter measurement
    - what is going on between `CaptureState` (every opcode)
        - `if steps%1000 == 0 && atomic.LoadInt32(&in.evm.abort) != 0` probably negligible check, unlikely we'll go above 1000 instructions, but sth to keep in mind
        - `logged, pcCopy, gasCopy = false, pc, contract.Gas` if tracing is on
        - `in.cfg.Tracer.CaptureState(...)` tracing itself, just before `execute` of an opcode
        - `logged = true` if tracing is on
