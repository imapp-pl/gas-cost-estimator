## Bytecode Monitoring of Java Programs

Wong

http://www.cs.ox.ac.uk/people/peter.wong/pub/project.pdf

**TODO** (optional) - read the entire paper, but the interting part is:

Timing  analysis  of  Java  bytecodes  -  An  initiative  that  is  brought  up  to  investigate  the  implementation  of  benchmarking  the  Java  Virtual  Machine  (JVM)  Instruction  Set
(3.1 Finding methods to calculate running time of bytecodes:)


### Notes


1. The  initial  idea  is  to  benchmark  single  bytecode  at  a  time  by  repetitively  executing  individual  bytecode  in  multiples  of  10s,  100s  and  1000s,  to  enable JVM to monitor these bytecodes a technique so-called Application Response Measurement (ARM) [8] (**TODO** see [8])
2. Methods for measurement: hard to follow but:
    1. shell out from C and measure in C
    2. System.currentTimeMillis
    3. clock_gettime system call
3. bytecodes are duplicated, with the stack being prepared beforehand (it is claimed that the stack size doesn't affect the results). Duplication is done: "1,10,100,1000 and 9000 iteration(s) sequence"
4. For bytecodes leaving values on the stack, there's a technique similar to `measure inferred` from [`strategy.md`](/docs/strategy.md) - they substract an earlier calculated timing of the `pop`, from the measured opcode timing, they get
5. They infer JVM optimisation kicked in and "This  could  be  one  of  the  reason  (and  the  same  reason)  as  to  why  when  individual  bytecode  was  timed,  one  iteration  took  more  time  that  an  average  of  multiple  iterations  (e.g. 1000).". Not a problem for us
