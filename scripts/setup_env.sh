#!/bin/sh -e

echo "This environment is built for the Raspi OS release 2021-05-07-raspios-buster-armhf-lite."

echo "Adding OS packages..."
sudo apt install -y wget software-properties-common build-essential libnss3-dev zlib1g-dev libgdbm-dev libncurses5-dev libssl-dev libffi-dev libreadline-dev libsqlite3-dev libbz2-dev liblzma-dev
sudo apt-get install -y libopenjp2-7
sudo apt-get install -y libtiff5
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev
sudo apt-get install -y cmake

echo "Configuring PATH variable..."
echo "export PATH=/home/pi/.local/bin:$PATH/" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc

echo "Installing pip3 & Python 3.7 modules..."
sudo apt install python3-pip -y
python3 -m pip install -r /home/pi/oasis-grow/requirements.txt

echo "Installing python 3.7 RPi.GPIO for OS..."
sudo apt-get -y install python3-rpi.gpio

echo "Installing Python 3.9..."
cd ..
wget https://www.python.org/ftp/python/3.9.6/Python-3.9.6.tgz
tar xvf Python-3.9.6.tgz
cd Python-3.9.6/
./configure  --enable-optimizations
sudo make altinstall
python3.9 -V

echo "Building pip3.9 environment..."
cd ..
sudo apt-get install python3.9-distutils
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.9 get-pip.py

echo "Build llvm-10 from source (Apache Arrow dependency)..."
echo "export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc
git clone https://github.com/llvm/llvm-project.git
cd llvm-project
git fetch --tags
git checkout llvmorg-10.0.1
mkdir build
cd build
cmake -G "Unix Makefiles" \
    -DLLVM_ENABLE_PROJECTS="clang;libcxx;libcxxabi" \
    -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_ASSERTIONS=On \
    ../llvm
make -j4
sudo make install

echo "Build Apache Arrow from source (streamlit dependency)"
wget https://github.com/apache/arrow/archive/apache-arrow-1.0.1.tar.gz
tar xzf apache-arrow-1.0.1.tar.gz
cd arrow-apache-arrow-1.0.1/cpp
mkdir build
cd build
export ARROW_HOME=/usr/local
cmake \
    -DCMAKE_INSTALL_PREFIX=$ARROW_HOME \
    -DCMAKE_INSTALL_LIBDIR=lib \
    -DARROW_WITH_BZ2=ON \
    -DARROW_WITH_ZLIB=ON \
    -DARROW_WITH_ZSTD=ON \
    -DARROW_WITH_LZ4=ON \
    -DARROW_WITH_SNAPPY=ON \
    -DARROW_PARQUET=ON \
    -DARROW_PYTHON=ON \
    -DARROW_BUILD_TESTS=OFF \
    ..
make -j4
sudo make install
cd ../../python
python3.9 setup.py build_ext --build-type=release --with-parquet
sudo python3.9 setup.py install

echo "Add LD_Preload to .bashrc..."
echo "LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1.2.0" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc

echo "Installing python3.9 modules via pip..."
sudo python3.9 -m pip install numpy==1.19.3
sudo python3.9 -m pip install streamlit
