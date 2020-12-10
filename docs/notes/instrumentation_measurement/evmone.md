## Evmone


### Installation and running

1. Building
    ```
    mkdir build
    git submodule update --init
    cd build
    cmake .. -DEVMONE_TESTING=ON
    cmake --build . -- -j
    ```
    
    I got compile errors because of old gcc not supporting C++17
    1. https://askubuntu.com/questions/466651/how-do-i-use-the-latest-gcc-on-ubuntu/1163021#1163021
    2. then:
    ```
    sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 10
    sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-8 10
    ```
2. Running

    From the `build` directory:
    ```
    evmc/bin/evmc run --vm ./lib/libevmone.so [--print-opcodes] [--measure-all] [--measure-total] [--measure-one <instruction number>] [--repeat <number of repetitions>] <bytecode> 
    ```
    for example:
    ```
    evmc/bin/evmc run --vm ./lib/libevmone.so --print-opcodes --measure-all --measure-one 3 --repeat 2 602060070260F053600160F0F3
    ```
### Comments
* evmone adds `5B` (`JUMPDEST`) instruction in the beginning 


### Rough notes

1. Probably not a good fit to meausure, only instrumentation
    - TODO: compare instrumentation with one used with the Broken Metre (aleth fork) implementation
2. EVMC API - these are tools that go with the EVMONE VM implementation.
    1. under `/build/evmc/bin/evmc run --help` one finds help about how to run bytecode
    2. trying `evmc/bin/evmc run 0x60` - this is `PUSH1`, check out https://www.ethervm.io/#60
        1. PUSH 20
        2. PUSH 07
        3. MUL
        4. PUSH F0 (offset)
        5. MSTORE8
        6. PUSH 01 (length)
        7. PUSH F0 (offset)
        8. RETURN
        9. `evmc/bin/evmc run --vm ./lib/libevmone.so 602060070260F053600160F0F3`, nice
    
