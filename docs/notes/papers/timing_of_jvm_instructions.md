## Platform Independent Timing of Java Virtual Machine Bytecode Instructions


Jonathan M. Lambert1and  James F.Power

http://mural.maynoothuniversity.ie/6382/2/JP-Platform.pdf

### Notes

1. white-box ((done) follow citations  [11,6,7], [25]), where JVM source code is available vs black-box (statistically, on a entire program level). This paper is black-box: "to what extent can we reliably predict theexecution timings for JVM bytecode instructions at this kind of platform-independentlevel?"
    - they do white-box for calibration/validation using RDTSC
    - calibration is linear regression of their method vs RDTSC. 2 outliers (not accounted for). Their method under-predicts by 23%, but what if one takes out the 2 outliers, which are over-prdicted?
2. Problems with white-box sound JVM specific: "Java bytecode instructions execute within nanoseconds.  Attempting to measurethese instructions with a high degree of precision using standard Java library tim-ing methods such asSystem.currentTimeMillis or System.nanoTimeresults in thequantisation errors masking their true execution times.".
    - do we have nanosecond accuracy In rust/c? **TODO** (done for golang: https://github.com/imapp-pl/gas-cost-estimator/issues/14)
    - there is `System.nanoTime` but "System.nanoTimecannot guarantee nanosecond accuracy"
3. **TODO** (optional) follow citations [18, 4, 9] in case low-resolution timing handling is required, or at least the paragraph that summarizes them
4. (can't find) follow [13] and  follow [26] "present a technique for the measure-ment of bytecode execution times"
5. (done) follow [20] "production of aninstruction timing model to model CPU performance measurements"
6. They estimate timer overhead by 2 consecutive calls - same thing on our list
7. In JVM you have an instuction to invoke `System.currentTimeMillis`. See Code segment 1
