// from https://stackoverflow.com/questions/14610459/how-precise-is-gos-time-really

package main

import (
	"fmt"
	"golang.org/x/sys/unix"
	"time"
)

func main() {
	res := unix.Timespec{}
	unix.ClockGetres(unix.CLOCK_MONOTONIC, &res)
	fmt.Printf("Monotonic clock resolution is %d nanoseconds\n", res.Nsec)

	const N = 20
	res_array := [N]unix.Timespec{}
	time_array := [N]time.Time{}

	for i := 0; i < N; i++ {
		unix.ClockGettime(unix.CLOCK_MONOTONIC, &res_array[i])
	}
	for i := 1; i < N; i++ {
		fmt.Printf("Test clock_gettime: %d\n", res_array[i].Nsec-res_array[i-1].Nsec)
	}
	for i := 0; i < N; i++ {
		time_array[i] = time.Now()
	}
	for i := 1; i < N; i++ {
		since := time_array[i].Sub(time_array[i-1])
		fmt.Printf("Test time.Now(): %d\n", since.Nanoseconds())
	}
}
