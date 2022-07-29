#/bin/sh -e

echo "Checking Python 3.7 Venv Install..."
/usr/bin/env python3.7 --version
if ! [ $? -eq 0  ]; then
    echo "python3.7 virtualenv not found"
fi

echo "Checking Python 3.7 Venv Packages..."
for packageName in serial, setuptools, Cython, firebase, pyrebase, python_jwt, gcloud, sseclient, pycairo, requests, requests-toolbelt, pickle5, pyserial, Pillow, RPi.GPIO, opencv-python, streamlit; do
    if ! [ -d "/home/pi/oasis-grow_venv/lib/python3.7/site-packages/$packageName" ]; then
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