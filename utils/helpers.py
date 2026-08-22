import os
import re
import base64
import functools
import cv2
import numpy as np
from flask import session, redirect, url_for, flash, request, jsonify

def admin_required(f):
    """
    Decorator to ensure admin is logged in before accessing protected routes.
    Redirects unauthenticated web requests to /login and returns 401 for JSON API calls.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
            flash('Please log in as Administrator to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def decode_base64_image(base64_string: str):
    """
    Decodes a base64 encoded image string (e.g. from canvas or file reader)
    into an OpenCV BGR numpy array.
    """
    try:
        if not base64_string:
            return None
        # Strip header if present (e.g., data:image/jpeg;base64,...)
        if ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        
        image_bytes = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image_bgr
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None

def sanitize_filename(name: str) -> str:
    """Sanitize string for safe filenames."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip())

def save_face_image(image_bgr, usn: str, target_dir: str) -> str:
    """
    Saves the student's face image to disk and returns the relative filename.
    """
    os.makedirs(target_dir, exist_ok=True)
    clean_usn = sanitize_filename(usn)
    filename = f"{clean_usn}.jpg"
    filepath = os.path.join(target_dir, filename)
    
    cv2.imwrite(filepath, image_bgr)
    return filename
