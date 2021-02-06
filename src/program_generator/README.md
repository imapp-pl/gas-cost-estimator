## Program generator

### Installation

```
virtualenv --python=python3 ~/.venv/gce
source ~/.venv/gce/bin/activate
pip install -r requirements.txt
```

### Usage

```
python3 program_generator.py generate --help
```

#### Use together with `instrumenter.go`

From `src`

```
export GOPATH=
export GOGC=off
python3 program_generator/program_generator.py generate | xargs -L1 go run ./instrumentation_measurement/geth/main.go --bytecode
```

#### (Ewasm) use together with `openethereum-evm`

From `src`

```
# ensure `wabt` binaries are in PATH
# ensure `parity-evm` binaries are in PATH
python3 program_generator/program_generator.py generate --ewasm | xargs -L1 parity-evm --gas 5000 --chain ../../openethereum/ethcore/res/instant_seal.json --code
```

#### Use together with `measurements.py`

From `src`

(`go` exports as above)

```
python3 program_generator/program_generator.py generate --fullCsv | python3 instrumentation_measurement/measurements.py measure --sampleSize=50 --nSamples=4 > ../../result_geth.csv
```

or similar.
