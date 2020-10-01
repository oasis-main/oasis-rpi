#include <Wire.h>
#include <Adafruit_AM2315.h>

// Connect RED of the AM2315 sensor to 5.0V
// Connect BLACK to Ground
// Connect WHITE to i2c clock (A5)
// Connect YELLOW to i2c data (A4)

Adafruit_AM2315 am2315; // intiialize sensor

int waterLevelPin = 2;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    delay(10);
  }
  
  if (! am2315.begin()) {
     Serial.println("Sensor not found, check wiring & pullups!");
     while (1);
  }

  pinMode(waterLevelPin, INPUT_PULLUP);
}

// Next add 

void loop() {
  float temperature, humidity;
  int waterLow;

  if (! am2315.readTemperatureAndHumidity(&temperature, &humidity)) {
    temperature = -1;
    humidity = -1;
    return;
  }

  if (digitalRead(waterLevelPin) == LOW)
  {
    waterLow = 0;
  }

  if (digitalRead(waterLevelPin) == HIGH)
  {
    waterLow = 1;
  }
  
  Serial.print(humidity);
  Serial.print(" "); 
  Serial.print(temperature*(1.8)+32); //need to manually adjust the sensor smh
  Serial.print(" ");
  Serial.print(waterLow);
  Serial.println(); 

  delay(2000);
}
