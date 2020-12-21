import pandas
import csv

temp = 70
hum = 90

#for use in python operations
dict =  {"temp": [int(temp)], "humid": [int(hum)]}

#load dict into dataframe
df = pandas.DataFrame(dict)

#.csv write
df.to_csv('/home/pi/Documents/sensor_data.csv', sep='\t', header=None, mode='a')

