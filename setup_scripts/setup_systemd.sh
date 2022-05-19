#!/bin/sh -e

echo "Creating systemd unit file..."
printf "
[Unit]
Description=Starts Oasis-X Firmware

[Service]
ExecStart= /bin/sh /home/pi/oasis-grow/start.sh  #in this line specify the path to the script.
StandardOutput=journal+console
StandardError=inherit

[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/oasis-grow.service

sudo systemctl enable oasis-grow
sudo systemctl start oasis-grow
sudo systemctl status oasis-grow

#References
#https://stackoverflow.com/questions/37585758/how-to-redirect-output-of-systemd-service-to-a-file
#DefaultDependencies=false
#Type=simple
