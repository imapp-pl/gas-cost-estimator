package instrumenter

// this portion ensures that we have access to the least-overhead timer

import _ "unsafe"

// runtimeNano returns the current value of the runtime clock in nanoseconds.
//go:linkname runtimeNano runtime.nanotime
func runtimeNano() int64
