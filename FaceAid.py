import cv2
import mediapipe as mp
import pyautogui
import numpy as np

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

    # Check if a face is found
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

        # Move Mouse
        if move_x != 0 or move_y != 0:
            curr_x, curr_y = pyautogui.position()
            pyautogui.moveTo(curr_x + move_x, curr_y + move_y)

    cv2.imshow('FaceAid SafeBox', frame)
    if cv2.waitKey(1) == 27: 
        break

cam.release()
cv2.destroyAllWindows()