// Copyright 2015 The go-ethereum Authors
// This file is part of the go-ethereum library.
//
// The go-ethereum library is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// The go-ethereum library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with the go-ethereum library. If not, see <http://www.gnu.org/licenses/>.

package instrumenter

import (
	"fmt"
	"io"
	"math/big"
	"time"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/vm"
	"github.com/ethereum/go-ethereum/params"
)

// LogConfig are the configuration options for structured logger the vm.EVM
type LogConfig struct {
	DisableMemory     bool // disable memory capture
	DisableStack      bool // disable stack capture
	DisableStorage    bool // disable storage capture
	DisableReturnData bool // disable return data capture
	Debug             bool // print output during capture end
	Limit             int  // maximum length of output, but zero means unlimited
	// Chain overrides, can be used to execute a trace using future fork rules
	Overrides *params.ChainConfig `json:"overrides,omitempty"`
}

//go:generate gencodec -type InstrumenterLog -field-override structLogMarshaling -out gen_structlog.go

// InstrumenterLog is emitted to the vm.EVM each cycle and lists information about the current internal state
// prior to the execution of the statement.
type InstrumenterLog struct {
	Pc     uint64    `json:"pc"`
	Op     vm.OpCode `json:"op"`
	TimeNs int64     `json:"timeNs"`
}

// OpName formats the operand name in a human-readable format.
func (s *InstrumenterLog) OpName() string {
	return s.Op.String()
}

// InstrumenterLogger is an vm.EVM state logger and implements Tracer.
//
// InstrumenterLogger can capture state based on the given Log configuration and also keeps
// a track record of modified storage which is used in reporting snapshots of the
// contract their storage.
type InstrumenterLogger struct {
	cfg LogConfig

	logs            []InstrumenterLog
	lastCaptureTime time.Time
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
	l.lastCaptureTime = time.Now()
	return nil
}

// CaptureState logs a new structured log message and pushes it out to the environment
func (l *InstrumenterLogger) CaptureState(env *vm.EVM, pc uint64, op vm.OpCode, gas, cost uint64, memory *vm.Memory, stack *vm.Stack, rStack *vm.ReturnStack, rData []byte, contract *vm.Contract, depth int, err error) error {
	timeSincePrevious := time.Since(l.lastCaptureTime)
	log := InstrumenterLog{pc, op, timeSincePrevious.Nanoseconds()}
	l.logs = append(l.logs, log)
	l.lastCaptureTime = time.Now()
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
		fmt.Fprintf(writer, "%-16spc=%08d time_ns=%v", log.Op, log.Pc, log.TimeNs)
		fmt.Fprintln(writer)
	}
}

func WriteCSVTrace(writer io.Writer, logs []InstrumenterLog, programId int, sampleId int, runId int) {
	// CSV header
	// fmt.Fprintln(writer, "program_id,sample_id,run_id,instruction_id,measure_all_time_ns,measure_one_time_ns")

	for instructionId, log := range logs {
		// NOTE: we don't have measure_one_time_ns for now, we leave it out at the end
		fmt.Fprintf(writer, "%v,%v,%v,%v,%v,", programId, sampleId, runId, instructionId, log.TimeNs)
		fmt.Fprintln(writer)
	}
}
