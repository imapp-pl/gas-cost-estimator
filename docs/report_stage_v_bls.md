# Gas Cost Estimator

Stage 5 Report

## Abstract

Building on the methodologies and insights from previous stages (e.g., [Stage III](https://github.com/imapp-pl/gas-cost-estimator/blob/master/docs/report_stage_iii.md) and [Stage IV](https://github.com/imapp-pl/gas-cost-estimator/blob/master/docs/report_stage_iv.md)), this stage specifically focuses on the gas costs of operations on the BLS12-381 curve, as defined in [EIP-2537](https://eips.ethereum.org/EIPS/eip-2537). These operations underpin critical cryptographic functionalities in Ethereum, such as zero-knowledge proofs and aggregated signatures, making their cost evaluation essential for optimizing efficiency and security within the ecosystem.

## Scope

This report focuses specifically on the seven distinct precompile addresses introduced by EIP-2537, each corresponding to a fundamental operation over the BLS12-381 elliptic curve. These operations are:

* `BLS12_G1ADD`: Point addition on the G1 curve.  
* `BLS12_G2ADD`: Point addition on the G2 curve.  
* `BLS12_G1MSM`: Multi-scalar multiplication (MSM) on the G1 curve.  
* `BLS12_G2MSM`: Multi-scalar multiplication (MSM) on the G2 curve.  
* `BLS12_PAIRING_CHECK`: Verification of elliptic curve pairings.  
* `BLS12_MAP_FP_TO_G1`: Mapping a field element (from Fp) to a point on the G1 curve.  
* `BLS12_MAP_FP2_TO_G2`: Mapping a field element (from Fp2) to a point on the G2 curve.

The scope of this analysis is strictly limited to the intrinsic computational cost of these cryptographic operations on various EVM clients. This implies that the evaluation deliberately abstracts away external factors and network-related overheads, such as the costs associated with state persistence or data storage. The primary objective is to ensure that the proposed gas costs accurately reflect the actual processing effort and CPU cycles consumed by EVM clients when executing these precompiled functions, providing a clear and direct measure of their computational intensity.

## Methodology

The gas cost measurements for this stage were conducted using a benchmarking approach consistent with prior stages of the project. Each BLS12-381 operation was executed multiple times under controlled conditions, with execution times recorded to ensure reliability and repeatability.  
The benchmark programs were composed using test vectors from EIP-2537 as well as Ethereum test cases.
Additionally, we created test cases that measure how various argument sizes affect the execution time. This is done in a similar manner as the previous research.

A cornerstone of this methodology is the scaling of all measured gas costs for BLS12-381 operations relative to the `ECRecover` precompile (address 0x01). This established precompile is assigned a fixed cost of 3000 gas units, serving as a consistent benchmark. This scaling approach is a well-precedented practice within Ethereum's gas schedule adjustments.

The conversion from execution time to gas cost was calculated using the following formula:  

>`gas = (execution_time / base_time) × base_gas`

Here, base time represents the execution time of the ECRecover precompile, and base gas is set at 3000 gas. This methodology ensures that the gas costs reflect the relative computational effort required by each operation.

## Analysis

The analysis is structured into subsections corresponding to the key BLS12-381 operations evaluated in this stage. Each subsection discusses the nature of the operation and the approach to measuring its gas cost.

### Marginal course

The marginal course uses a set of programs that differs with the number of examined operations and estimates the computation time of operations based on statistical methods as the result. The examination is performed thoroughly but no other dependencies are considered, in particular, arguments are fixed.

In all cases, a strong regression is obtained with a low relative standard deviation - BLS12\_G1MSM\_K0 and BLS12\_G2MSM\_K0 are special and discussed separately. That means that the estimated computational times of operations are very reliable. Below is an example of analysed results with a strong regression line, see the marginal reports for further details.

<img src="./report_stage_v_assets/evmone_g2add_marginal.png" width="600" alt="EVMONE G2ADD MARGINAL">

The operations BLS12_G1MSM, BLS12_G2MSM and BLS12_PAIRING_CHECK depend on input size, expressed by the argument k. In all cases the argument is set to k=2 as it includes both multiplication and addition. For BLS12_G1MSM, BLS12_G2MSM examinations with k=1 and k=0 are also provided but for further analysis the case k=2 is selected.

For the operations BLS12_G1MSM, BLS12_G2MSM the case k=1 is provided to compare the cases with and without addition. See the MSM section below for further investigation.

The case k=0 is provided to investigate a potential attack vector. The formula for the gas cost states clearly that such precompile invocation costs zero gas. The standard states (citation) "Also, the case when k = 0 is safe: CALL or STATICCALL cost is non-zero, and the case with formal zero gas cost is already used in Blake2f precompile". The CALL or STATICCALL costs 100 gas. But EIP-7904 proposes a significant drop of the cost to 5 so the network security assumptions may change. The tables below summarize the results for k=0 in two views: relative to k=1 and k=2 cases, and expressed as gas having cases k=1 and k=2 as the base.

| EVM BLS12_G1MSM | K0/K1 % | K0/K2 % | K0/K1 gas | K0/K2 gas |
|-----------------|---------|---------|-----------|-----------|
| besu            | -0.28   |  -0.14  | -33.9     |  -32.4    |
| erigon          | 0.03    |  0.02   | 3.2       |  4.8      |
| evmone          | 0.00    |  0.00   | -0.5      |  -0.7     |
| geth            | 0.21    |  0.16   | 25.5      |  37.0     |
| nethermind      | 1.56    |  1.19   | 187.7     |  270.7    |
| revm            | 0.02    |  0.00   | 2.4       |  0.5      |

| EVM BLS12_G2MSM | K0/K1 % | K0/K2 %  | K0/K1 gas | K0/K2 gas |
|-----------------|---------|----------|-----------|-----------|
| besu            | -0.25   |  -0.13   | -56.6     |  -57.5    |
| erigon          | 0.02    | 0.01     | 3.5       |  5.1      |
| evmone          | 0.00    |  0.00    | -0.5      |  -0.7     |
| geth            | 0.12    |  0.10    | 26.4      |  42.8     |
| nethermind      | 0.82    |  0.61    | 183.5     |  273.0    |
| revm            | 0.01    |  0.00    | 2.3       |  0.6      |

Note that negative values are valid - it means that an operation last less than invoking a warm empty non-precompile address.

### Relative cost to the EIP-2537 gas cost

The graph below presents the estimated computational time relatively to the EIP-2537 gas cost for each EVM.
That is the computational time per 1 gas unit related to the evm's average.
The exact formula is

>`ect_per_gas = ect / EIP2537_gas_cost`

>`relative_ect_per_gas = ect_per_gas / AVG(each_evm.ect_per_gas)`

<img src="./report_stage_v_assets/relative_ct_bls.png" width="600" alt="Relative Computational Time">

BLS12_G1MSM_ARG0 and BLS12_G2MSM_ARG0 are G1 and G2 multiplications - 12000 and 22500. BLS12_PAIRING_CHECK_ARGC is the constant of the pairing check - 37700 gas. The reference value is always 1 as the calculation is performed relatively to 1 gas unit.

The main outcome is that EIP-2537 gas cost is well-balanced. Most values are within &#177; 20%. This means that if the gas cost of one precompile would be adjusted, the others should be changed proportionally.

The remark worth to be noted are that BLS12_MAP_FP_TO_G2 is slightly overpriced and BLS12_G1MSM_ARG0 is slightly underpriced.

Please recall these values are not referred to ECRECOVER, they are self referred. Please note investigation on MSM below also for the full picture.

### Multi-scalar Multiplication (BLS12\_G1MSM, BLS12\_G2MSM)

Multi-scalar multiplication computes the sum of multiple scalar multiplications of points on the G1 or G2 curves. The EIP-2537 expects the implementation of Pippenger’s algorithm, and prices the operations accordingly.
The general formula is  

>`cost = (k * multiplication_cost * discount[k]) / multiplier`

where  

>`k` is a number of pairs/multiplications  
>`multiplication_cost` is 12000 for G1 and 22500 for G2  
>`discount` is a value from the discount table and depends on k  
>`multiplier` is always 1000  

Note a sublinear dependency. Thus a semi-linear regression is employed in analysis. That is defined as the problem of finding the best fit of the curve determined by the discount table to measurements.

There are two measurements courses: the marginal and the arguments. The marginal course is more accurate, the arguments course investigate the dependency on the argument k - the number of pairs/multiplications. Finally, the results of marginal and arguments courses are compared.

The marginal course consists of three cases: k=0, k=1 and k=2. The case k=0 is discussed above, and it is omitted in this section. The main difference between the cases k=1 and k=2 is that the latter requires addition. The reference gas cost of G1 MSM operation is 12000 for k=1 and 22776 for k=2, the reference gas cost of G2 MSM operation is 22500 for k=1 and 45000 for k=2. So the ratio is 1.898 and 2.0 for G1 MSM and G2 MSM operations respectively.

| EVM        | G1 reference ratio | G1 estimated ratio | G2 reference ratio | G2 estimated ratio |
|------------|--------------------|--------------------|--------------------|--------------------|
| besu       |  1.898             |  1.99              |  2                 |  1.97              |
| erigon     |  1.898             |  1.27              |  2                 |  1.36              |
| evmone     |  1.898             |  1.49              |  2                 |  1.43              |
| geth       |  1.898             |  1.31              |  2                 |  1.23              |
| nethermind |  1.898             |  1.32              |  2                 |  1.34              |
| revm       |  1.898             |  8.72              |  2                 |  7.43              |

Note that EVMs are warmed up before measurements so it not the case that some software required initialization.

The measurements significantly depend on the argument k \- the number of multiplications. The gas cost formula includes discount factor which is non-linear and needs examination also.
There are two sets within the arguments course, 1-128 multiplications and 1-8 multiplications - in short the large and small arguments. Note that the discount table defined in EIP-2537 ranges to 128. The reason to investigate small arguments is the observation that most EVMs have different behaviour than for the large arguments. It may because of optimizations available for small arguments.

Below are graphs for large arguments. The red dotted line is the fitted cost curve according to the discount table - semi-linear regression.

<img src="./report_stage_v_assets/besu_msm_g1.png" width="600" alt="Besu BLS12_G1MSM">
<img src="./report_stage_v_assets/besu_msm_g2.png" width="600" alt="Besu BLS12_G2MSM">
<img src="./report_stage_v_assets/evmone_msm_g1.png" width="600" alt="Evmone BLS12_G1MSM">
<img src="./report_stage_v_assets/evmone_msm_g2.png" width="600" alt="Evmone BLS12_G2MSM">
<img src="./report_stage_v_assets/erigon_msm_g1.png" width="600" alt="Erigon BLS12_G1MSM">
<img src="./report_stage_v_assets/erigon_msm_g2.png" width="600" alt="Erigon BLS12_G2MSM">
<img src="./report_stage_v_assets/geth_msm_g1.png" width="600" alt="Geth BLS12_G1MSM">
<img src="./report_stage_v_assets/geth_msm_g2.png" width="600" alt="Geth BLS12_G2MSM">
<img src="./report_stage_v_assets/nethermind_msm_g1.png" width="600" alt="Nethermind BLS12_G1MSM">
<img src="./report_stage_v_assets/nethermind_msm_g2.png" width="600" alt="Nethermind BLS12_G2MSM">
<img src="./report_stage_v_assets/revm_msm_g1.png" width="600" alt="Revm BLS12_G1MSM">
<img src="./report_stage_v_assets/revm_msm_g2.png" width="600" alt="Revm BLS12_G2MSM">

The first observation is: revm results look chaotic. But repeated measurements yield similar shapes. So it is specific for the evm. There are three segments: 1-16, 16-32, 32-128. The point is that estimations are not reliable with such data. Although results G1 MSM in the segment 32-128 are in the line of expectation. Further investigation is needed to explain the phenomena.

The second observation is: besu, erigon and geth results have two modes. For small arguments the results are significantly lower. For erigon and geth it is 1-20 arguments, for besu it is 1-4 arguments. These results are visibly below estimated regression. For the small arguments optimizations are possible other than Pippenger’s algorithm and this is a reason for these two modes. Note that low results for small arguments affects the regression line - it would fit better to large arguments only. And that would confirm the discount table.

This raises the dilemma: whether the results for small arguments should be taken into account for the gas cost estimations or not. The results for large arguments cannot be neglected as this could make the gas cost for large arguments underpriced and undermine the network security. Of course operations with low arguments would be overpriced, and that is a drawback. The decision is to use all arguments for the estimation. But it is not obvious and possibly not final.

The third observation is: evmone and nethermind have almost perfect match to the estimated regression. This confirms the discount table. Note that the two evms have higher results for 32-64 arguments. The reason for that is uncertain.

The standard enforces Pippenger’s algorithm. For small arguments, in particular k=1 and k=2, more effective optimisations are possible. Below are graphs for small arguments.

<img src="./report_stage_v_assets/besu_msm_g1_s.png" width="600" alt="Besu BLS12_G1MSM S">
<img src="./report_stage_v_assets/besu_msm_g2_s.png" width="600" alt="Besu BLS12_G2MSM S">
<img src="./report_stage_v_assets/evmone_msm_g1_s.png" width="600" alt="Evmone BLS12_G1MSM S">
<img src="./report_stage_v_assets/evmone_msm_g2_s.png" width="600" alt="Evmone BLS12_G2MSM S">
<img src="./report_stage_v_assets/erigon_msm_g1_s.png" width="600" alt="Erigon BLS12_G1MSM S">
<img src="./report_stage_v_assets/erigon_msm_g2_s.png" width="600" alt="Erigon BLS12_G2MSM S">
<img src="./report_stage_v_assets/geth_msm_g1_s.png" width="600" alt="Geth BLS12_G1MSM S">
<img src="./report_stage_v_assets/geth_msm_g2_s.png" width="600" alt="Geth BLS12_G2MSM S">
<img src="./report_stage_v_assets/nethermind_msm_g1_s.png" width="600" alt="Nethermind BLS12_G1MSM S">
<img src="./report_stage_v_assets/nethermind_msm_g2_s.png" width="600" alt="Nethermind BLS12_G2MSM S">
<img src="./report_stage_v_assets/revm_msm_g1_s.png" width="600" alt="Revm BLS12_G1MSM S">
<img src="./report_stage_v_assets/revm_msm_g2_s.png" width="600" alt="Revm BLS12_G2MSM S">

Besu and revm have visible steps. As is stated above, revm requires further investigation. Besu provides optimisations for arguments k=1 and k=2. But other evms have the results in line with the expected curve based on the discount table. Thus, erigon and geth results fit the expected curve independently for the two modes described above.

To verify consistency of the marginal and arguments courses, the results for the small arguments investigation is preferred because they yields better estimations for the arguments k=1 and k=2. Note, that for the further analysis the estimates based on the large arguments are eligible, but at this paragraph it is checked if two applied courses do not diverge.
We compare the estimated computation time obtained from the arguments course (red dotted line) with the results obtained from the marginal cost.

| EVM | G1MSM k=1 | G1MSM k=2 | G2MSM k=1 | G2MSM k=2 |
|-----|-----------|-----------|-----------|-----------|
| besu       | 0.07      | 	1.04     | 	1.59     |	2.09 |
| erigon     | 0.91      | 	1.01     | 	1.08     |	0.99 |
| evmone     | 0.80      | 	1.00     | 	0.73     |	0.95 |
| geth       | 0.96      | 	1.00     | 	1.01     |	1.01 |
| nethermind | 0.80      | 	0.96     | 	0.72     |	0.93 |
| revm       | 0.04      | 	0.60     | 	1.48     |	0.61 |

The desired value is 1. The results for k=1 and k=2 in the case of besu and revm are not well estimated by the regression curve even for the small arguments. 

Statistic methods employed to analysis calculate a match to `a+b*k` regression. The point is that the constant cost `a` is assumed and calculated to find the best match, but EIP-2537 formula does not contain the constant cost. For the record, `b` is the argument cost.
We verify if the constant cost that comes from estimation, can be neglected. For the reference value the argument estimated computation time is picked as it is relatively stable what is discussed above. Note that the argument cost is G1/G2 multiplication cost. The argument gas cost is set according to EIP-2537 gas cost, i.e. 12000 for G1 and 22500 for G2, and the expected gas cost for the constant component is calculated.

| EVM | G1 multiplication | G1 constant | G2 multiplication | G2 constant |
|-----|-------------------|-------------|-------------------|-------------|
| besu       | 12000             | 	75825.0    | 	22500            | 	224673.0   |
| erigon     | 12000             | 	516587.4   | 	22500            | 	989540.0   |   
| evmone     | 12000             | 	-1197.1    | 	22500            | 	-9092.3    |    
| geth       | 12000             | 	514251.5   | 	22500            | 	1076676.9  |  
| nethermind | 12000             | 	49205.8    | 	22500            | 	53870.9    |    
| revm       | 12000             | 	366227.3   | 	22500            | 	650921.1   |   

For evmone the constant gas cost can be neglected, even -9k gas at the G2 side. For other evms, the G1 side seems to be consistent: except revm, the constant gas cost is around 55k. But as is discussed above, revm needs further investigations. The G2 side is not consistent. The estimated gas cost for the constant component is large or even huge. But note that large arguments means arithmetic of large gas amount. 1M gas (estimated gas cost of the constant component) is relatively small comparing to 10M gas (reference gas cost of BLS12_G2MSM operations with 50 pairs).
Nevertheless, these gas estimations enforced by the large arguments are unacceptable for the small arguments - a single multiplication, k=1, cannot cost 1M gas. This formulates the dilemma.

The table below presents estimation of the constant component based on the results for the small arguments. The estimated argument computation time for the large arguments is still the reference value. 

| EVM | G1 multiplication (large) | G1 multiplication (small) | G1 constant (small) | G2 multiplication (large) | G2 multiplication (small) | G2 constant (small) |
|-----|---------------------------|---------------------------|---------------------|---------------------------|---------------------------|---------------------|
| besu       | 12000                    | 25771.0                  | -25015.7           | 22500                     | 56786.8                  | -21036.8           |
| erigon     | 12000                    | 52785.1                  | 60600.9            | 22500                     | 95971.9                  | 288404.3           |           
| evmone     | 12000                    | 11580.0                  | 527.9              | 22500                     | 20396.0                  | 3240.5             |             
| geth       | 12000                    | 50694.0                  | 77827.8            | 22500                     | 96969.2                  | 318655.9           |           
| nethermind | 12000                    | 15126.0                  | 7862.5             | 22500                     | 25549.2                  | 9075.7             |             
| revm       | 12000                    | 138882.1                 | -137938.9          | 22500                     | 152872.2                 | -78966.0           |           

For evmone and nethermind the examination for the small arguments is consistent with the large arguments. For erigon and geth the ratio of the argument cost to the constant cost dropped, it is 1:1 for G1 and 1:3 for G2. But the argument cost increases significantly, it is around 5 times as the reference.

To summarize this part. We can follow the investigation of small arguments or the investigation of large arguments to determine the gas cost of MSM precompiles. Picking any direction may lead to dangerous overpirce or underprice of the other arguments.
There are consistent estimations of gas cost for the argument component based on the large arguments. But there is no consistency for the constant component of operations.
For now, it would be best to investigate the cause of the constant cost for some emvs, but it is out of scope of this report.
It seems that the gas cost should be based on the large arguments from the perspective of network security.

Finally, we verify the approach to the gas cost: the arguments cost is based on the large arguments and the constant cost is nullified. Specifically, we consider only 32-128 arguments and remove the constant cost. The light red dotted line is the calculated regression curve, the red dotted line is the estimated computational time - the regression curve with the constant component subtracted.

<img src="./report_stage_v_assets/besu_msm_g1_pv.png" width="600" alt="Besu BLS12_G1MSM">
<img src="./report_stage_v_assets/besu_msm_g2_pv.png" width="600" alt="Besu BLS12_G2MSM">
<img src="./report_stage_v_assets/evmone_msm_g1_pv.png" width="600" alt="Evmone BLS12_G1MSM">
<img src="./report_stage_v_assets/evmone_msm_g2_pv.png" width="600" alt="Evmone BLS12_G2MSM">
<img src="./report_stage_v_assets/erigon_msm_g1_pv.png" width="600" alt="Erigon BLS12_G1MSM">
<img src="./report_stage_v_assets/erigon_msm_g2_pv.png" width="600" alt="Erigon BLS12_G2MSM">
<img src="./report_stage_v_assets/geth_msm_g1_pv.png" width="600" alt="Geth BLS12_G1MSM">
<img src="./report_stage_v_assets/geth_msm_g2_pv.png" width="600" alt="Geth BLS12_G2MSM">
<img src="./report_stage_v_assets/nethermind_msm_g1_pv.png" width="600" alt="Nethermind BLS12_G1MSM">
<img src="./report_stage_v_assets/nethermind_msm_g2_pv.png" width="600" alt="Nethermind BLS12_G2MSM">
<img src="./report_stage_v_assets/revm_msm_g1_pv.png" width="600" alt="Revm BLS12_G1MSM">
<img src="./report_stage_v_assets/revm_msm_g2_pv.png" width="600" alt="Revm BLS12_G2MSM">

To visualize the deviation we calculate the proportion of the measurements and the estimated computation time. This is an assessment of how MSM precompiles are underpriced because of the constant cost nullification.

<img src="./report_stage_v_assets/besu_msm_g1_pv_ratio.png" width="600" alt="Besu BLS12_G1MSM">
<img src="./report_stage_v_assets/besu_msm_g2_pv_ratio.png" width="600" alt="Besu BLS12_G2MSM">
<img src="./report_stage_v_assets/evmone_msm_g1_pv_ratio.png" width="600" alt="Evmone BLS12_G1MSM">
<img src="./report_stage_v_assets/evmone_msm_g2_pv_ratio.png" width="600" alt="Evmone BLS12_G2MSM">
<img src="./report_stage_v_assets/erigon_msm_g1_pv_ratio.png" width="600" alt="Erigon BLS12_G1MSM">
<img src="./report_stage_v_assets/erigon_msm_g2_pv_ratio.png" width="600" alt="Erigon BLS12_G2MSM">
<img src="./report_stage_v_assets/geth_msm_g1_pv_ratio.png" width="600" alt="Geth BLS12_G1MSM">
<img src="./report_stage_v_assets/geth_msm_g2_pv_ratio.png" width="600" alt="Geth BLS12_G2MSM">
<img src="./report_stage_v_assets/nethermind_msm_g1_pv_ratio.png" width="600" alt="Nethermind BLS12_G1MSM">
<img src="./report_stage_v_assets/nethermind_msm_g2_pv_ratio.png" width="600" alt="Nethermind BLS12_G2MSM">
<img src="./report_stage_v_assets/revm_msm_g1_pv_ratio.png" width="600" alt="Revm BLS12_G1MSM">
<img src="./report_stage_v_assets/revm_msm_g2_pv_ratio.png" width="600" alt="Revm BLS12_G2MSM">

### Pairing Check (BLS12\_PAIRING\_CHECK)

The pairing check operation verifies whether a set of pairings on the BLS12-381 curve satisfies a specific condition. The nominal cost formula is:  

>`cost = 37700 + k * 32600`

where  

>`k` is a number of pairs

There are two measurements courses: the marginal and the arguments. The marginal programs assume the argument `k=2` so the reference gas cost is 102300. The arguments course investigates the dependence on `k` only. Note that the gas cost formula consists of the constant cost and the argument cost. Finally, the results of marginal and arguments courses are compared.

In all cases of the argument course a strong regression is obtained with a low relative standard deviation. That means that the estimated computational times of the constant and argument components are very reliable. Below is an example of analysed results with a strong regression line, see the arguments reports for further details.

<img src="./report_stage_v_assets/evmone_pairing_check_arguments.png" width="600" alt="EVMONE PAIRNG CHECK ARGUMENTS">

<img src="./report_stage_v_assets/evmone_pairing_check_all_arguments.png" width="600" alt="EVMONE PAIRNG CHECK ALL ARGUMENTS">

The latter image presents the series of programs with 0 operations per program (wheat color), 15 operations per program (green color) and 30 operations per program (blue program). A proportional linear distance between the series is expected.

The results are scaled relatively to the argument cost in the table below.  

| EVM        | the argument cost (ref 32600) | the constant cost (ref 37700) | %      | the marginal estimation (ref 102300) | % |
|------------|-------------------------------|-------------------------------|--------|--------------------------------------|---|
| besu       | 32600                         |  42691.3                      | -13.2  | 107315.5                             | -4.9    |
| erigon     | 32600                         |  41980.8                      | -11.4  | 107820.0                             | -5.4    |
| evmone     | 32600                         |  30650.8                      | 18.7   | 95716.7                              | 6.4       |
| geth       | 32600                         |  42210.4                      | -12.0  | 106310.6                             | -3.9    |
| nethermind | 32600                         |  29808.5                      | 20.9   | 95525.8                              | 6.6       |
| revm       | 32600                         |  44145.6                      | -17.1  | 99246.3                              | 3.0      |

Assuming the argument cost is the reference value, the calculated constant cost diverges &#177; 20% from the expected value, and the estimated cost of precompile in the marginal course diverges &#177; 6% from the expected value. The latter proves methodology and the great consistency between these two courses. The former indicates quite good balance between the constant cost and the arguments cost.

### Pivot

ECRecover precompile was selected as the pivot operation for this research. The pivot operation is the reference to verify the gas cost for BLS precompiles against to. Literally, 3100 gas is considered as the cost for ECRecovery operation. So, ECRecovery and BLS precompiles are executed in the set.

ECRecovery precompile was analysed in the stage 4 of the Gas Cost Estimator project and is discussed in EIP-7904.

According to the final report (that compares the results), assuming ECRecovery precompile results as the benchmark fixed to 3100 gas, the calculated alternative gas is as follows.

| cost element              | current gas | alternative gas | diff % |
|---------------------------|-------------|-----------------|--------|
| ECRECOVER                 | 3100        | 3100            | 0      |
| BLS12_G1ADD               | 375         | 213             | -43.2  |
| BLS12_G2ADD               | 600         | 402             | -33    |
| BLS12_G1MSM_ARG0          | 12000       | 8346            | -30.4  |
| BLS12_G2MSM_ARG0          | 22500       | 15875           | -29.4  |
| BLS12_PAIRING_CHECK_ARG0  | 32600       | 24149           | -25.5  |
| BLS12_PAIRING_CHECK_CONST | 37700       | 27942           | -25.8  |
| BLS12_MAP_FP_TO_G1        | 5500        | 4273            | -22.3  |
| BLS12_MAP_FP_TO_G2        | 23800       | 14773           | -37.9  |

The calculation comply with the observation stated above: the precompiles costs are well-balanced. 
That's read: if the benchmark is ECRecovery, then every gas cost should be decreased by ~30%, BLS_G1ADD a bit more.

The stage 4 of Gas Cost Estimator project provided analysis on ECRecovery precompile. The reference values are a large set of arithmetic opcodes. The final calculation discovered that the precompile is substantially underpriced. This is said excerpt from the stage 4 report.

| cost element              | current gas | alternative gas | diff % |
|---------------------------|-------------|-----------------|--------|
| ECRECOVER                 | 3100        | 10299           | +232.2 |

That's read: if the benchmark are the arithmetic opcodes, then BLS gas cost should be increased by ~132% (3.322*0.7=2.32).

The EIP-7904 is based on the stage 4 report. It provides a general repricing - in particular substantial decrement of gas cost for the arithmetic opcodes. It is also stated that: assuming the provided costs for the arithmetic opcodes, ECRecovery gas cost should increase by ~20%, but the increase is a little so the price is recommended not to be changed and avoid backward compatibility risks.
That's read: if the benchmark are EIP-7904 arithmetic opcodes, then BLS gas should be decreased by ~16% (1.2*0.7=0.84).

BLS procompiles are well-balanced as stated above. In the graph below ECRecovery is the reference value - ECRecovery is fixed at 3100 gas and BLS precompiles are calculated relatively.

<img src="./report_stage_v_assets/all_add.png" width="600" alt="BLS12_G1ADD vs ECRecovery">

The spread is significant. And the estimates bear a substantial uncertainty. We investigate the situation of ECRecovery itself. Recall the results from the stage 4. In the graph below there is the estimates of ECRecovery with the arithmetic opcodes as the reference.

<img src="./report_stage_v_assets/ecrecovery_stage4.png" width="600" alt="ECRecovery">

The spread is significant. But if we combine these two relations (bls-to-ecrecovery, ecrecovery-to-arithmetic), then there is a relation (bls-to-arithmetic) with a moderate spread. Thus, the final estimates provided in this work are still reliable, but it is better to take the arithmetic opcodes as the reference.

### BLS Tests

Together with the marginal and the arguments courses, a tests driven programs are investigated. Test input data are fetched from [EIP-2537 test vectors](https://github.com/ethereum/EIPs/tree/master/assets/eip-2537). For each test there are provided programs that execute input data in the marginal course favor. Note that each procompile is associated with multiple tests. Then the computation time of invoking the precompile with provided input data is estimated. The goal is to verify if any special or edge cases do not impose a threat. This research is supplementary to the work described above.

Estimated computation time of precompile invocation associated with a test is calculated with the methods provided by the marginal course. The benchmarks are the results obtained in the marginal course. Thus, it is expected then the tests results are comparable to the marginal results.

The vector tests are positive and negative. The estimated computation time may be relatively very low in the case of negative tests. This is expected and sometimes desired. For instance an invocation with an empty input should be very quick. The negative tests have zero gas cost assigned as a reference.

In the graphs below data are scaled so 1.0 is a benchmark - the marginal course results. The interpretation is: if the result is below the reference, it is good, if the result is somewhat above, it is worth to check but not alarming, if it is much above, it is a risk.

<img src="./report_stage_v_assets/relative_ct_bls_tests_g1msm.png" width="600" alt="BLS12_G1MSM">
<img src="./report_stage_v_assets/relative_ct_bls_tests_g2msm.png" width="600" alt="BLS12_G2MSM">
<img src="./report_stage_v_assets/relative_ct_bls_tests_pairing_check.png" width="600" alt="BLS12_PAIRNG_CHECK">
<img src="./report_stage_v_assets/relative_ct_bls_tests_g1map_fp.png" width="600" alt="BLS12_MAP_FP_TO_G1">
<img src="./report_stage_v_assets/relative_ct_bls_tests_g2map_fp.png" width="600" alt="BLS12_MAP_FP_TO_G2">

The tests: BLS12_G1MSM_bls_g1msm_multiple, BLS12_G1MSM_bls_g1msm_multiple_with_point_at_infinity, BLS12_G2MSM_bls_g2msm_multiple, BLS12_G2MSM_bls_g2msm_multiple_with_point_at_infinity - seem to have very high results for besu. But it is not the case. Please see the MSMs section above. For the arguments k > 2, besu yields super-linear estimated computation time compared to k=2 case. And that is consistent with the results for these test. So any other discussion is directed to the MSMs part.
Other tests worth to be noted are: BLS12_G1MSM_bls_g1msm_random\*g1_unnormalized_scalar, BLS12_G1MSM_bls_g1msm_random\*p1_unnormalized_scalar, BLS12_G2MSM_bls_g2msm_random\*g2_unnormalized_scalar, BLS12_G2MSM_bls_g2msm_random\*p2_unnormalized_scalar. Most evms report higher than expected results when multiplying by an unnormalized scalar. But the excess is moderate and in the opinion of authors it is safe. Still worth to be verified by teams.

<img src="./report_stage_v_assets/relative_ct_bls_tests_g1add.png" width="600" alt="BLS12_G1ADD">
<img src="./report_stage_v_assets/relative_ct_bls_tests_g2add.png" width="600" alt="BLS12_G2ADD">

For BLS12_G1ADD and BLS12_G2ADD two evms have high results, they are besu and geth. 

Check the detailed tests report to explain why besu has excessive results. This is an example graph that present the regression analysis for the test BLS12_G1ADD_bls_g1add_g1+p1.

<img src="./report_stage_v_assets/besu_g1add_g1_p1.png" width="600" alt="besu BLS12_G1ADD_bls_g1add_g1+p1">

The correlation is visible but for the purpose of this work it is quite weak. Please check graphs for other tests. The measurements for op_count=0 impact on the estimated computation time - the regression - make it higher. Recall that the reference value is the estimated computation time for G1ADD and G2ADD respectively obtained in the marginal course. So here is the graph for the regression analysis of the reference value.

<img src="./report_stage_v_assets/besu_g1add.png" width="600" alt="besu BLS12_G1ADD">

Here is the step for op_count=0. But the impact of the measurement for op_count=1 on the regression is lesser since there is much more measurements for op_count>0. Note that even for op_count=0 an evm instance is warmed up, and it is not the case that for op_count>0 an evm instance bears additional computation cost related to some initialization.

Conclusion: in case of besu, the high results for tests are caused by the step at op_count=0, and this step needs an explanation, not the tests.

The correlation is strong enough in the case of geth, so the results are reliable. See the graph below as an example.

<img src="./report_stage_v_assets/geth_g1add_g1_p1.png" width="600" alt="geth BLS12_G1ADD_bls_g1add_g1+p1">

Conclusion: in case of geth and BLS12_G1ADD, the results for some tests are 2 times higher than the reference value. For instance BLS12_G1ADD_bls_g1add_empty_input - this one is quite interesting because other evms have very low results. It is advised to investigate the situation.

## Conclusions

Our analysis confirms three things:

* The team responsible for the EIP-2537 has done a great job in defining the gas costs for BLS12-381 operations. The gas costs are well-balanced and consistent across different EVM clients.
* The current gas cost schedule does not pose any significant security risks to the Ethereum network.
* The methodology used in the Gas Cost Estimator project is sound and can be applied to any other operations.

### Proposal

The table below summarizes the proposed gas cost based on our analysis:

| Operation | Current Gas | Proposed Gas |
| ------------ | :---: | :---: |
| BLS12\_G1ADD | 375   | 375   |
| BLS12\_G2ADD | 600   | 600   |
| BLS12\_G1MSM | k \* 12000 \* discountG1(k) | k \* 12000 \* discountG1(k) `*`|
| BLS12\_G2MSM | k \* 22500 \* discountG2(k) | k \* 22500 \* discountG2(k) `*`|
| BLS12\_PAIRING\_CHECK | 37700 + k \* 32600 | 37700 + k \* 32600 |
| BLS12\_MAP\_FP\_TO\_G1 | 5500 | 5500 |
| BLS12\_MAP\_FP2\_TO\_G2 | 23800 | 16300 |

`*` Both multiplication methods could be revised as described in the MSM section below.

### Recommendations

Discuss whether the introduction of a base cost for the BLS12_G1MSM and BLS12_G2MSM operations is necessary. This could be paired with the reduction of the `k` cost or adjusting the discount factor for small `k` values.

The Revm team to revise their MSM implementation. It has very good optimization for large k, but for k \< 32 some edge cases are exceeding the expected costs significantly.
