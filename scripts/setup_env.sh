echo "Adding packages..."
sudo apt install -y python3-pip
sudo apt-get install -y libopenjp2-7
sudo apt-get install -y libtiff5
sudo apt-get install -y libatlas-base-dev

pip3 install firebase pyrebase python_jwt gcloud sseclient requests-toolbelt pickle5 pandas pyserial Pillow