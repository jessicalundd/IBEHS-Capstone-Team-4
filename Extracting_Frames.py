# Video Frame Extraction
import cv2
import os

print("Saving images to:", os.getcwd())
cap = cv2.VideoCapture("/Users/yooseonjang/Documents/McMaster/Capstone/Tunnel_Box.MP4")
fps = int(cap.get(cv2.CAP_PROP_FPS))
print("fps:",fps)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print("frame count:",frame_count)

for i in range(int(frame_count/fps)):
     arr_frame=[]
     arr_lap=[]
     for j in range(fps):
         success, frame = cap.read()
         laplacian = cv2.Laplacian(frame, cv2.CV_64F).var()
         arr_lap.append(laplacian)
         arr_frame.append(frame)
     selected_frame = arr_frame[arr_lap.index(max(arr_lap))]
     cv2.imwrite(f"Tunnel_Box{i}.jpg", selected_frame)
