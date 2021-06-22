sudo chmod +x /home/pi/oasis-grow/scripts/setup_env.sh
source /home/pi/oasis-grow/scripts/setup_env.sh
sudo chmod +x /home/pi/oasis-grow/scripts/setup_config.sh
source /home/pi/oasis-grow/scripts/setup_config.sh
sudo chmod +x /home/pi/oasis-grow/scripts/setup_network.sh
source /home/pi/oasis-grow/scripts/setup_network.sh

while getopts ":a:" opt; do
    case $opt in
        b)
            echo "Setting up grow_ctrl bootloader..."
            printf "
            sudo source /home/pi/oasis-grow/bin/activate
            sudo python3 /home/pi/oasis-grow/controller.py &
            " | sudo tee -a /etc/rc.local
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
            ;;
    esac
done