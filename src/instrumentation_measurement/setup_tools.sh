# install .NET 7.0
wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
chmod +x ./dotnet-install.sh
./dotnet-install.sh --channel 7.0
rm ./dotnet-install.sh

# install go
sudo snap install go --classic

# install rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh


