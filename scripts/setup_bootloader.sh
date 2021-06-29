sudo chmod +w /etc/rc.local
sudo sed -ie "/^fi/a \n/home/pi/oasis-grow/bin/activate\npython3 /home/pi/oasis-grow/controller.py &" /etc/rc.local