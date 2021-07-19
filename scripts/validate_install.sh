#/bin/sh -e

echo "Validating python packages..."


echo "Checking network connectivity..."
wget -q --spider http://google.com

if [ $? -eq 0 ]; then
    echo "Online"
else
    echo "Offline"
fi