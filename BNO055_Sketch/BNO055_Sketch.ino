#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
  
Adafruit_BNO055 bno = Adafruit_BNO055(55);

void setup(void) 
{
  Serial.begin(9600);
  Serial.println("Orientation Sensor Test"); Serial.println("");
  
  /* Initialise the sensor */
  if(!bno.begin())
  {
    /* There was a problem detecting the BNO055 ... check your connections */
    Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
    while(1);
  }
  
  delay(1000);
    
  bno.setExtCrystalUse(true);
}

void loop(void) 
{
  imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
  imu::Vector<3> accelerometer = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);

  /* Display the floating point data */
  Serial.print("Xe: ");
  Serial.print(euler.x());
  Serial.print(" Ye: ");
  Serial.print(euler.y());
  Serial.print(" Ze: ");
  Serial.print(euler.z());
  Serial.print("\n");
  
  Serial.print("Xa: ");
  Serial.print(accelerometer.x());
  Serial.print(" Ya: ");
  Serial.print(accelerometer.y());
  Serial.print(" Za: ");
  Serial.print(accelerometer.z());
  Serial.print("\n");
}