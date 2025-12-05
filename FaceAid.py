import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time


#blinking
BLINK_THRESHOLD = 0.012
DOUBLE_BLINK_TIME = 0.6
blink_count = 0
last_blink_end = 0

#helper functions
def get_dist(p1, p2):
    return np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p2.x, p2.y]))

def calculate_ear(landmarks):
    left = get_dist(landmarks[159], landmarks[145])
    right = get_dist(landmarks[386], landmarks[374])
    return (left + right) / 2.0

#config
DEADZONE_X = 0.06
DEADZONE_Y = 0.05
SPEED_SENSITIVITY_X = 25.0
SPEED_SENSITIVITY_Y = 35.0
pyautogui.FAILSAFE = False
screen_w, screen_h = pyautogui.size()

# Setup Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = cam.read()
    if not ret: 
        break
    
    frame = cv2.flip(frame, 1) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    frame_h, frame_w, _ = frame.shape

    center_x, center_y = int(frame_w / 2), int(frame_h / 2)
    box_w = int(DEADZONE_X * frame_w)
    box_h = int(DEADZONE_Y * frame_h)
    
    cv2.rectangle(frame, 
                  (center_x - box_w, center_y - box_h), 
                  (center_x + box_w, center_y + box_h), 
                  (255, 255, 255), 1)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        # add logic here
        nose = landmarks[4]
        
        # Calculate offset from center
        dx = nose.x - 0.5
        dy = nose.y - 0.5
        
        move_x = 0
        move_y = 0
        
        # X Logic
        if abs(dx) > DEADZONE_X:
            if dx > 0: 
                val = dx - DEADZONE_X
            else:      
                val = dx + DEADZONE_X
            move_x = val * SPEED_SENSITIVITY_X * 50

        # Y Logic
        if abs(dy) > DEADZONE_Y:
            if dy > 0: 
                val = dy - DEADZONE_Y
            else:      
                val = dy + DEADZONE_Y
            move_y = val * SPEED_SENSITIVITY_Y * 50

        # Move Mouse & Visuals
        if move_x != 0 or move_y != 0:
            curr_x, curr_y = pyautogui.position()
            pyautogui.moveTo(curr_x + move_x, curr_y + move_y)
            
            # Green line showing active push
            nose_px = (int(nose.x * frame_w), int(nose.y * frame_h))
            cv2.line(frame, (center_x, center_y), nose_px, (0, 255, 0), 2)
        else:
            # Red Dot (Safe/Stopped)
            nose_px = (int(nose.x * frame_w), int(nose.y * frame_h))
            cv2.circle(frame, nose_px, 5, (0, 0, 255), -1)

    cv2.imshow('FaceAid SafeBox', frame)
    if cv2.waitKey(1) == 27: 
        break

cam.release()
cv2.destroyAllWindows()