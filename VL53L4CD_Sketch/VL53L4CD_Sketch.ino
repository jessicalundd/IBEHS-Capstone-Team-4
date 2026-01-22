/*
  VL53L4CD ESP32 Qwiic Test
  Uses Pololu VL53L4CD Arduino library
  Outputs distance in mm (Serial Plotter friendly)
*/

#include <Wire.h>
#include <VL53L4CD.h>

VL53L4CD sensor;

void setup()
{
  // Start Serial FIRST (ESP32-safe)
  Serial.begin(115200);
  delay(1000);

  Serial.println("VL53L4CD ESP32 starting...");

  // Start I2C (ESP32 default: SDA=21, SCL=22)
  Wire.begin();
  Wire.setClock(400000);

  // Initialize sensor
  sensor.setTimeout(500);

  if (!sensor.init())
  {
    Serial.println("ERROR: VL53L4CD not detected");
    while (1) {
      delay(100);
    }
  }

  Serial.println("VL53L4CD initialized");

  // Start continuous ranging
  sensor.startContinuous();
}

void loop()
{
  uint16_t distance = sensor.read();

  Serial.println(distance);  // One number per line → Serial Plotter

  if (sensor.timeoutOccurred())
  {
    Serial.println("0"); // keep plotter alive even on timeout
  }

  delay(50); // ~20 Hz update
}
