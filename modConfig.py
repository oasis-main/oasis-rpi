import json
import sys

#update access_config.json
def modAccessConfig(wak, local_id, id_token):
    data = {}
    data["wak"] = str(wak)
    data["local_id"] = str(local_id)
    data["id_token"] = str(id_token)

    with open("/home/pi/access_config.json", "w") as outfile:
        json.dump(data, outfile)

#update wpa_supplicant.conf
def modWifiConfig(SSID, password):
    config_lines = [
    'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev',
    'update_config=1',
    'country=US',
    '\n',
    'network={',
    '\tssid="{}"'.format(SSID),
    '\tpsk="{}"'.format(password),
    '\tkey_mgmt=WPA-PSK',
    '}'
    ]

    config = '\n'.join(config_lines)
    #print(config)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "r+") as wifi:
        wifi.seek(0)
        wifi.write(config)
        wifi.truncate()

    print("Wifi config added")

#enter in order: wifi name, wifi pass, wak, local_id, id_token
modWifiConfig(str(sys.argv[1]), str(sys.argv[2]))
modAccessConfig(str(sys.argv[3]), str(sys.argv[4]), str(sys.argv[5]))

