package main

import (
	"flag"
	"fmt"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/vm/runtime"
	go_runtime "runtime"
	"time"
)

func main() {
	bytecodePtr := flag.String("bytecode", "", "EVM bytecode to execute and measure")
	sampleSizePtr := flag.Int("sampleSize", 1, "Size of the sample - number of measured repetitions of execution")

	flag.Parse()

	bytecode := common.Hex2Bytes(*bytecodePtr)
	sampleSize := *sampleSizePtr

	_, _, _ = runtime.Execute(bytecode, nil, nil)

	for i := 0; i < sampleSize; i++ {
		go_runtime.GC()
		start := time.Now()
		ret, _, err := runtime.Execute(bytecode, nil, nil)
		duration := time.Since(start)

		if err != nil {
			fmt.Println(err)
		}
		fmt.Println(ret, duration.Nanoseconds())
	}
}
