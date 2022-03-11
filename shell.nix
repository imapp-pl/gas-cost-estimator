with import <nixpkgs> {};

let
  python-packages = p: (with p; [ fire ]);
  python = pkgs.python39.withPackages python-packages;
in
mkShell {
  buildInputs = [
    python
    pkgs.go_1_17
    pkgs.cmake
];

  shellHook = ''
    mkdir -p ".go/src/github.com/ethereum/"
    if [ ! -f ".go/src/github.com/ethereum/" ] ; then
      ln -s $(pwd)/../go-ethereum .go/src/github.com/ethereum/
    fi

    export GOPATH="$(pwd)/.go/"
    export GO111MODULE=off
  '';
}
