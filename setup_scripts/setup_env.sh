#!/bin/sh -e

echo "This environment is built for the Raspi OS release 2021-05-07-raspios-buster-armhf-lite."

echo "Adding OS packages..."
sudo apt install -y wget software-properties-common build-essential libnss3-dev zlib1g-dev libgdbm-dev libncurses5-dev libssl-dev libffi-dev libreadline-dev libsqlite3-dev libbz2-dev liblzma-dev
sudo apt-get install -y libopenjp2-7
sudo apt-get install -y libtiff5
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev
sudo apt-get install -y cmake

echo "Activating NTP & setting local time to America/New_York"
sudo apt-get install -y ntp
sudo systemctl enable ntp
sudo systemctl start ntp
sudo timedatectl set-ntp true
sudo timedatectl set-timezone America/New_York

echo "Configuring PATH variable..."
echo "export PATH=/home/pi/.local/bin:$PATH/" | sudo tee -a /home/pi/.bashrc
. /home/pi/.bashrc

echo "Installing Python Env & Pkg Manager..."
sudo apt install python3-pip -y
sudo apt-get install python3-venv -y

echo "Installing Rust Compiler..."
curl https://sh.rustup.rs -sSf | sh
. "$HOME/.cargo/env"

echo "Installing Python Modules..."
python3 -m venv /home/pi/oasis-grow/oasis_venv_pi #uncomment to build env from source
. /home/pi/oasis-grow/oasis_venv_pi/bin/activate
/usr/bin/env python3 -m pip install --upgrade pip #uncomment to build env from source
/usr/bin/env python3 -m pip install -r /home/pi/oasis-grow/requirements.txt #uncomment to build env from source

echo "Installing Rust Modules..."
cd /home/pi/oasis-grow/rusty_locks
maturin build --release
cd ..

echo "Installing Python3 Root Dependencies for OS..."
sudo apt-get -y install python3-rpi.gpio #GPIO Pin Access
sudo apt install python3-opencv -y #Image Processing with GPU
sudo pip3 install orjson
sudo pip3 install click==8.0.4 streamlit==0.62.0 pickle5 pyrebase #Network Setup
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel #Raspi LED Driver 
sudo python3 -m pip install --force-reinstall adafruit-blinka #Raspi LED Driver