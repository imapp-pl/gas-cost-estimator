# Running with program generator
    From `instrumentation_measurement` directory:
    ```
    python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --sampleSize=50 --nSamples=3 > ../../geth.csv
    ```
    
    By default programs are executed in geth. To change EVM specify `--evm` parameter:
    ```
    python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --sampleSize=50 --nSamples=3 --evm evmone > ../../evmone.csv
    ```