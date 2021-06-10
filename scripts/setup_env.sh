echo "Removing unnecessary packages..."
sudo apt-get purge --auto-remove gvfs-backends gvfs-fuse

echo "Cloning repositories..."
cd ~
git clone https://github.com/oasis-gardens/oasis-grow.git
cd oasis-grow

echo "Adding packages..."
pip3 install firebase pyrebase python_jwt gcloud sseclient requests-toolbelt pickle5 pandas pyserial Pillow