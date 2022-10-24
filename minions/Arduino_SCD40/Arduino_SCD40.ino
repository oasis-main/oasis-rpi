#include <Arduino.h>
#include <SensirionI2CScd4x.h>
#include <Wire.h>

SensirionI2CScd4x scd4x;

void printUint16Hex(uint16_t value) {
    //Serial.print(value < 4096 ? "0" : "");
    //Serial.print(value < 256 ? "0" : "");
    //Serial.print(value < 16 ? "0" : "");
    //Serial.print(value, HEX);
}

void printSerialNumber(uint16_t serial0, uint16_t serial1, uint16_t serial2) {
    //Serial.print("Serial: 0x");
    printUint16Hex(serial0);
    printUint16Hex(serial1);
    printUint16Hex(serial2);
    //Serial.println();
}

void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);
    while (!Serial) {
        delay(100);
    }

    Wire.begin();

    uint16_t error;
    char errorMessage[256];

    scd4x.begin(Wire);

    // stop potentially previously started measurement
    error = scd4x.stopPeriodicMeasurement();
    if (error) {
        //Serial.print("Error trying to execute stopPeriodicMeasurement(): ");
        errorToString(error, errorMessage, 256);
        //Serial.println(errorMessage);
    }

    uint16_t serial0;
    uint16_t serial1;
    uint16_t serial2;
    error = scd4x.getSerialNumber(serial0, serial1, serial2);
    if (error) {
        //Serial.print("Error trying to execute getSerialNumber(): ");
        errorToString(error, errorMessage, 256);
        //Serial.println(errorMessage);
    } else {
        printSerialNumber(serial0, serial1, serial2);
    }

    // Start Measurement
    error = scd4x.startPeriodicMeasurement();
    if (error) {
        //Serial.print("Error trying to execute startPeriodicMeasurement(): ");
        //errorToString(error, errorMessage, 256);
        //Serial.println(errorMessage);
    }

    //Serial.println("Waiting for first measurement... (5 sec)");
}

void loop() {
  uint16_t error;
    char errorMessage[256];

    delay(5000);

    // Read Measurement
    uint16_t co2;
    float temperature;
    float humidity;
    error = scd4x.readMeasurement(co2, temperature, humidity);
    if (error) {
        //Serial.print("Error trying to execute readMeasurement(): ");
        //errorToString(error, errorMessage, 256);
        //Serial.println(errorMessage);
    } else if (co2 == 0) {
        //Serial.println("Invalid sample detected, skipping.");
    } else {
        Serial.print("{")
        Serial.print("\"temperature\":");
        Serial.print((double(temperature)*double(1.8))+double(32));
        Serial.print(", ");
        
        Serial.print("\"humidity\": ");
        Serial.print(humidity);
        Serial.print(", ");
        
        Serial.print("\"co2\": ");
        Serial.print(co2);
        //Serial.print(", "); //no trailing comma, this is the last json field
    
        Serial.print("}"); //close the json and issue new line
        Serial.println();
    }
}
  
