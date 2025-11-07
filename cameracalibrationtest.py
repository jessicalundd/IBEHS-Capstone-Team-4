import cv2
import numpy as np
import glob
import math

CHECKERBOARD = (9,6)

objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

# Arrays to store object points and image points
objpoints = []  # 3d points in real world space
imgpoints = []  # 2d points in image plane

# Load images
images = glob.glob('C:/Users/megha/Downloads/Camera Calibration/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    # If found, refine and add points
    if ret:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(
            gray, corners, (11, 11), (-1, -1),
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        )
        imgpoints.append(corners2)

        # Optional: draw and show
        cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
        cv2.imshow('Corners', img)
        cv2.waitKey(100)

cv2.destroyAllWindows()

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)
print("Camera matrix:\n", np.array2string(mtx, precision=3, suppress_small=True))
print("Distortion coefficients:\n", dist)
np.savez('camera_calibration.npz', mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs)

img = cv2.imread('C:/Users/megha/Downloads/Camera Calibration/Image8.jpg')
h, w = img.shape[:2]
print("Width:", w)
print("Height:", h)

fx = mtx[0, 0]
fy = mtx[1, 1]

fov_x = 2 * math.degrees(math.atan(w / (2 * fx)))
fov_y = 2 * math.degrees(math.atan(h / (2 * fy)))
print(f"Horizontal FOV: {fov_x:.2f} degrees")
print(f"Vertical FOV:   {fov_y:.2f} degrees")