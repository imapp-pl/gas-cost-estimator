package main

import (
	"fmt"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/vm/runtime"
)

func main() {
	ret, _, err := runtime.Execute(common.Hex2Bytes("602060070260F053600160F0F3"), nil, nil)
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println(ret)
}
