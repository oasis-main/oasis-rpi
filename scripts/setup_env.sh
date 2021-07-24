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
echo "Installing python3.9 modules via pip..."
wget https://apache.bintray.com/arrow/ubuntu/apache-arrow-archive-keyring-latest-focal.deb
sudo apt install ./apache-arrow-archive-keyring-latest-focal.deb
sudo apt install libarrow-dev libarrow-python-dev
ARROW_HOME=/usr PYARROW_CMAKE_OPTIONS="-DARROW_ARMV8_ARCH=armv8-a"
sudo python3.9 -m pip install streamlit
