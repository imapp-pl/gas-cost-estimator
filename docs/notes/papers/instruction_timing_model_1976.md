## An Instruction Timing Model of CPU Performance

Bernard L. Peuto Leonard J. Shustek

https://inspirehep.net/literature/110758

**NOTE** this is a really old paper, but it has some inspiring thoughts:

1. OpCode pair investigation - on the 70's hardware measurement level opcode pairs were investigated, whether the pairing itself contributes to higher load, warranting distinguishing as a new opcode - we should maybe do a similar exercise?
2. More generally: we could model and explore _variance_ of computational cost of various OpCodes, not only a static cost estimation. E.g. what if `PUSH` behaves differently very in different circumstances? We could generate programs so that they capture this variation the best.
3. Taking this further, there could be parameters to each opcode we don't know about, which should modify the gas cost incurred.
