#/bin/sh -e

echo "Validating python packages..."
if ! [ -d "/usr/local/lib/python3.9/site-packages/requests" ]; then
    echo "package 'requests' not found"
    exit 1
fi

echo "Checking network connectivity..."
wget -q --spider http://google.com

if [ $? -eq 0 ]; then
    echo "Network is online"
else
    echo "Network is offline"
    exit 2
fi