import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'face-attend-super-secret-key-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload and Face Directories
    KNOWN_FACES_DIR = os.path.join(BASE_DIR, 'known_faces')
    EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    
    # Face Recognition Parameters
    FACE_MATCH_THRESHOLD = float(os.environ.get('FACE_MATCH_THRESHOLD', 0.50))
    ATTENDANCE_COOLDOWN_SECONDS = int(os.environ.get('ATTENDANCE_COOLDOWN_SECONDS', 30))
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

def _get_db_uri(default_sqlite=True):
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            return db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    if default_sqlite:
        return f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'attendance.db')}"
    return None

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _get_db_uri()

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    ATTENDANCE_COOLDOWN_SECONDS = 0

class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _get_db_uri()

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
