import sys
import serial
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel

# -------------------------
# Worker Thread
# -------------------------
class SerialWorker(QThread):
    update_angles = pyqtSignal(float, float, float)   # send first 3 avg values to GUI
    calibration_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = False

        # parameters
        self.sampling_rate = 100
        self.window_size = 10
        self.calibration_length = 3
        self.sample_delay = 10

        self.home_angle = None
        self.home_acc = None

    def clear_serial_buffer(self, ser):
        time.sleep(0.5)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

    def run_calibration(self, ser):
        initial_angle = []
        initial_acc = []

        print("Clearing buffer...")
        self.clear_serial_buffer(ser)
        print("Buffer cleared.")

        i = 0
        total_samples = self.calibration_length * self.sampling_rate + 100

        while i < total_samples:
            current_data = str(ser.readline())
            if "Xe" in current_data:
                split_data = current_data.split(" ")
                split_data[-1] = split_data[-1].strip("\\r\\n'")
                data_array = np.asarray(split_data[1::2], dtype=float)

                initial_angle.append(data_array[0:3])
                initial_acc.append(data_array[3:])
                i += 1

        # Remove first 100 samples
        self.home_angle = np.mean(initial_angle[100:], axis=0)
        self.home_acc = np.mean(initial_acc[100:], axis=0)

    def run(self):
        """Main worker loop."""
        self.running = True

        with serial.Serial('COM4', 9600, timeout=1) as ser:

            # ---- Calibration phase ----
            self.run_calibration(ser)
            homes = np.concatenate((self.home_angle, self.home_acc))
            self.calibration_done.emit()

            # ---- Tracking phase ----
            rolling_buffer = []
            sample_count = 0

            while self.running:
                current_data = str(ser.readline())
                if "Xe" in current_data:
                    split_data = current_data.split(" ")
                    split_data[-1] = split_data[-1].strip("\\r\\n'")
                    data_array = np.asarray(split_data[1::2], dtype=float) - homes

                    rolling_buffer.append(data_array)
                    if len(rolling_buffer) > self.window_size:
                        rolling_buffer.pop(0)

                    sample_count += 1
                    if len(rolling_buffer) == self.window_size and (sample_count % self.sample_delay == 0):
                        avg = np.mean(rolling_buffer, axis=0)
                        self.update_angles.emit(avg[0], avg[1], avg[2])

        print("Thread stopped.")

    def stop(self):
        self.running = False
        self.wait()


# -------------------------
# GUI
# -------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.worker = SerialWorker()

        # GUI elements
        self.cal_button = QPushButton("Start Calibration")
        self.label = QLabel("Waiting...")
        self.label.setStyleSheet("font-size: 20px;")

        layout = QVBoxLayout()
        layout.addWidget(self.cal_button)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # connections
        self.cal_button.clicked.connect(self.start_worker)
        self.worker.update_angles.connect(self.update_label)
        self.worker.calibration_done.connect(self.on_calibration_done)

        self.setWindowTitle("Gyro Tracking GUI")

    def start_worker(self):
        self.cal_button.setEnabled(False)
        self.label.setText("Calibrating...")
        self.worker.start()

    def on_calibration_done(self):
        self.label.setText("Calibration complete.\nTracking angles...")

    def update_label(self, a, b, c):
        self.label.setText(f"Angles:\nX: {a:.3f}\nY: {b:.3f}\nZ: {c:.3f}")

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()


# -------------------------
# Main
# -------------------------
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
