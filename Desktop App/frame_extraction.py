import cv2
import os
import sys
import subprocess
import shutil

def print_now(text):
    print(text)
    sys.stdout.flush()

def apply_metadata_to_folder(folder_path, make, model, focal_length):
    exif_path = shutil.which("exiftool")
    
    command = [
        exif_path, 
        "-overwrite_original_in_place", 
        "-m", "-P",
        f"-Make={make}", 
        f"-Model={model}", 
        f"-FocalLength={focal_length}", 
        folder_path
    ]

    try:
        # Run the bulk update on the whole folder
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print_now(f"EXIFTOOL ERROR: {result.stderr}")
    except Exception as e:
        print_now(f"CRASH: {e}")

def extract_frames(video_path, base_folder, patient_name, make, model, focal_length):
    patient_folder = os.path.join(base_folder, patient_name)
    if not os.path.exists(patient_folder):
        os.makedirs(patient_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print_now("ERROR: Could not open video file.")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    chunks_per_second = 2
    chunk_size = max(1, fps // chunks_per_second)

    frame_idx = 0
    saved_count = 0

    while frame_idx + chunk_size <= frame_count:
        arr_frame = []
        arr_lap = []

        # extracting sharpest frame using Laplacian
        for _ in range(chunk_size):
            success, frame = cap.read()
            if not success:
                break
            laplacian = cv2.Laplacian(frame, cv2.CV_64F).var()
            arr_lap.append(laplacian)
            arr_frame.append(frame)
            frame_idx += 1

        if arr_lap:
            sharpest_idx = arr_lap.index(max(arr_lap))
            selected_frame = arr_frame[sharpest_idx]
            frame_filename = f"frame_{saved_count:04d}.jpg"
            save_path = os.path.join(patient_folder, frame_filename)
            if cv2.imwrite(save_path, selected_frame):
                saved_count += 1

        if frame_count > 0:
            progress = int((frame_idx / frame_count) * 100)
            print_now(f"PROGRESS:{min(progress, 100)}")

    cap.release()
    
    # Run Metadata Injection
    apply_metadata_to_folder(patient_folder, make, model, focal_length)
    print_now("EXTRACTION_COMPLETE")

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print_now("ERROR: Missing arguments.")
    else:
        v_path = sys.argv[1]
        b_folder = sys.argv[2]
        p_name = sys.argv[3]
        u_make = sys.argv[4]
        u_model = sys.argv[5]
        u_focal = sys.argv[6]
        
        extract_frames(v_path, b_folder, p_name, u_make, u_model, u_focal)