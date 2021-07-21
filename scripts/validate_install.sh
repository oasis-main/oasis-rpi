#/bin/sh -e

echo "Validating python packages..."
if ! [ -d "/usr/local/lib/python3.9/site-packages/streamlit" ]; then
    echo "'streamlit' not found, python3.9 install failed"
    exit 1
fi

for packageName in setuptools Cython numpy pandas firebase pyrebase python_jwt gcloud sseclient requests requests_toolbelt pickle5 serial PIL; do
    if ! [ -d "usr/local/lib/python3.9/site-packages/$packageName"]; then
        echo "'$packageName' not found"
        exit 1
    fi
done

echo "Checking network connectivity..."
wget -q --spider http://google.com

if [ $? -eq 0 ]; then
    echo "Online"
else
    echo "Network is offline"
    exit 2
fi