from .auth_routes import auth_bp
from .dashboard_routes import dashboard_bp
from .student_routes import student_bp
from .attendance_routes import attendance_bp

__all__ = ['auth_bp', 'dashboard_bp', 'student_bp', 'attendance_bp']
