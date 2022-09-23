import os
import csv
from scipy.stats import bernoulli, uniform

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
    
        
    sim_temp = float()
    sim_hum = float()
    sim_vpd = float()
    sim_level = float()
    sim_co2 = float()
    sim_lux = float()
    sim_ph = float()
    sim_moisture = float()
    sim_tds = float()
    
    while True:
        
        sim_temp = float() #normdist mean 70
        sim_hum = float() #normdist mean 50
        sim_vpd = float() 
        sim_level = bernoulli(0.1) #always 0
        sim_co2 = float() #normdist 400ppm
        sim_lux = float() #normdist 500lux
        sim_ph = uniform(6.0,8.0) #uniform 6-8 
        sim_moisture = float() #normdist mean 50
        sim_tds = float() #normdist 300ppm
    
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