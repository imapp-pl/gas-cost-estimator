// from https://stackoverflow.com/questions/14610459/how-precise-is-gos-time-really

// run this to compare the interval measurement with least overhead

package main

import (
	"fmt"
	"golang.org/x/sys/unix"
	"os"
	"time"
)

import _ "unsafe"

// runtimeNano returns the current value of the runtime clock in nanoseconds.
//go:linkname runtimeNano runtime.nanotime
func runtimeNano() int64

func main() {
	res := unix.Timespec{}
	unix.ClockGetres(unix.CLOCK_MONOTONIC, &res)
	fmt.Fprintf(os.Stderr, "Monotonic clock resolution is %d nanoseconds\n", res.Nsec)

	const N = 2000000
	res1 := unix.Timespec{}
	res2 := unix.Timespec{}
	sinceClockGettime := int64(0)
	time1 := time.Time{}
	time2 := time.Time{}
	sinceTime := time.Duration(0)
	runtimeNano1 := int64(0)
	runtimeNano2 := int64(0)
	sinceRuntimeNano := int64(0)

	fmt.Println("clock_gettime,time,runtime_nano")

	for i := 1; i < N; i++ {
		unix.ClockGettime(unix.CLOCK_MONOTONIC, &res1)
		unix.ClockGettime(unix.CLOCK_MONOTONIC, &res2)
		sinceClockGettime = res2.Nsec - res1.Nsec
		time1 = time.Now()
		time2 = time.Now()
		sinceTime = time2.Sub(time1)
		runtimeNano1 = runtimeNano()
		runtimeNano2 = runtimeNano()
		sinceRuntimeNano = runtimeNano2 - runtimeNano1
		fmt.Printf("%d,%d,%d\n", sinceClockGettime, sinceTime, sinceRuntimeNano)
	}
}
