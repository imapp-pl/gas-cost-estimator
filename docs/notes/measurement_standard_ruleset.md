## Measurement standard ruleset

In order to ensure easy portability and adaptability to various clients and environments, we write down a ruleset of how should OPCODE measurements be conducted

### `measure_all`

In `measure_all` we measure the time of all OPCODEs exectued for a given program.
We also measure the timer overhead alongside the OPCODE execution measurement.

It turned out to be much better to measure by applying crude modifications to the EVM interpreter code, than to measure via calling a callback (e.g. `Tracer.CaptureState` for `geth`).
To make this easier and as uniform as possible, follow these guidelines:

1. Measure the entire block of code which constitutes a single interpreter iteration. In particular, measure all code which is repeatedly executed as OPCODEs are interpreted.
2. Leave all preprocessing out.
3. Make sure all tracing/debugging is off, except what we need to trace.
4. Gather the measurements consistently. There should be no allocations done by the measurement code.
5. Measurements should be gathered in a pre-allocated collection.
6. Don't do IO (`println` etc.) in the loop.
7. Look into whether preprocessing or similar optimizations don't "move effort" from one instruction to another, like `evmone` does. If so, analyze impact and unfairness.
8. Use timer with least overhead, the most low-level one available.
9. When measuring the timer overhead, capture the time in exactly same way as done for the OPCODE measurement.

Follow this pseudocode pattern:

```go
// all preparations/allocations of the EVM code
// instrumentation preparations/allocations
start_time = now()
while {
    // EVM code
    // OPCODE code etc...
    
    switch some_end_conditions {
        continue: 
            // EVM code
            end_time = now()
            // measure the timer overhead
            end_timer_time = now()
            opcode_duration = end_time - start_time
            timer_duration = end_timer_time - end_time

            durations.store_with_no_allocations(opcode_duration, timer_duration)
            start_time = now()
        break:
            // EVM code
            end_time = now()
            // measure the timer overhead
            end_timer_time = now()
            opcode_duration = end_time - start_time
            timer_duration = end_timer_time - end_time

            durations.store_with_no_allocations(opcode_duration, timer_duration)
            // let it break normally
    }
}

durations.print()
```




