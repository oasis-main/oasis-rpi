echo "Adding packages..."
sudo apt install -y python3-pip
sudo apt-get install -y libopenjp2-7
sudo apt-get install -y libtiff5
sudo apt-get install -y libatlas-base-dev

echo "Configuring PATH variable..."
echo "export PATH=\"home/pi/.local/bin:$PATH" | sudo tee -a /home/pi/.bashrc

echo "Installing modules..."
pip3 install firebase pyrebase python_jwt gcloud sseclient requests-toolbelt pickle5 pandas pyserial Pillow