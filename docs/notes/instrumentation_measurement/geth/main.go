package main

import (
	"flag"
	"fmt"
	"math"
	"math/big"
	"os"
	go_runtime "runtime"
	"time"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/vm/runtime"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/params"

	"./instrumenter"
)

func main() {
	bytecodePtr := flag.String("bytecode", "", "EVM bytecode to execute and measure")
	sampleSizePtr := flag.Int("sampleSize", 1, "Size of the sample - number of measured repetitions of execution")
	printEachPtr := flag.Bool("printEach", true, "If false, printing of each execution time is skipped")

	flag.Parse()

	bytecode := common.Hex2Bytes(*bytecodePtr)
	sampleSize := *sampleSizePtr
	printEach := *printEachPtr

	cfg := new(runtime.Config)
	setDefaults(cfg)

	// Warm-up. **NOTE** we're keeping tracing on during warm-up, otherwise measurements are off
	cfg.EVMConfig.Debug = true
	tracer := instrumenter.NewInstrumenterLogger(nil)
	cfg.EVMConfig.Tracer = tracer
	retWarmUp, _, errWarmUp := runtime.Execute(bytecode, nil, cfg)
	// End warm-up

	sampleStart := time.Now()
	for i := 0; i < sampleSize; i++ {
		tracer = instrumenter.NewInstrumenterLogger(nil)
		cfg.EVMConfig.Tracer = tracer
		go_runtime.GC()
		start := time.Now()
		_, _, err := runtime.Execute(bytecode, nil, cfg)
		duration := time.Since(start)

		if err != nil {
			fmt.Println(err)
		}
		if printEach {
			fmt.Println(duration.Nanoseconds())

			structLogs := tracer.InstrumenterLogs()
			instrumenter.WriteTrace(os.Stdout, structLogs)
		}
	}

	sampleDuration := time.Since(sampleStart)

	if errWarmUp != nil {
		fmt.Println(errWarmUp)
	}
	fmt.Println("Return:", retWarmUp)
	fmt.Println(sampleDuration)

}

// copied directly from github.com/ethereum/go-ethereum/core/vm/runtime/runtime.go
// so that we skip this in measured code
func setDefaults(cfg *runtime.Config) {
	if cfg.ChainConfig == nil {
		cfg.ChainConfig = &params.ChainConfig{
			ChainID:             big.NewInt(1),
			HomesteadBlock:      new(big.Int),
			DAOForkBlock:        new(big.Int),
			DAOForkSupport:      false,
			EIP150Block:         new(big.Int),
			EIP150Hash:          common.Hash{},
			EIP155Block:         new(big.Int),
			EIP158Block:         new(big.Int),
			ByzantiumBlock:      new(big.Int),
			ConstantinopleBlock: new(big.Int),
			PetersburgBlock:     new(big.Int),
			IstanbulBlock:       new(big.Int),
			MuirGlacierBlock:    new(big.Int),
			YoloV2Block:         nil,
		}
	}

	if cfg.Difficulty == nil {
		cfg.Difficulty = new(big.Int)
	}
	if cfg.Time == nil {
		cfg.Time = big.NewInt(time.Now().Unix())
	}
	if cfg.GasLimit == 0 {
		cfg.GasLimit = math.MaxUint64
	}
	if cfg.GasPrice == nil {
		cfg.GasPrice = new(big.Int)
	}
	if cfg.Value == nil {
		cfg.Value = new(big.Int)
	}
	if cfg.BlockNumber == nil {
		cfg.BlockNumber = new(big.Int)
	}
	if cfg.GetHashFn == nil {
		cfg.GetHashFn = func(n uint64) common.Hash {
			return common.BytesToHash(crypto.Keccak256([]byte(new(big.Int).SetUint64(n).String())))
		}
	}
}
