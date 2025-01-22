# Report reproducibility

Reproducibility is a key aspect of any research. It allows other researchers to verify the results of a study and to build upon them.

This document describes how to reproduce the measurements, analysis and final reports contained in the project. There are two aspects of the project replication: data and reports. They can be executed independently, i.e. researchers can use the provided data to run their analysis and generate reports. Alternatively, they can use the provided report generators to automatically analyze their data.

## Measurement data

The original benchmarks were executed on a reference machine with the following specifications:
- Intel® Core™ i5-13500
- 64 GB DDR4
- 2 x 512 GB NVMe SSD
- Ubuntu 22.04

The following EVM implementations were used: EvmOne, Go Ethereum, Erigon, EthereumJS, Nethermind, Revm and Besu.

Execution of your benchmarks might have the following aims:
- Reproduce and verify the results of the project
- Run benchmarks on a different machine architecture or setup
- Add more EVM implementations
- Benchmark the same EVM implementations, but under different versions or configurations

Whatever your goals might be, we provide a framework that you can use to execute benchmarks and generate data.

### Convetions and data format

The data is stored in CSV files. File names follow the pattern `<content_type>-<measurement_type>-<group>-<client>.csv`. Where each field might take the following values:
- `content_type`: `pg`, `results`, `estimated_cost`
- `measurement_type`: `marginal`, `arguments`
- `group`: `full`, `precompiles`, `mem`, `create`, `stop`, etc
- `client`: `evmone`, `geth`, `erigon`, `ethereumjs`, `nethermind`, `revm`, `besu`

For example the file `pg_arguments_precompiles.csv` contains program generated using arguments method for precompiles. And `results_marginal_full_geth.csv` contains results of the marginal benchmark for the full group using the Geth client. Finally `estimated_cost_marginal_mem_evmone.csv` would contain calculated estimated cost for the EvmOne client.

The columns in the CSV files are as follows:
- `pg_marginal`: program_id,opcode,op_count,bytecode
- `pg_arguments`: program_id,opcode,op_count,arg0,arg1,arg2,bytecode
- `results`: program_id,sample_id,total_time_ns + optional columns like mem_allocs, mem_alloc_bytes, iterations_count, std_dev_time_ns, depending on a client
- `estimated_cost`: op,estimate_marginal_ns,estimate_marginal_ns_stderr,env

Keeping the same conventions will allow you to use the provided scripts to generate reports and easier shareing with other researchers.

### Gas Cost Estimator Releases

To simplify the reproduction process we provide pre-built binaries of the EVM implementations. They come in the form of 'releases' and can be found in [https://github.com/imapp-pl/gas-cost-estimator/releases](https://github.com/imapp-pl/gas-cost-estimator/releases).

Using them could not be simpler, just download the release for your target platform and extract the data. First, run `measure_test.sh` to check if the binaries work on your machine. This will run a simple test to check if the binaries are working correctly. If the test passes, you can proceed to running benchmarks. Note: not all platforms are fully supported yet, we will add more binaries in the future.

Now you are ready to run benchmarks by executing the `measure_full.sh` script. Be careful, this might take a few days to complete! Edit the script to run different program bytecodes. The folder `gas-cost-estimator/src/stage4` contains programs that were used in the project.

### Local compilation

To build the EVM implementations yourself, your environment needs to have the dependencies installed as required for each client. The script `setup_tools.sh` guides you through the process, but it might require some manual intervention. Refer to the EVM implementation documentation for more details.

The script `setup_clients.sh` downloads and compiles the EVM implementation used in this project. Edit the script to add more clients or change the versions. By default, the binaries are stored in the `gas-cost-estimator-clients` folder, next to the existing `gas-cost-estimator`. As you can see in the script sometimes we used our forks that enable benchmarking. You can find them in the `imapp-pl` organization on GitHub. We intend to include all the necessary changes in the upstream repositories in the future.

### Program Generation

The folder `src/stage4` contains programs that were used in the project, but you can create your own. We have provided handy generators in the `src/program_generator` folder. All programs used in the project were generated using these tools. Examples:

To generate marginal programs with all defaults use:

```shell
python3 ./src/program_generator/pg_marginal.py generate
```

You can customize the output with the following options:
```shell
python3 ./src/program_generator/pg_marginal.py generate --stepOpCount 1 --maxOpCount 100 --selectionFile selection_stop.csv
```

The selection file selects a group of opcodes. You can find more selection files in `src/program_generator/data`

To generate programs for the precompiles use:
```shell
python3 ./src/program_generator/pg_precompiles.py generate
python3 ./src/program_generator/pg_arguments.py generate
python3 ./src/program_generator/pg_arguments_precompiles.py generate
python3 ./src/program_generator/pg_validation.py generate
```
They all use the same parameters. Both arguments and validation produce very large files. You might want to review before running benchmarks.

All outputs are directed to the console, so you might want to redirect them to a file. Assuming you are in a parent folder:
```shell
python3 gas-cost-estimator/src/program_generator/pg_marginal.py generate > local/pg_marginal_full.csv
```

### Running benchmarks

We used native benchmark tools for each client. As such they tend to differ in terms of executing options, output format and so on. The script `measurements.py` contains the logic to run benchmarks for each client.

The example usage:
```shell
python3 gas-cost-estimator/src/instrumentation_measurement/measurements.py measure --input_file local/pg_marginal_full.csv --evm evmone --sample_size 10 > local/results_marginal_full_evmone.csv
```

You can use the same `measurements.py` to execute any program generated by `pg_` scripts. The `sample_size` option indicates how many times each line should be benchmarked. The `evm` of course selects the EVM implementation. The output is directed to the console, so you might want to redirect it to a file.

Edit the file `measurements.py` to add more clients or change client-specific options. By default, the binaries are stored in the `gas-cost-estimator-clients` folder, next to the existing `gas-cost-estimator`. You can change the binary location with the `exec_path` option.

## Report generation

For each client, we have two kinds of reports: marginal and arguments. Then there is a final report that combines all the data. The reports are generated using R notebooks. The notebooks are located in the `src/analysis` folder. You can run them in RStudio.

### Automated report generation

For your convenience, we have provided scripts that generate the reports automatically. This requires Docker to run.

First, build the Docker image:

```shell
docker build . -f Dockerfile.reports -t imapp-pl/gas-cost-estimator/reports:4.0
```

Then you can generate reports:
```shell
generate_marginal.sh ../local/results_marginal_full_evmone.csv
generate_arguments.sh ../local/results_arguments_full_evmone.csv
generate_final.sh ../local/results*.csv
```
