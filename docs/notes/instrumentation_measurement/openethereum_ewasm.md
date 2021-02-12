# Instrumentation and measurement using `OpenEthereum` with Ewasm

1. OpenEthereum currently seems to use a relatively old version of (`wasmi`)[https://github.com/paritytech/wasmi] - [`0.3.0`](https://github.com/paritytech/wasmi/tree/0.3), our changes branch off of that (https://github.com/paritytech/wasmi/compare/master...imapp-pl:time_measurement)
1. Useful reading about Wasm vs `wasmi`/Ewasm: https://github.com/paritytech/wasmi/blob/0.3/src/isa.rs
    - the instruction set (e.g. what is printed out in the instrumentation loop) is there, e.g. `I32Add`...
2. Wasm bytecode starts with: `WASM_BINARY_MAGIC + WASM_BINARY_VERSION` = `0061736d01000000`
3. https://webassembly.github.io/spec/core/appendix/index-instructions.html - another listing of instructions with stack requirements
4. Decode Wasm binary format from hex:
    ```
    cat wasm.example | python3 -c "import sys, binascii; sys.stdout.buffer.write(binascii.unhexlify(input().strip()))" > wasm.example.bin
    ```
    - this can then be loaded to [`wasm2wat`](https://webassembly.github.io/wabt/demo/wasm2wat/) (see below for WABT)

### `chfast` notes


```
(func (export "call"))
```

```
(module
  (func (export "call")
    i32.const 2
    i32.const 2
    i32.add
    drop
  )
)
```

```
(module
  (func (export "call")
    (call "useGas" 4)
    i32.const 2
    i32.const 2
    i32.add
    drop
  )
)
```

wabt
https://pengowray.github.io/wasm-ops/
https://webassembly.studio

https://github.com/ewasm/design/blob/master/metering.md
https://github.com/ewasm/design/blob/master/determining_wasm_gas_costs.md

### WABT

1. It installed as documented in gh for me

#### Integrate to measurements

Execute everything from the dir where you have `wabt` and `openethereum` repos, and `example.wat`
2. Generate hex bytecode
    ```
    wabt/build/wat2wasm example.wat && cat example.wasm | hexdump -ve '1/1 "%02x"' && echo
    ```
3. Generate hex bytecode from wat and execute
    ```
    wabt/build/wat2wasm example.wat && \
      cat example.wasm | \
      hexdump -ve '1/1 "%02x"' | \
      xargs -L1 \
        openethereum/target/release/parity-evm \
          --gas 5000 \
          --chain openethereum/ethcore/res/instant_seal.json \
          --code
    ```
