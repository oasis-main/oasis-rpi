#include <ArduinoModbus.h>

#define DE_PIN 7  // Driver Enable pin for RS485

void setup() {
  Serial.begin(9600);
  pinMode(DE_PIN, OUTPUT);  // Configure DE pin as output
  
  if (!ModbusRTUClient.begin(9600)) {
    Serial.println("Failed to start Modbus RTU Client!");
  }
}

void loop() {
  //Modbus communication
  uint8_t serverId = 1;
  uint16_t address = 0;
  uint16_t value = 1234; // example data
  
  digitalWrite(DE_PIN, HIGH);  // Set RS485 to send mode
  if (ModbusRTUClient.holdingRegisterWrite(serverId, address, value) < 0) {
    Serial.println("Modbus Write Failed");
  }

  digitalWrite(DE_PIN, LOW);  // Set RS485 to receive mode
  long readValue = ModbusRTUClient.holdingRegisterRead(serverId, address);
  if (readValue < 0) {
    Serial.println("Modbus Read Failed");
  } else {
    Serial.print("Read Value: ");
    Serial.println(readValue);
  }

  delay(1000);
}
