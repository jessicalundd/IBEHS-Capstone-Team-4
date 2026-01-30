import serial
import time
import numpy as np
import openpyxl
from scipy import integrate

sampling_rate = 100  # max frequency for ToF
window_size = 10
calibration_length = 3  # seconds
sample_delay = 10  # how many samples to skip before updating display

file_path = r"C:\Users\lamcl\Downloads\ToF Verification.xlsx"
workbook = openpyxl.load_workbook(filename=file_path)
sheet = workbook.active

meas_time = 5  # seconds
distance = 50  # mm
angle = 5  # degree

meas_distances = []

with serial.Serial('COM4', 115200, timeout=1) as ser:
    def clear_serial_buffer(s):
        time.sleep(0.5)  # wait for first junk data to arrive
        s.reset_input_buffer()  # clears everything received but unread
        s.reset_output_buffer()

    clear_serial_buffer(ser)

    # Rolling average - finding the space
    rolling_buffer = []
    sample_count = 0

    start_time = time.time()
    while True:
        try:
            if (time.time() - start_time) <= meas_time:
                current_data = float(ser.readline().decode('utf-8').rstrip())
                rolling_buffer.append(current_data)
                if len(rolling_buffer) > window_size:
                    rolling_buffer.pop(0)

                sample_count += 1
                if len(rolling_buffer) == window_size and (sample_count % sample_delay == 0):
                    avg = np.mean(rolling_buffer, axis=0)
                    meas_distances.append(avg)
                    print(f"Rolling avg: {np.round(avg, 3)}")

            else:
                new_data = [distance, angle] + meas_distances
                sheet.append(new_data)  # adding new row of data
                workbook.save(filename=file_path)
                print(f"Data appended to {file_path}")
                break

        except KeyboardInterrupt:
            break

ser.close()


