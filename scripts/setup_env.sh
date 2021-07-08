#!/bin/sh -e

echo "This environment is built for the Raspi OS release 2021-05-07-raspios-buster-armhf-lite."

echo "Adding OS packages..."
sudo apt install -y wget software-properties-common build-essential libnss3-dev zlib1g-dev libgdbm-dev libncurses5-dev libssl-dev libffi-dev libreadline-dev libsqlite3-dev libbz2-dev
sudo apt-get install -y libopenjp2-7
sudo apt-get install -y libtiff5
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev

echo "Building Python Environment (3.8.9)..."
wget https://www.python.org/ftp/python/3.8.9/Python-3.8.9.tgz
tar xvf Python-3.8.9.tgz
cd Python-3.8.9/
./configure --enable-optimizations
sudo make altinstall
python3.8 -V

echo "Pointing all python3 to python3.9..."
alias python3=python3.8
alias pip3=pip3.8
echo "alias python3=python3.8" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc
echo "alias pip3=pip3.8" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc

echo "Configuring PATH variable..."
echo "export PATH=/home/pi/.local/bin:$PATH/" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc

echo "Installing Python modules..."
cd ..
python3.8 -m pip install --upgrade pip
python3.8 -m pip install -r /home/pi/oasis-grow/requirements.txt

echo "Building RPi.GPIO from source..."
sudo apt-get install python-dev python3-dev -y
sudo apt-get install mercurial -y
sudo apt-get remove python-rpi.gpio python3-rpi.gpio -y
python3.8 -m pip install hg+http://hg.code.sf.net/p/raspberry-gpio-python/code#egg=RPi.GPIO
