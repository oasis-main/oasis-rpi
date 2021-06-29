sudo chmod +w /etc/rc.local
sed -ie "/^fi/a /home/pi/oasis-grow/bin/activate\npython3 controller.py &" /etc/rc.local