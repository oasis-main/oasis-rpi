#!/bin/sh -e

echo "This environment is built for the Raspi OS release 2021-05-07-raspios-buster-armhf-lite."

echo "Adding OS packages..."
sudo apt install -y wget software-properties-common build-essential libnss3-dev zlib1g-dev libgdbm-dev libncurses5-dev libssl-dev libffi-dev libreadline-dev libsqlite3-dev libbz2-dev liblzma-dev
sudo apt-get install -y libopenjp2-7
sudo apt-get install -y libtiff5
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev
sudo apt-get install -y cmake
sudo apt-get install -y ntp

echo "Activating NTP & setting local time to America/New_York"
sudo timedatectl set-ntp true
sudo timedatectl set-timezone America/New_York

echo "Configuring PATH variable..."
echo "export PATH=/home/pi/.local/bin:$PATH/" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc

echo "Installing pip3 & Python 3.7 modules..."
sudo apt install python3-pip -y
python3 -m pip install -r /home/pi/oasis-grow/requirements.txt

echo "Installing python 3.7 RPi.GPIO for OS..."
sudo apt-get -y install python3-rpi.gpio

echo "Installing streamlit to root so python can edit wpa_supplicant.conf.."
sudo pip3 install streamlit==0.62.0
