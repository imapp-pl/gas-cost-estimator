# Running with program generator
From `instrumentation_measurement` directory:

```
python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --sampleSize=50 --nSamples=3 > ../../geth.csv
```
    
By default programs are executed in geth. To change EVM specify `--evm` parameter:

```
python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --sampleSize=50 --nSamples=3 --evm evmone > ../../evmone.csv
```

### Running measurements via `docker`

From the repo root.

Build (pick tag name as desired):
```
sudo docker build -t measurements-geth -f Dockerfile.geth .
```

Run:
```
sudo docker run --rm --privileged --security-opt seccomp:unconfined \
  -it measurements-geth \
  sh -c "cd src && python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --sampleSize=5 --nSamples=1"
```

For other EVMs use respective `Dockerfile`s and use the `--evm` flag on the `measure` command, e.g. `measure --evm openethereum`
