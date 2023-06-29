## Evmone

### Installation and running

1. Building
    ```
    mkdir build
    git submodule update --init
    cd build
    cmake .. -DEVMONE_TESTING=ON
    cmake --build . -- -j $(nproc)
    ```
    Changes related to the Gas Cost Estimator are in branch `wallclock` in both `evmone` and `evmc` git submodules.
   
2. Running

    From the `build` directory:
    ```
    evmc/bin/evmc run --vm ./lib/libevmone.so,O=0 --sample-size 2 602060070260F053600160F0F3
    ```

### Comments
* evmone adds `5B` (`JUMPDEST`) instruction in the beginning if there is none

### Notes on execution

2. The `JUMPDEST` which appears at the beginning of each program is an intrinsic opcode `BEGINBLOCK`, `evmone` specific
    - "These intrinsic instructions may be injected to the code in the analysis phase"
    - "This instruction is defined as alias for JUMPDEST and replaces all JUMPDEST instructions"
