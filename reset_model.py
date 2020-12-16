import json

with open('/home/pi/device_state.json', 'r+') as d:
                        data = json.load(d)
                        data['connected'] = "0" # <--- reset to 0
                        data['running'] = "0"
                        data['LEDstatus'] = "off"
                        data['LEDtimeon'] = "0"
                        data['LEDtimeoff'] = "0"
                        data['AccessPoint'] = "0"
                        d.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, d)
                        d.truncate() # remove remaining part

with open('/home/pi/logs/growCtrl_log.json', 'r+') as l:
                        data = json.load(l)
                        data['last_start_mode'] = "fresh, no run history" # <--- reset to
                        l.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, l)
                        l.truncate() # remove remaining part



