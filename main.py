import serial
import time
with serial.Serial('COM3', 9600, timeout=1) as ser:
    while True:
        try:
            line = ser.readline()
            print(line)
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
ser.close()
