# install .NET 7.0
sudo add-apt-repository ppa:dotnet/backports
wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
chmod +x ./dotnet-install.sh
sudo ./dotnet-install.sh --channel 9.0
rm ./dotnet-install.sh

# install go
sudo snap install go --classic

# install rust
sudo curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# install node
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
nvm install 20
node -v
npm -v
npm i -g @vercel/ncc 

# install cmake
sudo apt-get install cmake

# install java
sudo apt-get install openjdk-21-jdk
