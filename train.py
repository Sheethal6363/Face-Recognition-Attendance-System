import cv2
import numpy as np
import os
import pickle

dataset_path = r"D:\Face_recognition_attendance_system\filtered_dataset"
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
model_save_path = "trainer.yml"
labels_save_path = "labels.pkl"

def get_images_and_labels(dataset_path):
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print(f"[ERROR] Could not load cascade from {cascade_path}")
        return [], [], {}
    
    faces = []
    labels = []
    label_dict = {}
    current_label = 0

    print("[INFO] Starting data preprocessing...")
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset path '{dataset_path}' does not exist.")
        return [], [], {}

    person_folders = [f for f in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, f))]
    
    for person_name in person_folders:
        person_dir = os.path.join(dataset_path, person_name)
        images = [img for img in os.listdir(person_dir) if img.endswith((".jpg", ".png", ".jpeg"))]
        
        # 9. Ignore folders with fewer than 2 images (though filtered dataset is supposed to guarantee this)
        if len(images) < 2:
            continue
            
        label_dict[current_label] = person_name
        has_face = False
        
        for image_name in images:
            image_path = os.path.join(person_dir, image_name)
            try:
                img = cv2.imread(image_path)
                if img is None: continue
                # Convert to grayscale
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Detect face
                detected_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                # Extract face region and resize
                for (x, y, w, h) in detected_faces:
                    face_roi = gray[y:y+h, x:x+w]
                    face_resized = cv2.resize(face_roi, (200, 200))
                    faces.append(face_resized)
                    labels.append(current_label)
                    has_face = True
            except Exception as e:
                # 8. Skip corrupted images
                print(f"[ERROR] Skipping corrupted image {image_path}: {e}")
                
        if has_face:
            current_label += 1

    return faces, labels, label_dict

def train_model():
    print("[INFO] Extracting faces and labels...")
    faces, labels, label_dict = get_images_and_labels(dataset_path)
    
    # 8. Handle empty training data safely
    if len(faces) == 0:
        print("[ERROR] No valid faces found to train. Please populate the dataset correctly.")
        return
        
    print(f"[INFO] Training LBPH model with {len(faces)} faces from {len(label_dict)} people...")
    
    # OpenCV LBPHFaceRecognizer Usage
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    
    # Save the trained model
    recognizer.save(model_save_path)
    
    # Save the label mapping as a PKL file
    with open(labels_save_path, 'wb') as f:
        pickle.dump(label_dict, f)
        
    print(f"[SUCCESS] Training completed. Model saved to '{model_save_path}'")
    print(f"[SUCCESS] Labels dictionary saved to '{labels_save_path}'")

if __name__ == "__main__":
    train_model()
