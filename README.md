# Gas Cost Estimator

The project aims to provide a tool for measuring, analysing and comparing gas costs of EVM operations across different implementations. The reproducibility is the key to the research. We have provided a complete setup guide and tooling to make the execution of the benchmarks as easy as possible.

The result of the analysis is a new gas cost schedule.

## Research progress

The project is divided into stages. The progress of each stage is described in the corresponding document:
 - [Stage I](docs/report_stage_i.md) - Initial research and methodology proposal
 - [Stage II](docs/report_stage_ii.md) - Benchmarking and data collection
 - [Stage III](docs/report_stage_iii.md) - Data analysis and report generation
 - [Stage IV](docs/report_stage_iv.md) - Comprehensive analysis of the gas cost and reproducibility (work in progress)
 - Stage V - Improved tooling and report generation (planned)

## Introduction and project scope

### EVM Implementations
We have included the following EVM implementations in the research:
- EvmOne
- Go Ethereum
- Erigon
- EthereumJS
- Nethermind
- Revm
- Besu

More implementations can be added in the future, depending on the community feedback, implementation maturity and availability of the resources.

### Measured OPCODEs and precompiles
We measure all OPCODEs together with the precompiles as of hard fork Cancun.

### Tooling and automation
The release contains precompiled binaries for easy execution. The binaries are available for Linux x64, MacOS x64 and Windows.

Additionally, we provide a complete setup guide to compile the EVM implementations and run the benchmarks.

## Quick start

If you plan to compile and run benchmarks on your own, you need the following tools installed:
- Python 3.8+
- Go 1.22.8+
- Rust 1.80.0+
- Node.js 18.0.0+
- .NET 7.0+
- Java 8.0.0+

You can use [setup_tools.sh](src/instrumentation_measurement/setup_tools.sh) script to install the required tools on Linux.

To download and compile the EVM implementations, run the following commands:
```bash
./src/instrumentation_measurement/setup_clients.sh
```

If your configuration is different, follow the steps in the script. The end results should be the same - you should have all the EVM implementations compiled and copied to the `../gas-cost-estimator-clients/build` directory.

To run the benchmarks, use the provided Python script:
```bash
python3 ./src/instrumentation_measurement/measurements.py measure --input_file ./src/stage4/pg_marginal_full5_c50_step5_shuffle.csv --evm evm_name --sample_size 10
```
Where `evm_name` is the name of the EVM implementation you want to measure.
