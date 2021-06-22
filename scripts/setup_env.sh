echo "Adding packages..."
sudo apt install -y python3-pip
sudo apt-get install -y python3-venv
sudo apt-get install -y libopenjp2-7
sudo apt-get install -y libtiff5
sudo apt-get install -y libatlas-base-dev

echo "Creating virtual environment..."
python3 -m venv /home/pi/oasis-grow
source /home/pi/oasis-grow/bin/activate

echo "Configuring PATH variable..."
echo "export PATH=\"home/pi/.local/bin:$PATH\"" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc

echo "Installing modules..."
pip3 install -r /home/pi/oasis-grow/requirements.txt
