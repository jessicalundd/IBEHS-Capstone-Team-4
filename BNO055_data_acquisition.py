import serial
import time
import numpy as np

sampling_rate = 10
calibration_length = 3  # seconds

initial_angle = []
initial_acc = []

with serial.Serial('COM3', 9600, timeout=1) as ser:
    status = input("Ready to calibrate? Enter Y or N: ")

    while True:
        try:
            if status == 'Y':
                i = 0
                while i < calibration_length * sampling_rate * 2:
                    current_data = str(ser.readline())
                    if "Xe" in current_data or "Xa" in current_data:
                        split_data = current_data.split(" ")
                        data_array = np.asarray([float(split_data[1]), float(split_data[3]), float(split_data[5].strip("\\n'"))])
                        if "e" in current_data:
                            initial_angle.append(data_array)
                        else:
                            initial_acc.append(data_array)
                        i += 1

                    time.sleep(1/sampling_rate)
                home_angle = np.asarray(initial_angle).mean(axis=0)
                home_acc = np.asarray(initial_acc).mean(axis=0)
                print(len(initial_angle))
                status = 'N'

            current_data = str(ser.readline())
            print(current_data)
            time.sleep(1 / sampling_rate)
        except KeyboardInterrupt:
            break
ser.close()
