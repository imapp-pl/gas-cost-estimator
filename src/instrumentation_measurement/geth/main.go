package main

import (
	"flag"
	"fmt"
	"math"
	"math/big"
	"os"
	go_runtime "runtime"
	"time"

  _ "unsafe"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/rawdb"
	"github.com/ethereum/go-ethereum/core/state"
	"github.com/ethereum/go-ethereum/core/vm"
	"github.com/ethereum/go-ethereum/core/vm/runtime"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/params"
)

func main() {

	bytecodePtr := flag.String("bytecode", "", "EVM bytecode to execute and measure")
	sampleSizePtr := flag.Int("sampleSize", 1, "Size of the sample - number of measured repetitions of execution")
	printEachPtr := flag.Bool("printEach", true, "If false, printing of each execution time is skipped")
	printCSVPtr := flag.Bool("printCSV", false, "If true, will print a CSV with standard results to STDOUT")
  modePtr := flag.String("mode", "all", "Measurement mode. Available options: all, total, trace")

	flag.Parse()

	bytecode := common.Hex2Bytes(*bytecodePtr)
	sampleSize := *sampleSizePtr
	printEach := *printEachPtr
	printCSV := *printCSVPtr
  mode := *modePtr

  if mode != "all" && mode != "total"  && mode != "trace" {
    fmt.Fprintln(os.Stderr, "Invalid measurement mode: ", mode)
    os.Exit(1)
  }

	cfg := new(runtime.Config)
	setDefaults(cfg)
	// from `github.com/ethereum/go-ethereum/core/vm/runtime/runtime.go:109`
	cfg.State, _ = state.New(common.Hash{}, state.NewDatabase(rawdb.NewMemoryDatabase()), nil)

	// Warm-up. **NOTE** we're keeping tracing on during warm-up, otherwise measurements are off
	cfg.EVMConfig.Debug = false
	cfg.EVMConfig.Instrumenter = vm.NewInstrumenterLogger()
	retWarmUp, _, errWarmUp := runtime.Execute(bytecode, nil, cfg)
	// End warm-up

	sampleStart := time.Now()
	for i := 0; i < sampleSize; i++ {
    if mode == "all" {
      MeasureAll(cfg, bytecode, printEach, printCSV, i)
    } else if mode == "total" {
      MeasureTotal(cfg, bytecode, printEach, printCSV, i)
    } else if mode == "trace" {
      TraceBytecode(cfg, bytecode, printCSV, i)
    }
	}

	sampleDuration := time.Since(sampleStart)

	if errWarmUp != nil {
		fmt.Fprintln(os.Stderr, errWarmUp)
	}
	fmt.Fprintln(os.Stderr, "Program: ", *bytecodePtr)
	fmt.Fprintln(os.Stderr, "Return:", retWarmUp)
	fmt.Fprintln(os.Stderr, "Sample duration:", sampleDuration)

}

func TraceBytecode(cfg *runtime.Config, bytecode []byte, printCSV bool, sampleId int) {
      tracerConfig := new(vm.LogConfig)
      setDefaultTracerConfig(tracerConfig)

      tracer := vm.NewStructLogger(tracerConfig)
      cfg.EVMConfig.Tracer = tracer
      cfg.EVMConfig.Debug = true

      _, _, err := runtime.Execute(bytecode, nil, cfg)
      if err != nil {
        fmt.Fprintln(os.Stderr, err)
      }

      if printCSV {
        logs := tracer.StructLogs()
        for i, log := range logs {
          fmt.Fprintf(os.Stdout, "%d,%d,%v,%d", i, log.Pc, log.Op, len(log.Stack))

          // let's print only 32 elems of the stack
          for i, elem := range log.Stack {
            if i < 32 {
              fmt.Fprintf(os.Stdout, ",%d", elem)
            }
          }
          // if there are not 32 elems, append the csv with empty columns
          for i := len(log.Stack) ; i < 32 ; i++ {
            fmt.Fprintf(os.Stdout, ",")
          }
          fmt.Fprintf(os.Stdout, "\n")
        }
      }
}

func MeasureTotal(cfg *runtime.Config, bytecode []byte, printEach bool, printCSV bool, sampleId int) {
  cfg.EVMConfig.Instrumenter = vm.NewInstrumenterLogger()
  go_runtime.GC()

  _, _, err := runtime.Execute(bytecode, nil, cfg)

  if err != nil {
    fmt.Fprintln(os.Stderr, err)
  }

  if printCSV {
    vm.WriteCSVInstrumentationTotal(os.Stdout, cfg.EVMConfig.Instrumenter, sampleId)
  }
}

func MeasureAll(cfg *runtime.Config, bytecode []byte, printEach bool, printCSV bool, sampleId int) {
  cfg.EVMConfig.Instrumenter = vm.NewInstrumenterLogger()
  go_runtime.GC()
  start := time.Now()
  _, _, err := runtime.Execute(bytecode, nil, cfg)
  duration := time.Since(start)

  if err != nil {
    fmt.Fprintln(os.Stderr, err)
  }
  if printEach {
    fmt.Fprintln(os.Stderr, "Run duration:", duration)

    instrumenterLogs := cfg.EVMConfig.Instrumenter.Logs
    vm.WriteInstrumentation(os.Stderr, instrumenterLogs)
  }

  if printCSV {
    instrumenterLogs := cfg.EVMConfig.Instrumenter.Logs
    vm.WriteCSVInstrumentationAll(os.Stdout, instrumenterLogs, sampleId)
  }
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

// for full options see github.com/ethereum/go-ethereum/core/vm/logger.go:50
func setDefaultTracerConfig(cfg *vm.LogConfig)  {
	cfg.DisableMemory = false
  cfg.DisableStack = false
  cfg.DisableStorage = true
  cfg.DisableReturnData = false
  cfg.Debug = false
  cfg.Limit = 0
}

// runtimeNano returns the current value of the runtime clock in nanoseconds.
//go:linkname runtimeNano runtime.nanotime
func runtimeNano() int64
