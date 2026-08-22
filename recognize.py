import cv2
import numpy as np
import os
import pickle
import pandas as pd
from datetime import datetime

cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
model_path = "trainer.yml"
labels_path = "labels.pkl"
attendance_file = "attendance.csv"
unknown_log_file = "unknown_logs.csv"

def init_attendance_file():
    """ Initialize required CSV files gracefully before beginning. """
    if not os.path.exists(attendance_file):
        df = pd.DataFrame(columns=['Name', 'Date', 'Time'])
        df.to_csv(attendance_file, index=False)
    if not os.path.exists(unknown_log_file):
        df = pd.DataFrame(columns=['Date', 'Time'])
        df.to_csv(unknown_log_file, index=False)

def log_attendance(name):
    """
    Log attendance logic mapping identity, preventing duplicate 
    marking in an identical session/date format.
    """
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')

    # Bonus: Add unknown face logging
    if name == "Unknown":
        try:
            df = pd.read_csv(unknown_log_file)
        except Exception:
            df = pd.DataFrame(columns=['Date', 'Time'])
        
        new_record = pd.DataFrame([{'Date': date_str, 'Time': time_str}])
        df = pd.concat([df, new_record], ignore_index=True)
        df.to_csv(unknown_log_file, index=False)
        return
        
    try:
        df = pd.read_csv(attendance_file)
    except Exception:
        df = pd.DataFrame(columns=['Name', 'Date', 'Time'])
        
    # Prevent duplicate identical day entries
    today_records = df[(df['Name'] == name) & (df['Date'] == date_str)]
    if today_records.empty:
        new_record = pd.DataFrame([{'Name': name, 'Date': date_str, 'Time': time_str}])
        df = pd.concat([df, new_record], ignore_index=True)
        df.to_csv(attendance_file, index=False)
        print(f"[SUCCESS] Marked valid attendance for {name} at {time_str}")

def start_recognition():
    """ Main real time video capture and recognition inference loop """
    if not os.path.exists(model_path) or not os.path.exists(labels_path):
        print(f"[ERROR] Missing {model_path} or {labels_path}. Please run train.py first.")
        return
        
    # Load model and mapping dictionary
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    
    with open(labels_path, 'rb') as f:
        label_dict = pickle.load(f)
        
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print(f"[ERROR] Could not load cascade from {cascade_path}")
        return
        
    video_capture = cv2.VideoCapture(0)
    print("[INFO] Starting real-time webcam feed...")
    print("[NOTICE] Bring window to focus and press 'q' to quit.")
    
    last_unknown_log = datetime.min

    while True:
        ret, frame = video_capture.read()
        if not ret: break
        
        # 9. Use grayscale for faster cascade detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Real-time real scale scanning
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))
        
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            # Must resize to precisely the shape we trained on! (200x200)
            roi_resized = cv2.resize(roi_gray, (200, 200))
            
            # Predict the identity across trained model
            id_, distance = recognizer.predict(roi_resized)
            
            name = "Unknown"
            conf = 0.0
            color = (0, 0, 255) # Red for unknown
            
            # Distance usually ranges from < 50 for very tight matches. 
            # We configure LBPH distance ~75 for solid threshold.
            confidence_threshold = 80
            
            if distance < confidence_threshold:
                name = label_dict.get(id_, "Unknown")
                conf = max(0, min(100, round(100 - distance)))
                if name != "Unknown":
                    color = (0, 255, 0)
                    log_attendance(name)
            else:
                conf = max(0, min(100, round(100 - distance)))
                now = datetime.now()
                # Cooldown so we don't produce 30 "Unknown" logs per second.
                if (now - last_unknown_log).total_seconds() > 5:
                    log_attendance("Unknown")
                    last_unknown_log = now
            
            # 7. UI Display details 
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            label = f"{name} ({conf}%)" if name != "Unknown" else f"Unknown ({conf}%)"
            
            cv2.rectangle(frame, (x, y+h), (x+w, y+h+30), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, label, (x + 5, y+h + 22), font, 0.6, (255, 255, 255), 1)

        cv2.imshow('Face Recognition System', frame)
        
        # Add "Press Q to quit" functionality (Waitkey looks out for the keyboard event)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Quitting application.")
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    init_attendance_file()
    start_recognition()
