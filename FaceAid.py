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

# --- 1. GLOBAL SETTINGS (DEFAULTS) ---
pyautogui.FAILSAFE = False

# These will now be controlled by the Sliders
SENSITIVITY = 25.0       # Speed multiplier
DEADZONE_SIZE = 0.06     # Safe box size (0.0 to 0.2)
SMILE_THRESHOLD = 0.45   # How wide to smile to pause
IS_MUTED = False         # Audio toggle

# Fixed Settings (Not on sliders for simplicity)
BLINK_THRESHOLD = 0.012
MOUTH_THRESHOLD = 0.05
DOUBLE_BLINK_TIME = 0.6
EYES_CLOSED_TIME = 3.0
PAUSE_TOGGLE_TIME = 1.2

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

# Pause Variables
is_paused = False
smile_start = None
pause_beep_done = False

# --- 3. HELPER FUNCTIONS ---
def get_dist(p1, p2):
    return np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p2.x, p2.y]))

def calculate_ear(landmarks):
    left = get_dist(landmarks[159], landmarks[145])
    right = get_dist(landmarks[386], landmarks[374])
    return (left + right) / 2.0

def calculate_smile_ratio(landmarks):
    mouth_width = get_dist(landmarks[61], landmarks[291])
    face_width = get_dist(landmarks[234], landmarks[454])
    if face_width == 0: return 0
    return mouth_width / face_width

# Wrapper for sound to handle Mute logic
def play_sound(freq, duration):
    if not IS_MUTED:
        winsound.Beep(freq, duration)

def quit_program():
    print("Exiting...")
    cam.release()
    cv2.destroyAllWindows()
    root.destroy()
    exit()

# --- 4. GUI UPDATE FUNCTIONS (SLIDER CALLBACKS) ---
def update_sensitivity(val):
    global SENSITIVITY
    SENSITIVITY = float(val)

def update_deadzone(val):
    global DEADZONE_SIZE
    # Slider gives 1-20, we want 0.01 to 0.20
    DEADZONE_SIZE = float(val) / 100.0

def update_smile_thresh(val):
    global SMILE_THRESHOLD
    # Slider gives 0.1 to 1.0 directly
    SMILE_THRESHOLD = float(val)

def toggle_mute():
    global IS_MUTED
    IS_MUTED = bool(mute_var.get())

# --- 5. THE MAIN LOOP ---
def update_camera():
    global blink_count, last_blink_end, eyes_closed_start, is_eyes_closed, last_beep, keyboard_trigger
    global is_paused, smile_start, pause_beep_done

    ret, frame = cam.read()
    if ret:
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        frame_h, frame_w, _ = frame.shape
        
        # Draw Safe Box (Dynamic Size based on Slider)
        center_x, center_y = int(frame_w / 2), int(frame_h / 2)
        box_w = int(DEADZONE_SIZE * frame_w)
        # We use a slightly smaller ratio for height typically, or just square
        box_h = int((DEADZONE_SIZE * 0.8) * frame_h) 
        
        box_color = (255, 200, 0) if is_paused else (255, 255, 255)
        cv2.rectangle(frame, (center_x - box_w, center_y - box_h), (center_x + box_w, center_y + box_h), box_color, 1)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            nose = landmarks[4]
            
            # --- A. CHECK PAUSE TOGGLE (SMILE) ---
            smile_ratio = calculate_smile_ratio(landmarks)
            
            # Use Dynamic SMILE_THRESHOLD from Slider
            if smile_ratio > SMILE_THRESHOLD:
                if smile_start is None:
                    smile_start = time.time()
                
                elapsed = time.time() - smile_start
                if elapsed > PAUSE_TOGGLE_TIME:
                    if not pause_beep_done:
                        is_paused = not is_paused
                        if is_paused:
                            play_sound(400, 300)
                            print("SYSTEM PAUSED")
                        else:
                            play_sound(1200, 300)
                            print("SYSTEM RESUMED")
                        pause_beep_done = True
                
                cv2.putText(frame, f"SMILE: {elapsed:.1f}", (50, 50), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 255), 2)
            else:
                smile_start = None
                pause_beep_done = False

            # --- B. IF PAUSED, STOP INPUTS ---
            if is_paused:
                cv2.putText(frame, "PAUSED", (center_x - 100, center_y), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 165, 255), 3)
                cv2.putText(frame, "(Smile to Resume)", (center_x - 120, center_y + 40), cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 165, 255), 1)
                
            else:
                # --- ACTIVE MODE ---
                dx = nose.x - 0.5
                dy = nose.y - 0.5
                move_x = 0
                move_y = 0
                
                # Use Dynamic DEADZONE_SIZE
                deadzone_x = DEADZONE_SIZE
                deadzone_y = DEADZONE_SIZE * 0.8 # height is usually tighter
                
                if abs(dx) > deadzone_x:
                    val = dx - deadzone_x if dx > 0 else dx + deadzone_x
                    move_x = val * SENSITIVITY * 50 # Use Dynamic SENSITIVITY
                
                if abs(dy) > deadzone_y:
                    val = dy - deadzone_y if dy > 0 else dy + deadzone_y
                    move_y = val * (SENSITIVITY * 1.4) * 50 # Y axis usually needs more speed

                if not is_eyes_closed:
                    if move_x != 0 or move_y != 0:
                        curr_x, curr_y = pyautogui.position()
                        pyautogui.moveTo(curr_x + move_x, curr_y + move_y)
                        nose_px = (int(nose.x * frame_w), int(nose.y * frame_h))
                        cv2.line(frame, (center_x, center_y), nose_px, (0, 255, 0), 2)
                    else:
                        nose_px = (int(nose.x * frame_w), int(nose.y * frame_h))
                        cv2.circle(frame, nose_px, 5, (0, 0, 255), -1)

                # Gestures
                ear = calculate_ear(landmarks)
                
                # Exit
                if ear < BLINK_THRESHOLD: 
                    if not is_eyes_closed:
                        eyes_closed_start = time.time()
                        is_eyes_closed = True
                    
                    elapsed = time.time() - eyes_closed_start
                    countdown = EYES_CLOSED_TIME - elapsed
                    curr_sec = int(elapsed)
                    
                    if curr_sec > last_beep and curr_sec < EYES_CLOSED_TIME:
                        play_sound(500 + (curr_sec * 500), 200)
                        last_beep = curr_sec
                    
                    if countdown <= 0:
                        play_sound(2000, 800)
                        quit_program()
                    cv2.putText(frame, f"EXIT: {countdown:.1f}", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
                else: 
                    if is_eyes_closed:
                        if (time.time() - eyes_closed_start) < 1.0: 
                            curr_time = time.time()
                            if curr_time - last_blink_end < DOUBLE_BLINK_TIME:
                                blink_count += 1
                            else:
                                blink_count = 1
                            last_blink_end = curr_time
                        is_eyes_closed = False
                        eyes_closed_start = None
                        last_beep = 0

                # Clicks
                if blink_count > 0 and (time.time() - last_blink_end > DOUBLE_BLINK_TIME):
                    if blink_count == 2:
                        print("Click")
                        play_sound(1000, 100)
                        pyautogui.mouseDown()
                        time.sleep(0.1) 
                        pyautogui.mouseUp()
                    elif blink_count == 3:
                        print("Backspace")
                        play_sound(600, 100)
                        pyautogui.press('backspace')
                    blink_count = 0

                # Keyboard
                mar = get_dist(landmarks[13], landmarks[14])
                if mar > MOUTH_THRESHOLD and smile_ratio < 0.5:
                    keyboard_trigger += 1
                    if keyboard_trigger == 10: 
                        print("Keyboard")
                        play_sound(800, 100)
                        try:
                            subprocess.Popen("osk", shell=True)
                        except: pass
                        keyboard_trigger = 0
                else:
                    keyboard_trigger = 0

        cv2.imshow('FaceAid Camera View', frame)
        cv2.waitKey(1)

    root.after(10, update_camera)

# --- 6. GUI SETUP (DASHBOARD) ---
root = tk.Tk()
root.title("FaceAid Configuration")
root.geometry("400x750") # Taller window for more sliders
root.configure(bg="#2c3e50")

# Header
tk.Label(root, text="FaceAid Control", font=("Segoe UI", 20, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(pady=15)

# Instructions
instr_frame = tk.LabelFrame(root, text=" Commands ", font=("Segoe UI", 12, "bold"), bg="#34495e", fg="#ecf0f1", relief="flat")
instr_frame.pack(fill="x", padx=20, pady=5)
guide_text = (
    "HEAD: Tilt to move mouse\n"
    "CENTER: Stop mouse\n"
    "SMILE: Pause/Resume\n"
    "BLINK x2: Left Click\n"
    "BLINK x3: Backspace\n"
    "MOUTH: Open for Keyboard"
)
tk.Label(instr_frame, text=guide_text, justify="left", font=("Segoe UI", 10), bg="#34495e", fg="#ecf0f1").pack(anchor="w", padx=10, pady=5)

# --- CONTROL PANEL ---
settings_frame = tk.LabelFrame(root, text=" Settings ", font=("Segoe UI", 12, "bold"), bg="#34495e", fg="#ecf0f1", relief="flat")
settings_frame.pack(fill="x", padx=20, pady=10)

# 1. Sensitivity Slider
tk.Label(settings_frame, text="Mouse Speed", bg="#34495e", fg="#bdc3c7").pack(anchor="w", padx=10)
scale_sens = tk.Scale(settings_frame, from_=5, to=80, orient="horizontal", 
                      bg="#34495e", fg="#ecf0f1", highlightthickness=0, command=update_sensitivity)
scale_sens.set(SENSITIVITY) # Set default
scale_sens.pack(fill="x", padx=10)

# 2. Deadzone Slider
tk.Label(settings_frame, text="Deadzone Size (Safe Box)", bg="#34495e", fg="#bdc3c7").pack(anchor="w", padx=10, pady=(10,0))
scale_dead = tk.Scale(settings_frame, from_=1, to=15, orient="horizontal", 
                      bg="#34495e", fg="#ecf0f1", highlightthickness=0, command=update_deadzone)
scale_dead.set(int(DEADZONE_SIZE*100)) # Set default
scale_dead.pack(fill="x", padx=10)

# 3. Smile Threshold Slider
tk.Label(settings_frame, text="Smile Sensitivity (Pause)", bg="#34495e", fg="#bdc3c7").pack(anchor="w", padx=10, pady=(10,0))
scale_smile = tk.Scale(settings_frame, from_=0.3, to=0.8, resolution=0.05, orient="horizontal", 
                       bg="#34495e", fg="#ecf0f1", highlightthickness=0, command=update_smile_thresh)
scale_smile.set(SMILE_THRESHOLD)
scale_smile.pack(fill="x", padx=10)

# 4. Audio Control
mute_var = tk.BooleanVar()
chk_mute = tk.Checkbutton(settings_frame, text="Mute All Sounds", variable=mute_var, 
                          bg="#34495e", fg="#ecf0f1", selectcolor="#2c3e50", 
                          activebackground="#34495e", activeforeground="#ecf0f1", command=toggle_mute)
chk_mute.pack(anchor="w", padx=10, pady=15)

# Status / Quit
tk.Button(root, text="FORCE QUIT", command=quit_program, bg="#c0392b", fg="white", font=("Segoe UI", 12, "bold"), height=2).pack(fill="x", side="bottom", padx=20, pady=20)

print("Starting FaceAid Final...")
update_camera() 
root.mainloop()