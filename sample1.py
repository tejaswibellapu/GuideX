import cv2
import numpy as np
import threading
from playsound import playsound
import os


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
prev_object = ""


def play_audio(label):
    global is_playing
    is_playing = True
    audio_path = os.path.join("C:\\Users\\Deeptha Bandi\\OneDrive\\Desktop\\hackathonproject1\\Audiofiles", label + ".mp3")
    if os.path.exists(audio_path):
        playsound(audio_path)
    else:
        print(f"[Warning] Audio file not found: {label}")
    is_playing = False


cap = cv2.VideoCapture(stream_url)

while True:
    ret, frame = cap.read()
    if not ret:
        print("[Warning] Couldn't read frame.")
        continue

    classIds, confs, bbox = net.detect(frame, confThreshold=0.5)

    if len(classIds) != 0:
        max_conf_idx = np.argmax(confs)
        classId = classIds.flatten()[max_conf_idx]
        box = bbox[max_conf_idx]
        if 0 < classId <= len(classNames):
            label = classNames[classId - 1]
        else:
            print(f"[Warning] Invalid classId: {classId}")
            continue


        cv2.rectangle(frame, box, color=(0, 255, 0), thickness=2)
        cv2.putText(frame, label, (box[0] + 10, box[1] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if label != prev_object and not is_playing:
            prev_object = label
            threading.Thread(target=play_audio, args=(label,), daemon=True).start()

    cv2.imshow("ESP32-CAM Live Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
