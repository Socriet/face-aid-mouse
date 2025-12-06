# FACEAID - HANDS-FREE MOUSE INTERFACE

FaceAid is a Python application that allows you to control your computer mouse using only head movements and facial expressions. It is designed as an assistive tool for hands-free computer interaction.



## REQUIREMENTS

You need **Python** installed on your system.
The following libraries are required:

* `opencv-python`
* `mediapipe`
* `pyautogui`
* `numpy`

To install them, run the following command in your terminal:

pip install opencv-python mediapipe pyautogui numpy

## HOW TO RUN

1. Open your terminal or command prompt in the project folder.
2. Run the final script:

    python FaceAid_Final.py

## CONTROLS

The application uses a "Joystick" method for mouse movement.

| Action | Gesture |
| :--- | :--- |
| **Move Mouse** | Tilt your head (look away from center). |
| **Stop Mouse** | Keep your head in the center "Safe Box". |
| **Left Click** | Double Blink (fast). |
| **Backspace** | Triple Blink. |
| **Open Keyboard** | Open your mouth wide (jaw drop). |
| **Pause / Resume** | Smile wide and hold for **1 second**. |
| **EXIT APPLICATION** | Close your eyes and hold for **3 seconds**. |

## SETTINGS DASHBOARD

When you run the program, a configuration window will open alongside the camera view.
You can adjust the following settings in real-time:

* **Mouse Speed:** Controls how fast the cursor accelerates.
* **Deadzone Size:** Adjusts the size of the safe area in the center where the mouse stops.
* **Smile Sensitivity:** Adjusts how wide you must smile to trigger the Pause function.
* **Mute:** Check this box to silence all audio feedback beeps.

## AUTHORS

Project developed for **Computacao Visual**.

* Student A87946
* Student A86829
