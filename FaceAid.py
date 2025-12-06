import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import winsound
import os
import subprocess
import tkinter as tk
from collections import deque

# --- 1. GLOBAL SETTINGS ---
pyautogui.FAILSAFE = False

# Sensitivity Settings (Global so GUI can eventually change them)
DEADZONE_X = 0.06
DEADZONE_Y = 0.05
SPEED_SENSITIVITY_X = 25.0
SPEED_SENSITIVITY_Y = 35.0

# Gesture Settings
BLINK_THRESHOLD = 0.012
MOUTH_THRESHOLD = 0.04
DOUBLE_BLINK_TIME = 0.6
EYES_CLOSED_TIME = 3.0

# --- 2. SETUP ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
screen_w, screen_h = pyautogui.size()

# State Variables
blink_count = 0
last_blink_end = 0
eyes_closed_start = None
is_eyes_closed = False
last_beep = 0
keyboard_trigger = 0

# --- 3. HELPER FUNCTIONS ---
def get_dist(p1, p2):
    return np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p2.x, p2.y]))

def calculate_ear(landmarks):
    left = get_dist(landmarks[159], landmarks[145])
    right = get_dist(landmarks[386], landmarks[374])
    return (left + right) / 2.0

def quit_program():
    print("Exiting...")
    cam.release()
    cv2.destroyAllWindows()
    root.destroy()
    exit()

# --- 4. THE MAIN LOOP (Now a function) ---
def update_camera():
    global blink_count, last_blink_end, eyes_closed_start, is_eyes_closed, last_beep, keyboard_trigger

    ret, frame = cam.read()
    if ret:
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        frame_h, frame_w, _ = frame.shape
        
        # Draw Safe Box
        center_x, center_y = int(frame_w / 2), int(frame_h / 2)
        box_w = int(DEADZONE_X * frame_w)
        box_h = int(DEADZONE_Y * frame_h)
        cv2.rectangle(frame, (center_x - box_w, center_y - box_h), (center_x + box_w, center_y + box_h), (255, 255, 255), 1)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            nose = landmarks[4]
            
            # --- JOYSTICK LOGIC ---
            dx = nose.x - 0.5
            dy = nose.y - 0.5
            move_x = 0
            move_y = 0
            
            if abs(dx) > DEADZONE_X:
                val = dx - DEADZONE_X if dx > 0 else dx + DEADZONE_X
                move_x = val * SPEED_SENSITIVITY_X * 50
            
            if abs(dy) > DEADZONE_Y:
                val = dy - DEADZONE_Y if dy > 0 else dy + DEADZONE_Y
                move_y = val * SPEED_SENSITIVITY_Y * 50

            if not is_eyes_closed:
                if move_x != 0 or move_y != 0:
                    curr_x, curr_y = pyautogui.position()
                    pyautogui.moveTo(curr_x + move_x, curr_y + move_y)
                    nose_px = (int(nose.x * frame_w), int(nose.y * frame_h))
                    cv2.line(frame, (center_x, center_y), nose_px, (0, 255, 0), 2)
                else:
                    nose_px = (int(nose.x * frame_w), int(nose.y * frame_h))
                    cv2.circle(frame, nose_px, 5, (0, 0, 255), -1)

            # --- GESTURES ---
            ear = calculate_ear(landmarks)
            
            # Eyes Closed / Exit
            if ear < BLINK_THRESHOLD: 
                if not is_eyes_closed:
                    eyes_closed_start = time.time()
                    is_eyes_closed = True
                
                elapsed = time.time() - eyes_closed_start
                countdown = EYES_CLOSED_TIME - elapsed
                curr_sec = int(elapsed)
                
                if curr_sec > last_beep and curr_sec < EYES_CLOSED_TIME:
                    winsound.Beep(500 + (curr_sec * 500), 200)
                    last_beep = curr_sec
                
                if countdown <= 0:
                    winsound.Beep(2000, 800)
                    quit_program() # Call the safe exit function
                cv2.putText(frame, f"EXIT: {countdown:.1f}", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
            else: 
                if is_eyes_closed:
                    if (time.time() - eyes_closed_start) < 1.0: # Short blink
                        curr_time = time.time()
                        if curr_time - last_blink_end < DOUBLE_BLINK_TIME:
                            blink_count += 1
                        else:
                            blink_count = 1
                        last_blink_end = curr_time
                    is_eyes_closed = False
                    eyes_closed_start = None
                    last_beep = 0

            # Click Execution
            if blink_count > 0 and (time.time() - last_blink_end > DOUBLE_BLINK_TIME):
                if blink_count == 2:
                    print("Click")
                    winsound.Beep(1000, 100)
                    pyautogui.mouseDown()
                    time.sleep(0.1) 
                    pyautogui.mouseUp()
                elif blink_count == 3:
                    print("Action: Backspace")
                    winsound.Beep(600, 100)
                    pyautogui.press('backspace')
                blink_count = 0

            # Keyboard Execution
            mar = get_dist(landmarks[13], landmarks[14])
            if mar > MOUTH_THRESHOLD:
                keyboard_trigger += 1
                if keyboard_trigger == 10: 
                    print("Keyboard")
                    winsound.Beep(800, 100)
                    try:
                        subprocess.Popen("osk", shell=True)
                    except: pass
                    keyboard_trigger = 0
            else:
                keyboard_trigger = 0

        cv2.imshow('FaceAid Camera View', frame)
        cv2.waitKey(1)

    # Schedule the next frame update in 10 milliseconds (100 FPS cap)
    # This keeps the Tkinter window alive while the camera runs
    root.after(10, update_camera)

# --- 5. GUI SETUP (DASHBOARD) ---
root = tk.Tk()
root.title("FaceAid Configuration")
root.geometry("400x600") # Smaller side-window
root.configure(bg="#2c3e50")

# Header
tk.Label(root, text="FaceAid Control", font=("Segoe UI", 20, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=15)

# Instructions Panel
instr_frame = tk.LabelFrame(root, text=" Commands ", font=("Segoe UI", 12, "bold"), bg="#34495e", fg="#ecf0f1", relief="flat")
instr_frame.pack(fill="x", padx=20, pady=10)

guide_text = (
    "HEAD: Tilt to move mouse\n"
    "CENTER: Stop mouse\n\n"
    "BLINK x2: Left Click\n"
    "BLINK x3: Go Back\n"
    "MOUTH: Open for Keyboard"
)
tk.Label(instr_frame, text=guide_text, justify="left", font=("Segoe UI", 11), bg="#34495e", fg="#ecf0f1").pack(anchor="w", padx=10, pady=10)

# Visual Settings (Placeholders for now)
settings_frame = tk.LabelFrame(root, text=" Settings (Visual) ", font=("Segoe UI", 12, "bold"), bg="#34495e", fg="#ecf0f1", relief="flat")
settings_frame.pack(fill="x", padx=20, pady=10)

tk.Label(settings_frame, text="Sensitivity", bg="#34495e", fg="#bdc3c7").pack(anchor="w", padx=10)
tk.Scale(settings_frame, from_=1, to=50, orient="horizontal", bg="#34495e", fg="#ecf0f1", highlightthickness=0).pack(fill="x", padx=10)

tk.Label(settings_frame, text="Deadzone Size", bg="#34495e", fg="#bdc3c7").pack(anchor="w", padx=10, pady=(10,0))
tk.Scale(settings_frame, from_=1, to=20, orient="horizontal", bg="#34495e", fg="#ecf0f1", highlightthickness=0).pack(fill="x", padx=10, pady=(0,10))

# Status / Quit
tk.Button(root, text="FORCE QUIT", command=quit_program, bg="#c0392b", fg="white", font=("Segoe UI", 12, "bold"), height=2).pack(fill="x", side="bottom", padx=20, pady=20)

# --- START BOTH SYSTEMS ---
print("Starting FaceAid Dashboard...")
update_camera() # Run the first camera frame
root.mainloop() # Start the GUI loop (which now contains the camera loop)