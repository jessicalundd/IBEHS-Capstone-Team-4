import sys
import serial
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout, QProgressBar

# Worker Thread
class SerialWorker(QThread):
    update_calibration_progress = pyqtSignal(float)
    calibration_done = pyqtSignal(np.ndarray)
    update_angles = pyqtSignal(float, float, float)   # send first 3 avg values to GUI
    update_thru_space = pyqtSignal(np.ndarray)
    extremes_done = pyqtSignal(list, list, list, list)
    all_space_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.port = 'COM4'
        self.baud = 9600

        self.running = False
        self.tracking = False
        self.video_running = False

        # parameters
        self.sampling_rate = 100
        self.window_size = 10
        self.calibration_length = 3
        self.sample_delay = 10

        # Initial state
        self.homes = None
        self.angle1_list = None
        self.angle2_list = None
        self.indicator_list = None
        self.thru_space = np.zeros((3, 2))
        self.rolling_buffer = []
        self.space = []

    def clear_serial_buffer(self, ser):
        time.sleep(0.5)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

    def compute_extremes(self):
        space_arr = np.array(self.space)
        space_angles = space_arr[:, :3].T
        angle1_list, angle2_list, angle_diff_list, indicator_list = [], [], [], []

        for angles in space_angles:
            if any(angles >= 0) and any(angles < 0):  # +ve and -ve angles present, angle deviations from 0 degrees, +ve = one extreme and -ve = other extreme
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
                indicator = "neg"

            angle1_list.append(angle1)
            angle2_list.append(angle2)
            angle_diff_list.append(angle_diff)
            indicator_list.append(indicator)

        self.angle1_list = angle1_list
        self.angle2_list = angle2_list
        self.indicator_list = indicator_list
        self.extremes_done.emit(angle1_list, angle2_list, angle_diff_list, indicator_list)

    def run_calibration(self, ser):
        print("Starting calibration...")
        initial_angle = []
        initial_acc = []

        print("Clearing buffer...")
        self.clear_serial_buffer(ser)
        print("Buffer cleared.")

        i = 0
        total_samples = self.calibration_length * self.sampling_rate + 100

        while i < total_samples and self.running:
            current_data = str(ser.readline())
            if "Xe" in current_data:
                split_data = current_data.split(" ")
                split_data[-1] = split_data[-1].strip("\\r\\n'")
                data_array = np.asarray(split_data[1::2], dtype=float)

                initial_angle.append(data_array[0:3])
                initial_acc.append(data_array[3:])
                i += 1

                # Emit calibration progress (0 to 100%)
                progress = min(100, (i / total_samples) * 100)
                self.update_calibration_progress.emit(progress)

        # Remove first 100 samples
        home_angle = np.mean(initial_angle[100:], axis=0)
        home_acc = np.mean(initial_acc[100:], axis=0)
        self.homes = np.concatenate((home_angle, home_acc))
        self.calibration_done.emit(self.homes)

    def run_loop(self, ser):
        sample_count = 0
        while self.running:
            current_data = str(ser.readline())
            if "Xe" in current_data:
                split_data = current_data.split(" ")
                split_data[-1] = split_data[-1].strip("\\r\\n'")
                data_array = np.asarray(split_data[1::2], dtype=float) - self.homes
                angles = data_array[:3]

                self.rolling_buffer.append(data_array)
                if len(self.rolling_buffer) > self.window_size:
                    self.rolling_buffer.pop(0)

                sample_count += 1
                if len(self.rolling_buffer) == self.window_size and (sample_count % self.sample_delay == 0):
                    avg = np.mean(self.rolling_buffer, axis=0)
                    self.update_angles.emit(avg[0], avg[1], avg[2])

                    if self.tracking:
                        self.space.append(avg)
                    else:
                        if self.space:
                            self.compute_extremes()
                            self.space = []

                    if self.video_running and self.angle1_list is not None:
                        for i, angle in enumerate(angles):
                            indicator = self.indicator_list[i]
                            if indicator == "pos-neg":
                                if angle >= self.angle2_list[i]:
                                    self.thru_space[i][1] = 1
                                if angle <= self.angle1_list[i]:
                                    self.thru_space[i][0] = 1
                            elif indicator == "pos":
                                if 180 > angle >= self.angle2_list[i]:
                                    self.thru_space[i][1] = 1
                                if 180 < angle <= self.angle1_list[i]:
                                    self.thru_space[i][0] = 1
                            elif indicator == "neg":
                                if -180 < angle <= self.angle2_list[i]:
                                    self.thru_space[i][1] = 1
                                if -180 > angle >= self.angle1_list[i]:
                                    self.thru_space[i][0] = 1

                        self.update_thru_space.emit(self.thru_space.copy())
                        if np.all(self.thru_space):
                            self.all_space_done.emit()
        print("Run stopped.")

    def run(self):
        try:
            with serial.Serial(self.port, self.baud, timeout=1) as ser:
                self.running = True
                self.clear_serial_buffer(ser)
                self.run_calibration(ser)
                self.run_loop(ser)
        except serial.SerialException as e:
            print(f"Serial error: {e}")

    def stop(self):
        self.running = False
        self.wait()

# GUI
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gyroscope Tracker")
        self.resize(500, 400)

        # Widgets
        self.pbar = QProgressBar(self)
        self.pbar.setRange(0, 100)

        self.cal_button = QPushButton("Start Calibration")
        self.start_track_button = QPushButton("Start Tracking")
        self.stop_track_button = QPushButton("Stop Tracking")
        self.start_video_button = QPushButton("Start Video")
        self.stop_video_button = QPushButton("Stop Video")

        self.angle_labels = [QLabel("X: ---"), QLabel("Y: ---"), QLabel("Z: ---")]
        self.thru_labels = [QLabel("X min/max: 0/0"), QLabel("Y min/max: 0/0"), QLabel("Z min/max: 0/0")]

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.cal_button)
        layout.addWidget(self.pbar)

        track_layout = QHBoxLayout()
        track_layout.addWidget(self.start_track_button)
        track_layout.addWidget(self.stop_track_button)
        layout.addLayout(track_layout)

        video_layout = QHBoxLayout()
        video_layout.addWidget(self.start_video_button)
        video_layout.addWidget(self.stop_video_button)
        layout.addLayout(video_layout)

        grid = QGridLayout()
        for i in range(3):
            grid.addWidget(self.angle_labels[i], i, 0)
            grid.addWidget(self.thru_labels[i], i, 1)
        layout.addLayout(grid)

        self.setLayout(layout)

        # Worker connections
        self.worker = SerialWorker()
        self.worker.update_calibration_progress.connect(self.update_calibration_progress)
        self.worker.update_angles.connect(self.update_angles)
        self.worker.update_thru_space.connect(self.update_thru_labels)
        self.worker.calibration_done.connect(self.calibration_done)
        self.worker.extremes_done.connect(self.extremes_done)
        self.worker.all_space_done.connect(self.video_done)

        # Buttons
        self.cal_button.clicked.connect(self.start_calibration)
        self.start_track_button.clicked.connect(self.start_tracking)
        self.stop_track_button.clicked.connect(self.stop_tracking)
        self.start_video_button.clicked.connect(self.start_video)
        self.stop_video_button.clicked.connect(self.stop_video)

    # Button methods
    def start_calibration(self):
        self.worker.start()
        self.cal_button.setEnabled(False)

    def start_tracking(self):
        self.worker.tracking = True

    def stop_tracking(self):
        self.worker.tracking = False

    def start_video(self):
        if self.worker.angle1_list is None:
            print("Tracking data not ready!")
            return
        self.worker.thru_space = np.zeros((3, 2))
        self.worker.video_running = True

    def stop_video(self):
        self.worker.video_running = False

    # Slots
    def update_calibration_progress(self, value):
        self.pbar.setValue(int(value))

    def calibration_done(self, homes):
        print("Calibration done.")

    def extremes_done(self, angle1, angle2, diff, indicator):
        print("Extremes computed.")

    def update_angles(self, x, y, z):
        self.angle_labels[0].setText(f"X: {x:.3f}")
        self.angle_labels[1].setText(f"Y: {y:.3f}")
        self.angle_labels[2].setText(f"Z: {z:.3f}")

    def update_thru_labels(self, thru_space):
        for i in range(3):
            self.thru_labels[i].setText(f"{['X','Y','Z'][i]} min/max: {int(thru_space[i][0])}/{int(thru_space[i][1])}")

    def video_done(self):
        print("All of the space has been captured!")

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()


# Main
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())