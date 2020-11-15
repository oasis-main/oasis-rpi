import json

with open('/home/pi/device_state.json', 'r+') as r:
                        data = json.load(r)
                        data['connected'] = "0" # <--- reset to 0
                        data['running'] = "0"
                        data['LEDstatus'] = "off"
                        data['LEDtimeon'] = 8
                        data['LEDtimeoff'] = 20
                        data['AccessPoint'] = "0"
                        r.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, r)
                        r.truncate() # remove remaining part

with open('/home/pi/logs/growCtrl_log.json', 'r+') as r:
                        data = json.load(r)
                        data['last_start_mode'] = "fresh, no run history" # <--- reset to
                        r.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, r)
                        r.truncate() # remove remaining part

