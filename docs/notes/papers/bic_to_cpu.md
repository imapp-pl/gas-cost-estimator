## Continuous Bytecode Instruction Counting for CPU Consumption Estimation

Andrea Camesi Jarle Hulaas Walter Binder

https://www.researchgate.net/publication/37450070_Continuous_Bytecode_Instruction_Counting_for_CPU_Consumption_Estimation

### Takeaways

Some interesting threads to potentially follow, but this approach doesn't differentiate between different JVM instructions, and also focuses on "typical applications", so different from ours.

### Notes

1. Is generally about translating a metric "BIC" (bytecode instruction count) to CPU time (exactly what we like) for JVM. "we show experi-mentally that for each platform there is a stable, application-specific bytecode rate that can be used for translating a BIC value into the cor-responding CPU consumption."
1. visit Java Resource Accounting Framework, Second Edition(J-RAF2, http://www.jraf2.org)
    - dead link
2. ! "use the knowledge ofBRexpin various man-agement tasks, like load-balancing or usage-based billing" ! **usage-based billing**. Follow links resulting for searching for this:
    - https://core.ac.uk/download/pdf/82526395.pdf - "Portable Resource Control in Java: Application to Mobile Agent Security" - not relevant
    - https://www.researchgate.net/publication/2848223_Portable_Resource_Control_in_Java/fulltext/0e5fb082f0c41c4932e6fc21/Portable-Resource-Control-in-Java.pdf - "Portable Resource Control in Java" - not relevant
    - https://www.researchgate.net/publication/223604760_Portable_virtual_cycle_accounting_for_large-scale_distributed_cycle_sharing_systems - "Portable virtual cycle accounting for large-scale distributed cycle sharing systems" - **TODO** optionally get this article, no free access
3. Follow citations "In contrastto related work which takes a low-level approach [11, 15,20]"
4. J-RAF2 and BRexp: J-RAF2 collects BIC and they add on CPU time measurement to this. Then they subtract the collecting routine execution time.
5. try finding Ethereum equivalent of the SPEC JVM98 SPEC JBB2005 Java Grande etc. is there anything like this?
    - however: "this benchmark implements a fairly varied set of activities,and that the statistical characteristics of the collected sam-ples, especially the stability ofBRexpare representative ofmany real-world applications"
    Such a benchmark "many real-world applications" isn't good enough for Ethereum
    - nothing found
6. Rationale for BRexp: a/ measurement precision b/ platform dependence "The objective of determining the CPU consumption forJava bytecodes is difficult because of the level of precisionthat is required:  the time taken to execute any single byte-code on recent hardware is usually far below the measure-ment  resolution  offered  by  the  JVM  or  by  the  OS  itself.Another difficulty is that the desired timings are specific toeach{JVM, OS, hardware}platform combination"
    - how much this applies to EVMs?
    - followed: "In previous ex-periments, we used standard APIs (notably the JVMPI [17]profiling API) for measuring elapsed per-thread CPU time,but  the  inherent  lack  of  resolution"
        - nothing
