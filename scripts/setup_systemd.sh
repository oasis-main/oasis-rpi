#!/bin/sh -e

echo "Creating systemd unit file..."
printf "
[Unit]
Description=oasis-grow startup script w/ permissions & virtualenv
[Service]
ExecStart= /bin/sh /home/pi/oasis-grow/start.sh  #in this line specify the path to the script.
[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/oasis-grow.service

sudo systemctl enableoasis-grow
sudo systemctl startoasis-grow
sudo systemctl statusoasis-grow
