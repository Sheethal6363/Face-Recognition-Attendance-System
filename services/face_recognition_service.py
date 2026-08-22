import os
import json
import logging
import cv2
import numpy as np

# Try importing face_recognition
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    def __init__(self, match_threshold=0.50):
        self.match_threshold = match_threshold
        self.known_face_encodings = []
        self.known_face_metadata = []
        self._is_loaded = False
        
        # Load OpenCV face cascade as auxiliary detector
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def load_known_faces(self, students=None):
        """
        Loads all active students' face encodings into memory cache.
        If students is None, queries Student model from the database.
        """
        if students is None:
            from database.models import Student
            students = Student.query.filter_by(is_active=True).all()

        encodings = []
        metadata = []

        for s in students:
            encoding_list = s.get_encoding_list()
            if encoding_list is not None and len(encoding_list) > 0:
                encodings.append(np.array(encoding_list, dtype=np.float64))
                metadata.append({
                    'id': s.id,
                    'name': s.name,
                    'usn': s.usn,
                    'department': s.department,
                    'section': s.section,
                    'face_image': s.face_image
                })

        self.known_face_encodings = encodings
        self.known_face_metadata = metadata
        self._is_loaded = True
        logger.info(f"Loaded {len(self.known_face_encodings)} student face encodings into memory.")
        return len(self.known_face_encodings)

    def reload_encodings(self):
        """Reloads known faces from database."""
        return self.load_known_faces()

    def detect_faces_opencv(self, frame_bgr):
        """Auxiliary face detector using OpenCV Haar Cascades."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        # Convert (x, y, w, h) to (top, right, bottom, left)
        boxes = []
        for (x, y, w, h) in faces:
            boxes.append((y, x + w, y + h, x))
        return boxes

    def detect_faces(self, frame_rgb):
        """Detect face locations using face_recognition with OpenCV fallback."""
        if HAS_FACE_RECOGNITION:
            try:
                return face_recognition.face_locations(frame_rgb)
            except Exception as e:
                logger.warning(f"face_recognition error: {e}. Falling back to OpenCV cascade.")
        
        # Fallback to OpenCV
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return self.detect_faces_opencv(frame_bgr)

    def encode_face_from_image(self, image_bgr):
        """
        Validates that exactly one face exists in the image and returns its 128-d encoding.
        Returns: (success: bool, message: str, encoding: list or None, location: tuple or None)
        """
        if image_bgr is None or image_bgr.size == 0:
            return False, "Invalid image data provided.", None, None

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        
        if HAS_FACE_RECOGNITION:
            locations = face_recognition.face_locations(image_rgb)
            if len(locations) == 0:
                return False, "No face detected in the image. Please align your face inside the camera view.", None, None
            if len(locations) > 1:
                return False, f"Multiple faces ({len(locations)}) detected. Please ensure only one person is visible.", None, None

            encodings = face_recognition.face_encodings(image_rgb, known_face_locations=locations)
            if len(encodings) == 0:
                return False, "Could not extract facial features. Please ensure good lighting.", None, None

            encoding_list = encodings[0].tolist()
            return True, "Face successfully detected and encoded.", encoding_list, locations[0]
        else:
            # Simulated 128-d encoding fallback when face_recognition is not available
            locations = self.detect_faces_opencv(image_bgr)
            if len(locations) == 0:
                return False, "No face detected. Please ensure your face is clearly visible.", None, None
            if len(locations) > 1:
                return False, f"Multiple faces ({len(locations)}) detected. Please ensure only one person is in the frame.", None, None

            # Generate normalized histogram feature vector (128 dimensions) as fallback
            top, right, bottom, left = locations[0]
            face_roi = image_bgr[max(0, top):bottom, max(0, left):right]
            if face_roi.size == 0:
                return False, "Face region could not be cropped.", None, None
            
            resized_roi = cv2.resize(face_roi, (64, 64))
            gray = cv2.cvtColor(resized_roi, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [128], [0, 256])
            norm_hist = cv2.normalize(hist, hist).flatten().tolist()
            return True, "Face detected and encoded (standard OpenCV mode).", norm_hist, locations[0]

    def recognize_faces_in_frame(self, frame_bgr, threshold=None):
        """
        Processes a video frame, detects all visible faces, matches them against known encodings,
        and returns recognition results with bounding boxes and confidence scores.
        
        Returns: list of dicts:
        [
            {
                'recognized': bool,
                'student_id': int or None,
                'name': str,
                'usn': str or None,
                'department': str or None,
                'confidence': float (0-100),
                'distance': float,
                'box': (top, right, bottom, left) # in original frame coordinates
            }, ...
        ]
        """
        if threshold is None:
            threshold = self.match_threshold

        if not self._is_loaded:
            self.load_known_faces()

        # Optimize: downscale frame by 4x for fast recognition
        small_frame = cv2.resize(frame_bgr, (0, 0), fx=0.25, fy=0.25)
        small_frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        results = []

        if HAS_FACE_RECOGNITION and len(self.known_face_encodings) > 0:
            face_locations = face_recognition.face_locations(small_frame_rgb)
            face_encodings = face_recognition.face_encodings(small_frame_rgb, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Scale bounding box coordinates back to original size (4x)
                orig_box = (top * 4, right * 4, bottom * 4, left * 4)

                # Compute Euclidean face distances
                distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                if len(distances) > 0:
                    best_match_index = np.argmin(distances)
                    min_dist = float(distances[best_match_index])

                    if min_dist <= threshold:
                        meta = self.known_face_metadata[best_match_index]
                        # Calculate confidence percentage (linear mapping: dist=0 -> 100%, dist=threshold -> 70%)
                        conf_pct = max(0.0, min(100.0, (1.0 - (min_dist / (threshold * 1.5))) * 100.0))
                        
                        results.append({
                            'recognized': True,
                            'student_id': meta['id'],
                            'name': meta['name'],
                            'usn': meta['usn'],
                            'department': meta['department'],
                            'confidence': round(conf_pct, 1),
                            'distance': round(min_dist, 4),
                            'box': orig_box
                        })
                    else:
                        results.append({
                            'recognized': False,
                            'student_id': None,
                            'name': 'Unknown Person',
                            'usn': None,
                            'department': None,
                            'confidence': 0.0,
                            'distance': round(min_dist, 4),
                            'box': orig_box
                        })
                else:
                    results.append({
                        'recognized': False,
                        'student_id': None,
                        'name': 'Unknown Person',
                        'usn': None,
                        'department': None,
                        'confidence': 0.0,
                        'distance': 1.0,
                        'box': orig_box
                    })

        elif HAS_FACE_RECOGNITION and len(self.known_face_encodings) == 0:
            # No registered students in DB
            face_locations = face_recognition.face_locations(small_frame_rgb)
            for (top, right, bottom, left) in face_locations:
                orig_box = (top * 4, right * 4, bottom * 4, left * 4)
                results.append({
                    'recognized': False,
                    'student_id': None,
                    'name': 'No Registered Students',
                    'usn': None,
                    'department': None,
                    'confidence': 0.0,
                    'distance': 1.0,
                    'box': orig_box
                })

        else:
            # Fallback when face_recognition is not available
            boxes = self.detect_faces_opencv(frame_bgr)
            for (top, right, bottom, left) in boxes:
                results.append({
                    'recognized': False,
                    'student_id': None,
                    'name': 'Face Detected',
                    'usn': None,
                    'department': None,
                    'confidence': 50.0,
                    'distance': 0.5,
                    'box': (top, right, bottom, left)
                })

        return results

    def draw_recognition_overlays(self, frame_bgr, recognition_results):
        """Draws bounding boxes and labels onto the frame for live display."""
        for res in recognition_results:
            top, right, bottom, left = res['box']
            recognized = res['recognized']

            # Box color: Green for recognized, Red for unknown
            color = (46, 204, 113) if recognized else (52, 73, 235)  # BGR

            # Draw rectangle with rounded aesthetic corners
            cv2.rectangle(frame_bgr, (left, top), (right, bottom), color, 2)

            # Draw top label bar
            label = f"{res['name']} ({res['confidence']}%)" if recognized else res['name']
            if res.get('usn') and recognized:
                label_sub = f"USN: {res['usn']}"
            else:
                label_sub = None

            # Label background banner
            banner_height = 42 if label_sub else 26
            banner_top = max(0, top - banner_height)
            cv2.rectangle(frame_bgr, (left, banner_top), (right, top), color, cv2.FILLED)

            # Draw text
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame_bgr, label, (left + 6, banner_top + 18), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            if label_sub:
                cv2.putText(frame_bgr, label_sub, (left + 6, banner_top + 34), font, 0.42, (240, 240, 240), 1, cv2.LINE_AA)

        return frame_bgr

# Singleton instance
face_service = FaceRecognitionService()
