#/bin/sh -e

echo "Checking python 3.7 install..."
python3.7 --version
if ! [ $? -eq 0  ]; then
    echo "python3.7 installation not found"
fi

echo "Validating python packages..."
if ! [ -d "/usr/local/lib/python3.7/site-packages/streamlit" ]; then
    echo "'streamlit' not found"
fi

if ! [ -d "/usr/lib/python3/dist-packages/requests" ]; then
    echo "'requests' not found"
elif ! [ -d "/usr/lib/python3/dist-packages/setuptools" ]; then
    echo "'setuptools' not found"
fi

for packageName in Cython numpy pandas firebase pyrebase python_jwt gcloud sseclient requests_toolbelt pickle5 serial PIL; do
    if ! [ -d "/home/pi/.local/lib/python3.7/site-packages/$packageName" ]; then
        echo "package '$packageName' not found"
    fi
done

echo "Checking network connectivity..."
wget -q --spider http://google.com

if [ $? -eq 0 ]; then

    echo "Network is online."

else
    echo "Network is offline."
fi
