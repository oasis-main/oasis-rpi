import os
import csv

#write some data to a .csv, takes a dictionary and a path
def write_csv(filename, dict): #Depends on: "os" "csv"
    file_exists = os.path.isfile(filename)

    with open (filename, 'a') as csvfile:
        headers = ["time"]
        
        headers.append("temperature")

        headers.append("humidity")

        headers.append("co2")

        headers.append("soil_moisture")

        headers.append("vpd")

        headers.append("water_low")

        headers.append("lux")

        headers.append("ph")

        headers.append("tds")

        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        variables = {}

        for variable in dict.keys():
            if variable in headers:
                variables[variable] = dict[variable]

        writer.writerow(variables)

        writer = None

    return

if __name__ == "__main__":
    while True:
        
        sim_temp = float()
        sim_hum = float()
        sim_vpd = float()
        sim_level = float()
        sim_co2 = float()
        sim_lux = float()
        sim_ph = float()
        sim_moisture = float()
        sim_tds = float()
        
        payload = {"temperature": sim_temp,
                    "humidity": sim_hum,
                    "vpd": sim_vpd,
                    "water_low": sim_level,
                    "co2": sim_co2,
                    "lux": sim_lux,
                    "ph": sim_ph,
                    "soil_moisture": sim_moisture,
                    "tds": sim_tds}
        
        write_csv("sensor_data.csv",payload)