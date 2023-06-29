# Instrumentation and measurement using `go-ethereum` (`geth`)

Some low-level notes.

### Notes on `time.Time` precision and monotonicity

1. `time.Since` is handled by monotonic time, as we use it, since go 1.9 [time.Time](https://golang.org/pkg/time/#Time), [discussion](https://github.com/golang/go/issues/12914#issuecomment-277335863), [monotonic clocks](https://golang.org/pkg/time/#hdr-Monotonic_Clocks)
2. from [here](https://stackoverflow.com/questions/14610459/how-precise-is-gos-time-really) we get:
    ```
    $ go run ./src/instrumentation_measurement/clock_resolution_go/main.go
    Monotonic clock resolution is 1 nanoseconds
    ```
3. I tested the overhead of that `clock_gettime` with `time.Since()` (and a trick one: `runtimeNano`):
   - overhead is 10 times smaller using `time.Since`, and even smaller using `runtimeNano`
   - investigate: sometimes both overheads are smaller, sometimes both are bigger, up to 3 fold.
       - it might be worthwhile to measure and record the overhead on every OpCode, in case the overhead suffers from such long-running fluctuations <- yes, we're going to do that
   - overhead of golang's timers analyzed in [`exploration_timers.Rmd`](/src/analysis/exploration_timers.Rmd)

#### Timer takeaways

- timers have periods of better behavior and worse behavior; we might want to filter out measurements from the "worse periods"
- `runtimeNano` seems to be the least overhead overall. Switching from `time.Now` to `runtimeNano` allowed us to measure a quickest opcode execution at 52ns, compared to 67ns with `time.Now`. It's enough to look at the code of [`time.Now`](https://golang.org/src/time/time.go) to see how much it does before capturing time.
- timers seem to require a lot of warm-up
- we will be monitoring the timers during opcode measurements, the noise introduced by that shouldn't be large
- more in [`exploration_timers.Rmd`](/src/analysis/exploration_timers.Rmd) or [quick preview of notebook results](https://htmlpreview.github.io/?https://github.com/imapp-pl/gas-cost-estimator/blob/master/src/analysis/exploration_timers.nb.html)

### Execution environment

Please see Dockerfile.geth file to learn how to prepare the environment.
