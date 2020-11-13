# Instrumentation and measurement using `go-ethereum` (`geth`)

### Rough notes


1. https://pkg.go.dev/github.com/ethereum/go-ethereum@v1.9.23/core/vm#EVMInterpreter - revisit this, but doesn't give an immediate answer on how to do what we want to do
2. https://pkg.go.dev/github.com/ethereum/go-ethereum@v1.9.23/core/vm/runtime#example-Execute - bingo
    - you can try: `go run geth/main.go` from here (having `go get`-ed `go-ethereum` into your `GOPATH`)
    - results make little sense at this point. Try `GOGC=off`, which even out slightly
    - usage: `go run main.go --bytecode 6020 --sampleSize 23`
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
