// Sensor Sketch for Oasis Grow Device

// REQUIRES the following Arduino libraries:
// - DHT Sensor Library: https://github.com/adafruit/DHT-sensor-library
// - Adafruit Unified Sensor Lib: https://github.com/adafruit/Adafruit_Sensor

#include "DHT.h"

#define DHTPIN 2     // Digital pin connected to the DHT sensor
// Feather HUZZAH ESP8266 note: use pins 3, 4, 5, 12, 13 or 14 --
// Pin 15 can work but DHT must be disconnected during program upload.

// Uncomment whatever type you're using!
//#define DHTTYPE DHT11   // DHT 11
#define DHTTYPE DHT22   // DHT 22  (AM2302), AM2321
//#define DHTTYPE DHT21   // DHT 21 (AM2301)
//DHT22 setup:
// Connect pin 1 (on the left) of the sensor to +5V
// NOTE: If using a board with 3.3V logic like an Arduino Due connect pin 1
// to 3.3V instead of 5V!
// Connect pin 2 of the sensor to whatever your DHTPIN is
// Connect pin 4 (on the right) of the sensor to GROUND
// Connect a 10K resistor from pin 2 (data) to pin 1 (power) of the sensor

// Initialize DHT sensor (temp & hum)
DHT dht(DHTPIN, DHTTYPE);

//Initialize GY-30 sensor (lux)
#include <Wire.h>
int BH1750_address = 0x23; // i2c Addresses
byte buff[2];

void setup() {
  Wire.begin(); //start wire
  BH1750_Init(BH1750_address); //start GY-30 on i2c
  delay(200); //wait so nothing weird happens
  Serial.begin(9600); //start the serial monitor
  dht.begin(); //start DHT
  
}

void loop() {
  // Wait a few seconds between measurements.
  delay(1000);

  //DHT-22
  // Reading temperature or humidity takes about 250 milliseconds!
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  //float t = dht.readTemperature();
  // Read temperature as Fahrenheit (isFahrenheit = true)
  float f = dht.readTemperature(true);

  //GY-30
  float valf=0;
  float l = 0;
  if(BH1750_Read(BH1750_address)==2){
    
    valf=((buff[0]<<8)|buff[1])/1.2;
    
    if(valf<0) l = -1;
    else l = (int)valf; 
  }


  //define edge cases for faulty readings
  if (isnan(h)){
    h=-1;
  }
  if (isnan(f)){
    f=-1;
  }

  Serial.print(h);
  Serial.print(' ');
  Serial.print(f);
  Serial.print(' ');
  Serial.println(l);

}

void BH1750_Init(int address){
  
  Wire.beginTransmission(address);
  Wire.write(0x10); // 1 [lux] aufloesung
  Wire.endTransmission();
}

byte BH1750_Read(int address){
  
  byte i=0;
  Wire.beginTransmission(address);
  Wire.requestFrom(address, 2);
  while(Wire.available()){
    buff[i] = Wire.read(); 
    i++;
  }
  Wire.endTransmission();  
  return i;
}
