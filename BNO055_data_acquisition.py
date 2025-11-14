import serial
import time
import numpy as np
from scipy import integrate

sampling_rate = 100  # default for BNO055, can adjust in arduino code
window_size = 10
calibration_length = 3  # seconds
sample_delay = 10  # how many samples to skip before updating display

initial_angle = []
initial_acc = []

with serial.Serial('COM3', 9600, timeout=1) as ser:
    # status = input("Ready to calibrate? Enter Y or N: ")
    #
    # if status == 'Y':
    #     i = 0
    #     while i < calibration_length * sampling_rate:
    #         try:
    #             current_data = str(ser.readline())
    #             if "Xe" in current_data or "Xa" in current_data:
    #                 split_data = current_data.split(" ")
    #                 split_data[-1] = split_data[-1].strip("\\r\\n'")
    #                 data_array = np.asarray(split_data[1::2], dtype=float)
    #                 initial_angle.append(data_array[0:3])
    #                 initial_acc.append(data_array[3:])
    #                 i += 1
    #         except KeyboardInterrupt:
    #             break
    #     home_angle = np.asarray(initial_angle).mean(axis=0)
    #     home_acc = np.asarray(initial_acc).mean(axis=0)

    # Rolling average
    # rolling_buffer = []
    # sample_count = 0
    # while True:
    #     try:
    #         current_data = str(ser.readline())
    #         if "Xe" in current_data or "Xa" in current_data:
    #             split_data = current_data.split(" ")
    #             split_data[-1] = split_data[-1].strip("\\r\\n'")
    #             data_array = np.asarray(split_data[1::2], dtype=float)
    #
    #             rolling_buffer.append(data_array)
    #             if len(rolling_buffer) > window_size:
    #                 rolling_buffer.pop(0)
    #
    #             sample_count += 1
    #             if len(rolling_buffer) == window_size and (sample_count % sample_delay == 0):
    #                 avg = np.mean(rolling_buffer, axis=0)
    #                 print("Rolling avg:", avg)
    #
    #     except KeyboardInterrupt:
    #         break

    # Calculate position
    data = []
    times = []
    start_time = time.time()
    print('starting')
    while True:

        try:
            current_data = str(ser.readline())
            if "Xe" in current_data:
                times.append(time.time() - start_time)
                split_data = current_data.split(" ")
                split_data[-1] = split_data[-1].strip("\\r\\n'")
                data_array = np.asarray(split_data[1::2], dtype=float)
                data.append(data_array)
        except KeyboardInterrupt:
            break

    data = np.asarray(data)
    times = np.array(times)
    if len(times) > len(data):
        times = times[:len(data)-1]

    acc_data = data[:, 3:].T
    velocities = []
    for d in acc_data:
        v = integrate.cumulative_simpson(d, x=times)
        velocities.append(v)
    positions = []
    for v in velocities:
        p = integrate.simpson(v, times[:-1])
        positions.append(p)

ser.close()
