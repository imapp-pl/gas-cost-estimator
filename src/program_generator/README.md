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

#### Use together with `instrumentation_measurement` geth tools

From `src`

```
export GOPATH=
export GOGC=off
export GO111MODULE=off
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

### Versions

Generate programs containing arithmetic operations

```
python3 program_generator/pg_arythmetic.py generate --count=2 --gasLimit=100 --seed=123123123
```

- The parameter `--fullCsv` works as well. All parameters are optional. 
- The parameter `count` is the number of expected programs.
- The parameter `seed` is the seed of randomness, optional.
- A single program can be limited by `gasLimit`, `opsLimit`, `bytecodeLimit`. The default is `opsLimit=100`.
- The (optional) dominant is the opcode draw with probability ~0.5, for example `--dominant=0x06`.
- The program generator uses `push32` to populate random values. This can be altered by `--push=16` for instance.
- The flag `--cleanStack` pushes new values on the stack for every opcode execution.

Generate programs containing stack operations

```
python3 program_generator/pg_stack.py generate --count=1 --gasLimit=1000 --seed=123123123 --max=128 --min=1
```

A parameter `--fullCsv` works as well. All parameters are optional.
Parameters `min` and `max` refer to the stack size.
