# Instrumentation and measurement using `go-ethereum` (`geth`)

### Rough notes


1. https://pkg.go.dev/github.com/ethereum/go-ethereum@v1.9.23/core/vm#EVMInterpreter - revisit this, but doesn't give an immediate answer on how to do what we want to do
2. https://pkg.go.dev/github.com/ethereum/go-ethereum@v1.9.23/core/vm/runtime#example-Execute - bingo
    - you can try: `go run geth/main.go` from here (having `go get`-ed `go-ethereum` into your `GOPATH`)
