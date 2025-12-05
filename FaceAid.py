#Added configuration pop-up
import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import winsound
import os
import subprocess
import tkinter as tk

# --- 1. SAFETY & SETUP ---
pyautogui.FAILSAFE = False
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- 2. "SAFE BOX" CONFIGURATION ---
# The "Deadzone" is now a box. 
# 0.05 means you can move 5% of the screen width/height without triggering the mouse.
DEADZONE_X = 0.06  # Horizontal "wiggle room" (Reading text)
DEADZONE_Y = 0.05  # Vertical "wiggle room"

# Acceleration (How fast it moves once you leave the box)
SPEED_SENSITIVITY_X = 25.0
SPEED_SENSITIVITY_Y = 35.0 # Vertical often needs to be faster

# Gestures
BLINK_THRESHOLD = 0.012
MOUTH_THRESHOLD = 0.04
DOUBLE_BLINK_TIME = 0.6
EYES_CLOSED_TIME = 3.0

# State Variables
cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
screen_w, screen_h = pyautogui.size()
blink_count = 0
last_blink_end = 0
eyes_closed_start = None
is_eyes_closed = False
last_beep = 0
keyboard_trigger = 0

# Helper Functions
def get_dist(p1, p2):
    return np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p2.x, p2.y]))

def calculate_ear(landmarks):
    left = get_dist(landmarks[159], landmarks[145])
    right = get_dist(landmarks[386], landmarks[374])
    return (left + right) / 2.0

def show_configurations():
    root = tk.Tk()
    root.title("FaceAid - Setup & Guide")
    root.geometry("850x600")
    root.configure(bg="#2c3e50") # Dark ergonomic background

    # Header
    header_frame = tk.Frame(root, bg="#2c3e50")
    header_frame.pack(pady=20)
    
    title = tk.Label(header_frame, text="FaceAid Setup", 
                     font=("Segoe UI", 28, "bold"), bg="#2c3e50", fg="#ecf0f1")
    title.pack()
    
    subtitle = tk.Label(header_frame, text="Head-Tracking Mouse Controller", 
                        font=("Segoe UI", 12), bg="#2c3e50", fg="#bdc3c7")
    subtitle.pack()

    # Main content area (Grid)
    content_frame = tk.Frame(root, bg="#2c3e50")
    content_frame.pack(fill="both", expand=True, padx=30, pady=10)

    # Left Column: instructions
    instr_frame = tk.LabelFrame(content_frame, text="  User Guide  ", 
                                font=("Segoe UI", 12, "bold"), bg="#34495e", fg="#ecf0f1", 
                                relief="flat", padx=15, pady=15)
    instr_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    guide_text = (
        "1. NAVIGATION (Joystick Mode)\n"
        "   • CENTER HEAD: Stop Mouse (Safe Zone)\n"
        "   • TILT HEAD: Move Mouse\n"
        "   • TILT FURTHER: Increase Speed\n\n"
        "2. CLICKS & ACTIONS\n"
        "   • LEFT CLICK: Double Blink (Fast)\n"
        "   • GO BACK: Triple Blink\n"
        "   • KEYBOARD: Open Mouth Wide\n\n"
        "3. EMERGENCY EXIT\n"
        "   • Close eyes for 3 seconds."
    )
    
    lbl_instr = tk.Label(instr_frame, text=guide_text, justify="left", 
                         font=("Segoe UI", 11), bg="#34495e", fg="#ecf0f1")
    lbl_instr.pack(anchor="w")

    # Left Column: Settings (Visual Only)
    settings_frame = tk.LabelFrame(content_frame, text="  Sensitivity Settings  ", 
                                   font=("Segoe UI", 12, "bold"), bg="#34495e", fg="#ecf0f1", 
                                   relief="flat", padx=15, pady=15)
    settings_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

    # Slider 1: Speed
    lbl_speed = tk.Label(settings_frame, text="Mouse Speed", 
                         font=("Segoe UI", 10, "bold"), bg="#34495e", fg="#bdc3c7")
    lbl_speed.pack(anchor="w", pady=(10, 0))
    
    scale_speed = tk.Scale(settings_frame, from_=1, to=50, orient="horizontal", 
                           bg="#34495e", fg="#ecf0f1", highlightthickness=0, 
                           troughcolor="#2c3e50", activebackground="#27ae60")
    scale_speed.set(25) # Default visual value
    scale_speed.pack(fill="x", pady=5)

    # Slider 2: Deadzone
    lbl_deadzone = tk.Label(settings_frame, text="Safe Box Size (Deadzone)", 
                            font=("Segoe UI", 10, "bold"), bg="#34495e", fg="#bdc3c7")
    lbl_deadzone.pack(anchor="w", pady=(20, 0))
    
    scale_deadzone = tk.Scale(settings_frame, from_=1, to=20, orient="horizontal", 
                              bg="#34495e", fg="#ecf0f1", highlightthickness=0,
                              troughcolor="#2c3e50", activebackground="#27ae60")
    scale_deadzone.set(6) # Default visual value
    scale_deadzone.pack(fill="x", pady=5)

    # Note
    lbl_note = tk.Label(settings_frame, text="(Settings currently locked for Beta)", 
                        font=("Segoe UI", 9, "italic"), bg="#34495e", fg="#95a5a6")
    lbl_note.pack(pady=(30, 0))

    # Footer: Start Button
    btn_start = tk.Button(root, text="LAUNCH FACEAID", font=("Segoe UI", 14, "bold"), 
                          bg="#27ae60", fg="white", activebackground="#2ecc71", activeforeground="white",
                          relief="flat", cursor="hand2", height=2,
                          command=root.destroy)
    btn_start.pack(fill="x", side="bottom", padx=30, pady=30)

    root.mainloop()

print("FaceAid 'Safe Box' Mode Started!")

show_configurations()

while True:
    ret, frame = cam.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    frame_h, frame_w, _ = frame.shape
    
    # Draw Safe Box (Visual Guide)
    center_x, center_y = int(frame_w / 2), int(frame_h / 2)
    box_w = int(DEADZONE_X * frame_w)
    box_h = int(DEADZONE_Y * frame_h)
    
    # Draw Rectangle (White = Safe Zone)
    cv2.rectangle(frame, 
                  (center_x - box_w, center_y - box_h), 
                  (center_x + box_w, center_y + box_h), 
                  (255, 255, 255), 1)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        nose = landmarks[4]
        
        # Calculate raw offset from center
        dx = nose.x - 0.5
        dy = nose.y - 0.5
        
        move_x = 0
        move_y = 0
        
        # X axis logic 
        if abs(dx) > DEADZONE_X:
            # We subtract the deadzone so motion starts smoothly from 0
            if dx > 0: # Looking Right
                val = dx - DEADZONE_X
            else:      # Looking Left
                val = dx + DEADZONE_X
            move_x = val * SPEED_SENSITIVITY_X * 50

        # y axis logic 
        if abs(dy) > DEADZONE_Y:
            if dy > 0: # Looking Down
                val = dy - DEADZONE_Y
            else:      # Looking Up
                val = dy + DEADZONE_Y
            move_y = val * SPEED_SENSITIVITY_Y * 50

        # Apply Movement
        if not is_eyes_closed:
            # Only apply if there is actual movement intended
            if move_x != 0 or move_y != 0:
                curr_x, curr_y = pyautogui.position()
                pyautogui.moveTo(curr_x + move_x, curr_y + move_y)
                
                # Visual Feedback: Green line showing active push
                nose_px = (int(nose.x * frame_w), int(nose.y * frame_h))
                cv2.line(frame, (center_x, center_y), nose_px, (0, 255, 0), 2)
            else:
                # Visual Feedback: Red Dot (Safe/Stopped)
                nose_px = (int(nose.x * frame_w), int(nose.y * frame_h))
                cv2.circle(frame, nose_px, 5, (0, 0, 255), -1)

        # Gestures
        ear = calculate_ear(landmarks)
        
        # Exit / Blink Logic
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
                print("Exit.")
                break
            cv2.putText(frame, f"EXIT: {countdown:.1f}", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
            
        else: 
            if is_eyes_closed:
                duration = time.time() - eyes_closed_start
                if duration < 1.0:
                    curr_time = time.time()
                    if curr_time - last_blink_end < DOUBLE_BLINK_TIME:
                        blink_count += 1
                    else:
                        blink_count = 1
                    last_blink_end = curr_time
                is_eyes_closed = False
                eyes_closed_start = None
                last_beep = 0

        if blink_count > 0 and (time.time() - last_blink_end > DOUBLE_BLINK_TIME):
            if blink_count == 2:
                print("Click")
                winsound.Beep(1000, 100)
                pyautogui.click()
            elif blink_count == 3:
                print("Back")
                winsound.Beep(600, 100)
                pyautogui.press('browserback')
            blink_count = 0

# Keyboard Gestures
        mar = get_dist(landmarks[13], landmarks[14])
        
        # Check if mouth is open wider than the threshold
        if mar > MOUTH_THRESHOLD:
            keyboard_trigger += 1
            
            # trigger count is 10 (faster than 15)
            if keyboard_trigger == 10: 
                print("Action: Keyboard")
                winsound.Beep(800, 100) # Short beep (0.1s) to minimize lag
                
                # "Fire and Forget" launch - prevents video freeze
                try:
                    subprocess.Popen("osk", shell=True)
                except Exception as e:
                    print("Error opening keyboard:", e)
                    
                keyboard_trigger = 0 # Reset counter
        else:
            keyboard_trigger = 0

    cv2.imshow('FaceAid SafeBox', frame)
    if cv2.waitKey(1) == 27: break

cam.release()
cv2.destroyAllWindows()