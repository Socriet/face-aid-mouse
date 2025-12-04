import cv2
import mediapipe as mp

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
    if not ret: break
    
    frame = cv2.flip(frame, 1) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    frame_h, frame_w, _ = frame.shape

    # Check if a face is found
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        # add logic here

    cv2.imshow('FaceAid SafeBox', frame)
    if cv2.waitKey(1) == 27: break

cam.release()
cv2.destroyAllWindows()