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
    def clear_serial_buffer(s):
        time.sleep(0.5)  # wait for first junk data to arrive
        s.reset_input_buffer()  # clears everything received but unread
        s.reset_output_buffer()

    status = input("Ready to calibrate? Enter Y or N: ")

    if status == 'Y':
        print('Clearing buffer...')  # makes sure the data is the home position and not stored previously
        clear_serial_buffer(ser)
        print('Buffer cleared.')

        i = 0
        while i < calibration_length * sampling_rate + 100:
            try:
                current_data = str(ser.readline())
                print(current_data)
                if "Xe" in current_data:
                    split_data = current_data.split(" ")
                    split_data[-1] = split_data[-1].strip("\\r\\n'")
                    data_array = np.asarray(split_data[1::2], dtype=float)
                    initial_angle.append(data_array[0:3])
                    initial_acc.append(data_array[3:])
                    i += 1
            except KeyboardInterrupt:
                pass
        home_angle = np.asarray(initial_angle[100:]).mean(axis=0)  # taking off first 100 data points bc of buffer issue
        home_acc = np.asarray(initial_acc[100:]).mean(axis=0)  # taking off first 100 data points bc of buffer issue

    homes = np.concatenate((home_angle, home_acc), dtype=float)
    space = []  # data for angles throughout the space

    # Rolling average - finding the space
    rolling_buffer = []
    sample_count = 0
    while True:
        try:
            current_data = str(ser.readline())
            if "Xe" in current_data:
                split_data = current_data.split(" ")
                split_data[-1] = split_data[-1].strip("\\r\\n'")
                data_array = np.asarray(split_data[1::2], dtype=float) - homes

                rolling_buffer.append(data_array)
                if len(rolling_buffer) > window_size:
                    rolling_buffer.pop(0)

                sample_count += 1
                if len(rolling_buffer) == window_size and (sample_count % sample_delay == 0):
                    avg = np.mean(rolling_buffer, axis=0)
                    print(f"Rolling avg: {np.round(avg, 3)}")

                    space.append(avg)

        except KeyboardInterrupt:
            break

ser.close()

space = np.array(space)
space_angles = space[:, :3].T  # x, y, z angles in arrays
angle1_list = []
angle2_list = []
angle_diff_list = []
indicator_list = []

for angles in space_angles:
    if any(angles >=0) and any(angles < 0):  # +ve and -ve angles present, angle deviations from 0 degrees, +ve = one extreme and -ve = other extreme
        angle1 = min(angles)  # finds the largest negative angle
        angle2 = max(angles)  # finds the largest positive angle
        angle_diff = abs(angle2 - angle1)
        indicator = "pos-neg"
    if not any(angles < 0):  # only +ve angles, angle deviations from 0 degrees, extremes separated by 180 degrees
        angle1 = min(angles[angles > 180])  # finding extreme past 180, closer to 360 indicates smaller angle
        angle2 = max(angles[angles < 180])  # finding extreme before 180, closer to 0 indicates smaller angle
        angle_diff = abs(angle2 - (angle1 - 360))
        indicator = "pos"
    if not any(angles > 0):  # only -ve angles, angle deviations from 0 degrees, extremes separated by -180 degrees
        angle1 = max(angles[angles < -180])  # finding extreme past -180, closer to -360 indicates smaller angle
        angle2 = min(angles[angles > -180])  # finding extreme before -180, closer to 0 indicates smaller angle
        angle_diff = abs(angle2 - (angle1 + 360))
        indicator="neg"

    angle1_list.append(angle1)
    angle2_list.append(angle2)
    angle_diff_list.append(angle_diff)
    indicator_list.append(indicator)

print(indicator_list)
time.sleep(5)

with serial.Serial('COM3', 9600, timeout=1) as ser:
    def clear_serial_buffer(s):
        time.sleep(0.5)  # wait for first junk data to arrive
        s.reset_input_buffer()  # clears everything received but unread
        s.reset_output_buffer()

    status = input("Ready to take video? Enter Y or N: ")

    if status == "Y":
        print('Clearing buffer...')  # makes sure the data is the home position and not stored previously
        clear_serial_buffer(ser)
        print('Buffer cleared.')

    video_data = []
    thru_space = np.zeros([3, 2])  # tracks if all angles have been reached

    while True:
        try:
            current_data = str(ser.readline())
            if "Xe" in current_data:
                split_data = current_data.split(" ")
                split_data[-1] = split_data[-1].strip("\\r\\n'")
                data_array = np.asarray(split_data[1::2], dtype=float) - homes

                video_data.append(data_array)
                data_array_angles = data_array[:3]

                for i, angle in enumerate(data_array_angles):
                    indicator = indicator_list[i]
                    if indicator == "pos-neg":
                        if angle >= angle2_list[i]:
                            print(f'Achieved maximum angle for angle index {i}')
                            thru_space[i][1] = 1
                        if angle <= angle1_list[i]:
                            print(f'Achieved minimum angle for angle index {i}')
                            thru_space[i][0] = 1
                    if indicator == "pos":
                        if 180 > angle >= angle2_list[i]:
                            print(f'Achieved maximum angle for angle index {i}')
                            thru_space[i][1] = 1
                        if 180 < angle <= angle1_list[i]:
                            print(f'Achieved minimum angle for angle index {i}')
                            thru_space[i][0] = 1
                    if indicator == "neg":
                        if -180 < angle <= angle2_list[i]:
                            print(f'Achieved maximum angle for angle index {i}')
                            thru_space[i][1] = 1
                        if -180 > angle >= angle1_list[i]:
                            print(f'Achieved minimum angle for angle index {i}')
                            thru_space[i][0] = 1

                if np.all(thru_space):
                    print('All of the space has been captured')
                    break

        except KeyboardInterrupt:
            break

ser.close()


#     # Calculate position
#     data = []
#     times = []
#     start_time = time.time()
#     print('starting')
#     while True:
#
#         try:
#             current_data = str(ser.readline())
#             if "Xe" in current_data:
#                 times.append(time.time() - start_time)
#                 split_data = current_data.split(" ")
#                 split_data[-1] = split_data[-1].strip("\\r\\n'")
#                 data_array = np.asarray(split_data[1::2], dtype=float)
#                 data.append(data_array)
#         except KeyboardInterrupt:
#             break
#
#     data = np.asarray(data)
#     times = np.array(times)
#     if len(times) > len(data):
#         times = times[:len(data)-1]
#
#     acc_data = data[:, 3:].T
#     velocities = []
#     for d in acc_data:
#         v = integrate.cumulative_simpson(d, x=times)
#         velocities.append(v)
#     positions = []
#     for v in velocities:
#         p = integrate.simpson(v, times[:-1])
#         positions.append(p)
#
# ser.close()
