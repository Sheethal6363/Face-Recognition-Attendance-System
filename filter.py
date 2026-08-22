import os
import shutil

# Path to your dataset
dataset_path = r"D:\Face_recognition_attendance_system\lfw_funneled"

# New filtered dataset folder
filtered_path = r"D:\Face_recognition_attendance_system\filtered_dataset"

# Create folder if not exists
os.makedirs(filtered_path, exist_ok=True)

count_kept = 0
count_removed = 0

for person_name in os.listdir(dataset_path):
    person_folder = os.path.join(dataset_path, person_name)

    if not os.path.isdir(person_folder):
        continue

    images = [img for img in os.listdir(person_folder) if img.endswith((".jpg", ".png", ".jpeg"))]

    # ✅ Keep only if >= 2 images
    if len(images) >= 2:
        shutil.copytree(person_folder, os.path.join(filtered_path, person_name), dirs_exist_ok=True)
        count_kept += 1
    else:
        count_removed += 1

print("Filtering completed!")
print(f"People kept: {count_kept}")
print(f"People removed: {count_removed}")