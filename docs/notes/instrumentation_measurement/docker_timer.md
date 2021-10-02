# Investigation of timer differences in cloud/docker

`tl;dr` `sudo sh -c "echo tsc >/sys/devices/system/clocksource/clocksource0/current_clocksource"` on the machine to ensure we are using vDSO for timer, at least matters for go

### Problem

The timer readings are much more costly in golang when executed on an AWS VM, compared to laptop.
This turned out to be caused by AWS using its `xen` clock which seems to not do vDSO, resulting in a costly "classic" syscall.


local laptop:

```
program_id,sample_id,run_id,instruction_id,measure_all_time_ns,measure_all_timer_time_ns
ADDMOD_0,0,1,0,2066,26
ADDMOD_0,0,1,1,67,82
ADDMOD_0,0,1,2,55,25
ADDMOD_0,0,1,3,2036,27
ADDMOD_0,0,1,4,1105,25
```

cloud (docker):

```
program_id,sample_id,run_id,instruction_id,measure_all_time_ns,measure_all_timer_time_ns
ADDMOD_0,0,1,0,762,578
ADDMOD_0,0,1,1,603,565
ADDMOD_0,0,1,2,595,568
ADDMOD_0,0,1,3,864,571
ADDMOD_0,0,1,4,623,566
```

local laptop `lscpu`:

```
Architecture:                    x86_64
CPU op-mode(s):                  32-bit, 64-bit
Byte Order:                      Little Endian
Address sizes:                   39 bits physical, 48 bits virtual
CPU(s):                          4
On-line CPU(s) list:             0-3
Thread(s) per core:              2
Core(s) per socket:              2
Socket(s):                       1
NUMA node(s):                    1
Vendor ID:                       GenuineIntel
CPU family:                      6
Model:                           142
Model name:                      Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz
Stepping:                        9
CPU MHz:                         500.005
CPU max MHz:                     3100,0000
CPU min MHz:                     400,0000
BogoMIPS:                        5399.81
Virtualization:                  VT-x
L1d cache:                       64 KiB
L1i cache:                       64 KiB
L2 cache:                        512 KiB
L3 cache:                        3 MiB
NUMA node0 CPU(s):               0-3
Vulnerability Itlb multihit:     KVM: Vulnerable
Vulnerability L1tf:              Mitigation; PTE Inversion
Vulnerability Mds:               Mitigation; Clear CPU buffers; SMT vulnerable
Vulnerability Meltdown:          Mitigation; PTI
Vulnerability Spec store bypass: Mitigation; Speculative Store Bypass disabled via prctl and seccomp
Vulnerability Spectre v1:        Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:        Mitigation; Full generic retpoline, IBPB conditional, IBRS_FW, STIBP conditional
                                 , RSB filling
Vulnerability Srbds:             Mitigation; Microcode
Vulnerability Tsx async abort:   Not affected
Flags:                           fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush 
                                 dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_ts
                                 c art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf
                                  pni pclmulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm p
                                 cid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdra
                                 nd lahf_lm abm 3dnowprefetch cpuid_fault epb invpcid_single pti ssbd ibrs ibpb s
                                 tibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 
                                 smep bmi2 erms invpcid mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec x
                                 getbv1 xsaves dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp md_c
                                 lear flush_l1d
```

cloud (docker) `lscpu`:

```
Architecture:                    x86_64
CPU op-mode(s):                  32-bit, 64-bit
Byte Order:                      Little Endian
Address sizes:                   46 bits physical, 48 bits virtual
CPU(s):                          1
On-line CPU(s) list:             0
Thread(s) per core:              1
Core(s) per socket:              1
Socket(s):                       1
NUMA node(s):                    1
Vendor ID:                       GenuineIntel
CPU family:                      6
Model:                           63
Model name:                      Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz
Stepping:                        2
CPU MHz:                         2400.039
BogoMIPS:                        4800.00
Hypervisor vendor:               Xen
Virtualization type:             full
L1d cache:                       32 KiB
L1i cache:                       32 KiB
L2 cache:                        256 KiB
L3 cache:                        30 MiB
NUMA node0 CPU(s):               0
Vulnerability Itlb multihit:     KVM: Vulnerable
Vulnerability L1tf:              Mitigation; PTE Inversion
Vulnerability Mds:               Vulnerable: Clear CPU buffers attempted, no microcode; SMT Host state unknown
Vulnerability Meltdown:          Mitigation; PTI
Vulnerability Spec store bypass: Vulnerable
Vulnerability Spectre v1:        Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:        Mitigation; Full generic retpoline, STIBP disabled, RSB filling
Vulnerability Srbds:             Not affected
Vulnerability Tsx async abort:   Not affected
Flags:                           fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush 
                                 mmx fxsr sse sse2 ht syscall nx rdtscp lm constant_tsc rep_good nopl xtopology c
                                 puid pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_dea
                                 dline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm cpuid_fault invpcid
                                 _single pti fsgsbase bmi1 avx2 smep bmi2 erms invpcid xsaveopt
```

### Notes

1. Kudos to MB. This isn't docker, it's the machine (docker on laptop is same as baremetal laptop)
2. Deep dive `runtimeNano()` call:
  1. `//go:linkname runtimeNano runtime.nanotime`
  2. https://cs.opensource.google/go/go/+/master:src/runtime/time_nofake.go;l=20?q=nanotime&ss=go%2Fgo:src%2Fruntime%2F `return nanotime1()`
  3. which version I'm using? `go version go1.17.1 linux/amd64`
  4. https://github.com/golang/go/blob/8d09f7c5178b04bade2859d32d0710233a620d4f/src/runtime/sys_linux_amd64.s#L237
3. Running the clock measurement tool in docker: `sudo docker run --rm -it measurements-geth   bash -c "go get github.com/dterei/gotsc && cd src && go run instrumentation_measurement/clock_resolution_go/main.go"`
4. The vDSO fallback logic is key.
    - the "traditional syscall" is the `fallback` label in the `nanotime1` assembly
    - this in turn resolves to `SYS_clock_gettime`
    - when we run the `clock_resolution_go/main.go` we can see that our `runtimeNano` is very similar to the `clock_gettime` timer. Also, `time.Now()` still equals 2x `runtimeNano`, because it makes 2 such calls!
5. from vDSO manpage:
    - `find arch/$ARCH/ -name '*vdso*.so*' -o -name '*gate*.so*'`
    - didn't follow this but
6. from the Article 6. BINGO:
    -
    ```
    # locally
    $ cat /sys/devices/system/clocksource/clocksource0/current_clocksource
    tsc
    $ sudo docker run --rm -it measurements-geth   bash -c "cat /sys/devices/system/clocksource/clocksource0/current_clocksource"
    tsc
    # on cloud VM
    $ cat /sys/devices/system/clocksource/clocksource0/current_clocksource
    xen
    $ sudo docker run --rm -it measurements-geth   bash -c "cat /sys/devices/system/clocksource/clocksource0/current_clocksource"
    xen
    ```
7. `sudo sh -c "echo tsc >/sys/devices/system/clocksource/clocksource0/current_clocksource"` fixes the problem!

### Articles

1. https://pythonspeed.com/articles/docker-performance-overhead/ - nothing new, `--privileged` flag, that doesn't fix the timers, only some speedup
2. https://www.blazemeter.com/blog/performance-testing-with-docker - irrelevant
3. https://stackoverflow.com/questions/60840320/docker-50-performance-hit-on-cpu-intensive-code - `--security-opt seccomp:unconfined`, that doesn't produce noticeable change
4. https://en.wikipedia.org/wiki/VDSO - what is vDSO, important: "if the kernel does not have vDSO support, a traditional syscall is made"
5. https://man7.org/linux/man-pages/man7/vdso.7.html - very important