import cv2
import numpy as np
import threading
from playsound import playsound
import os
import time


stream_url = 'http://192.168.87.131:81/stream'


with open('coco.names', 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')


configPath = 'ssd_mobilenet_v3_large_coco_2020_01_14 (1).pbtxt'
weightsPath = 'frozen_inference_graph (1).pb'


net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(300, 300)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

is_playing = False
prev_direction = ""
prev_label = ""


audio_dir_direction = os.path.join(os.getcwd(), "audio_left_right")
audio_dir_objects = os.path.join(os.getcwd(), "Audiofiles")


direction_files = {
    "left": "move_left.mp3",
    "center": "center.mp3",
    "right": "move_right.mp3"
}

def play_both_audios(label, direction):
    global is_playing
    is_playing = True

    
    obj_audio_path = os.path.join(audio_dir_objects, label + ".mp3")
    if os.path.exists(obj_audio_path):
        try:
            playsound(obj_audio_path)
        except Exception as e:
            print(f"[Error] Couldn't play object audio ({label}): {e}")
    else:
        print(f"[Missing] Object audio: {label}")

    
    time.sleep(1)

    
    dir_audio_filename = direction_files.get(direction)
    dir_audio_path = os.path.join(audio_dir_direction, dir_audio_filename) if dir_audio_filename else ""
    if os.path.exists(dir_audio_path):
        try:
            playsound(dir_audio_path)
        except Exception as e:
            print(f"[Error] Couldn't play direction audio ({direction}): {e}")
    else:
        print(f"[Missing] Direction audio: {direction}")

    is_playing = False


cap = cv2.VideoCapture(stream_url)
print("[INFO] Starting object and direction detection...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[Warning] Couldn't read frame.")
        continue

    height, width, _ = frame.shape
    zone_width = width // 3

    zones = {
        "left": (0, zone_width),
        "center": (zone_width, 2 * zone_width),
        "right": (2 * zone_width, width)
    }

    classIds, confs, bbox = net.detect(frame, confThreshold=0.5)
    zone_votes = {"left": 0, "center": 0, "right": 0}
    current_label = None

    if len(classIds) != 0:
        classIds = classIds.flatten()
        for i in range(len(classIds)):
            classId = int(classIds[i])
            box = bbox[i]
            x, y, w, h = box
            obj_left = x
            obj_right = x + w

            
            overlaps = {
                zone: max(0, min(obj_right, end) - max(obj_left, start))
                for zone, (start, end) in zones.items()
            }
            max_zone = max(overlaps, key=overlaps.get)
            zone_votes[max_zone] += 1

            
            label = classNames[classId - 1] if 0 < classId <= len(classNames) else "Unknown"
            current_label = label

            cv2.rectangle(frame, box, (0, 255, 0), 2)
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        
        detected_zone = max(zone_votes, key=zone_votes.get)
        direction_map = {"left": "right", "right": "left", "center": "center"}
        suggested_direction = direction_map[detected_zone]

        
        if current_label and (suggested_direction != prev_direction or current_label != prev_label) and not is_playing:
            prev_direction = suggested_direction
            prev_label = current_label
            threading.Thread(target=play_both_audios, args=(current_label, suggested_direction), daemon=True).start()

    else:
        print("[INFO] No objects detected.")

    
    cv2.line(frame, (zone_width, 0), (zone_width, height), (255, 0, 0), 2)
    cv2.line(frame, (2 * zone_width, 0), (2 * zone_width, height), (255, 0, 0), 2)
    cv2.putText(frame, "Left", (zone_width // 2 - 30, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.putText(frame, "Center", (zone_width + zone_width // 2 - 50, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.putText(frame, "Right", (2 * zone_width + zone_width // 2 - 40, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    cv2.imshow("Object + Direction Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()