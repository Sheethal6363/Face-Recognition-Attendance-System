from datetime import datetime, timezone
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    usn = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(80), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(10), nullable=False)
    face_image = db.Column(db.String(255), nullable=True)
    face_encoding = db.Column(db.Text, nullable=True)  # Stored as JSON string
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    attendances = db.relationship('Attendance', backref='student_ref', lazy=True, cascade="all, delete-orphan")

    def get_encoding_list(self):
        """Returns the face encoding as a list of floats, or None if not set."""
        if not self.face_encoding:
            return None
        try:
            return json.loads(self.face_encoding)
        except (ValueError, TypeError):
            return None

    def set_encoding_list(self, encoding):
        """Accepts a numpy array or python list and stores it as JSON string."""
        if encoding is None:
            self.face_encoding = None
            return
        if hasattr(encoding, 'tolist'):
            encoding = encoding.tolist()
        self.face_encoding = json.dumps(encoding)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'usn': self.usn,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'semester': self.semester,
            'section': self.section,
            'face_image': self.face_image,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<Student {self.name} ({self.usn})>'


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    usn = db.Column(db.String(30), nullable=False, index=True)
    date = db.Column(db.String(10), nullable=False, index=True)  # YYYY-MM-DD
    time = db.Column(db.String(8), nullable=False)               # HH:MM:SS
    status = db.Column(db.String(20), default='Present', nullable=False)
    confidence = db.Column(db.Float, default=0.0, nullable=False) # e.g. 94.5 %
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Database-level unique constraint to prevent duplicate attendance for same student on same day
    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='uq_student_daily_attendance'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'usn': self.usn,
            'date': self.date,
            'time': self.time,
            'status': self.status,
            'confidence': round(self.confidence, 1),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<Attendance {self.usn} on {self.date} at {self.time}>'
