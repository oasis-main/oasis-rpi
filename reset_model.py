import json

with open('/home/pi/device_state.json', 'r+') as d:
                        data = json.load(d)
                        data['connected'] = "0" # <--- reset to 0
                        data['running'] = "0"
                        data['LEDstatus'] = "off"
                        data['LEDtimeon'] = "0"
                        data['LEDtimeoff'] = "0"
                        data['AccessPoint'] = "0"
                        data['awaiting_update'] = "0"
                        d.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, d)
                        d.truncate() # remove remaining part
d.close()

with open('/home/pi/logs/growCtrl_log.json', 'r+') as l:
                        data = json.load(l)
                        data['last_start_mode'] = "fresh, no run history" # <--- reset to
                        l.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, l)
                        l.truncate() # remove remaining part
l.close()

with open('/home/pi/grow_params.json', 'r+') as g:
                        data = json.load(g)
                        data["targetT"] = "70"
                        data["targetH"] = "90"
                        data["targetL"] = "on"
                        data["LtimeOn"] = "8"
                        data["LtimeOff"] = "22"
                        data["lightInterval"] = "60"
                        data["cameraInterval"] = "3600"
                        data["waterMode"] = "off"
                        data["waterDuration"] = "60"
                        data["waterInterval"] =  "3600"
                        g.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, g)
                        g.truncate() # remove remaining part
g.close()

