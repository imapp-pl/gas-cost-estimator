// based on `StructLogger` from `github.com/ethereum/go-ethereum/core/vm/logger.go:123`

package instrumenter

import (
	"fmt"
	"io"
	"math/big"
	"time"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/vm"
)

type LogConfig struct {
}

//go:generate gencodec -type InstrumenterLog -field-override structLogMarshaling -out gen_structlog.go

// InstrumenterLog is emitted to the vm.EVM each cycle and lists information about the current internal state
// prior to the execution of the statement.
type InstrumenterLog struct {
	Pc          uint64    `json:"pc"`
	Op          vm.OpCode `json:"op"`
	TimeNs      int64     `json:"timeNs"`
	TimerTimeNs int64     `json:"timerTimeNs"`
}

// InstrumenterLogger is an vm.EVM state logger and implements Tracer.
type InstrumenterLogger struct {
	cfg LogConfig

	logs            []InstrumenterLog
	lastCaptureTime int64

	// worker fields, just to avoid reallocation of local vars
	timeSincePrevious int64
	runtimeNano1      int64
	runtimeNano2      int64
	sinceRuntimeNano  int64
	log               InstrumenterLog
}

// NewInstrumenterLogger returns a new logger
func NewInstrumenterLogger(cfg *LogConfig) *InstrumenterLogger {
	logger := &InstrumenterLogger{}
	if cfg != nil {
		logger.cfg = *cfg
	}
	return logger
}

// CaptureStart implements the Tracer interface to initialize the tracing operation.
func (l *InstrumenterLogger) CaptureStart(from common.Address, to common.Address, create bool, input []byte, gas uint64, value *big.Int) error {
	l.lastCaptureTime = runtimeNano()
	return nil
}

// CaptureState logs a new structured log message and pushes it out to the environment
func (l *InstrumenterLogger) CaptureState(env *vm.EVM, pc uint64, op vm.OpCode, gas, cost uint64, memory *vm.Memory, stack *vm.Stack, rStack *vm.ReturnStack, rData []byte, contract *vm.Contract, depth int, err error) error {
	// measure the current iteration
	l.timeSincePrevious = runtimeNano() - l.lastCaptureTime

	// measure the most current timer overhead
	l.runtimeNano1 = runtimeNano()
	l.runtimeNano2 = runtimeNano()
	l.sinceRuntimeNano = l.runtimeNano2 - l.runtimeNano1

	// add to log
	l.log = InstrumenterLog{pc, op, l.timeSincePrevious, l.sinceRuntimeNano}
	l.logs = append(l.logs, l.log)

	// start timing the next iteration
	l.lastCaptureTime = runtimeNano()
	return nil
}

// CaptureFault implements the Tracer interface to trace an execution fault
// while running an opcode.
func (l *InstrumenterLogger) CaptureFault(env *vm.EVM, pc uint64, op vm.OpCode, gas, cost uint64, memory *vm.Memory, stack *vm.Stack, rStack *vm.ReturnStack, contract *vm.Contract, depth int, err error) error {
	return nil
}

// CaptureEnd is called after the call finishes to finalize the tracing.
func (l *InstrumenterLogger) CaptureEnd(output []byte, gasUsed uint64, t time.Duration, err error) error {
	return nil
}

// InstrumenterLogs returns the captured log entries.
func (l *InstrumenterLogger) InstrumenterLogs() []InstrumenterLog { return l.logs }

// WriteTrace writes a formatted trace to the given writer
func WriteTrace(writer io.Writer, logs []InstrumenterLog) {
	for _, log := range logs {
		fmt.Fprintf(writer, "%-16spc=%08d time_ns=%v timer_time_ns=%v", log.Op, log.Pc, log.TimeNs, log.TimerTimeNs)
		fmt.Fprintln(writer)
	}
}

func WriteCSVTrace(writer io.Writer, logs []InstrumenterLog, runId int) {
	// CSV header must be in sync with these fields here :(, but it's in measurements.py
	for instructionId, log := range logs {
		fmt.Fprintf(writer, "%v,%v,%v,%v", runId, instructionId, log.TimeNs, log.TimerTimeNs)
		fmt.Fprintln(writer)
	}
}
