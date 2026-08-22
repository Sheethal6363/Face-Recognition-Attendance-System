from datetime import datetime, date, timedelta
import time
import logging
from database.models import db, Student, Attendance
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class AttendanceService:
    def __init__(self, cooldown_seconds=30):
        self.cooldown_seconds = cooldown_seconds
        # In-memory cooldown cache: {student_id: epoch_timestamp}
        self.last_marked_timestamps = {}

    def is_in_cooldown(self, student_id: int) -> bool:
        """Check if student was recognized recently within cooldown window."""
        now = time.time()
        last_time = self.last_marked_timestamps.get(student_id, 0)
        return (now - last_time) < self.cooldown_seconds

    def mark_attendance(self, student_id: int, confidence: float = 0.0, status: str = 'Present'):
        """
        Marks attendance for a recognized student.
        Validates student existence, cooldown, and duplicate attendance on same day.
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'already_marked': bool,
                'attendance': dict or None
            }
        """
        student = Student.query.get(student_id)
        if not student:
            return {
                'success': False,
                'message': f'Student ID {student_id} not found.',
                'already_marked': False,
                'attendance': None
            }

        if not student.is_active:
            return {
                'success': False,
                'message': f'Student {student.name} is currently inactive.',
                'already_marked': False,
                'attendance': None
            }

        # Check cooldown to prevent excessive processing
        if self.is_in_cooldown(student_id):
            return {
                'success': False,
                'message': f'Cooldown active for {student.name}. Please wait.',
                'already_marked': True,
                'attendance': None
            }

        today_str = date.today().strftime('%Y-%m-%d')
        now_time_str = datetime.now().strftime('%H:%M:%S')

        # Check database for today's entry
        existing = Attendance.query.filter_by(student_id=student.id, date=today_str).first()
        if existing:
            # Update cooldown timestamp to prevent repeated DB checks
            self.last_marked_timestamps[student_id] = time.time()
            return {
                'success': False,
                'message': f'Attendance already marked for {student.name} today.',
                'already_marked': True,
                'attendance': existing.to_dict()
            }

        # Insert new attendance record
        try:
            record = Attendance(
                student_id=student.id,
                name=student.name,
                usn=student.usn,
                date=today_str,
                time=now_time_str,
                status=status,
                confidence=confidence
            )
            db.session.add(record)
            db.session.commit()

            # Record cooldown
            self.last_marked_timestamps[student_id] = time.time()
            logger.info(f"Attendance marked for {student.name} ({student.usn}) at {now_time_str}")

            return {
                'success': True,
                'message': f'Attendance successfully marked for {student.name}!',
                'already_marked': False,
                'attendance': record.to_dict()
            }

        except IntegrityError:
            db.session.rollback()
            self.last_marked_timestamps[student_id] = time.time()
            existing = Attendance.query.filter_by(student_id=student.id, date=today_str).first()
            return {
                'success': False,
                'message': f'Attendance already recorded for {student.name} today.',
                'already_marked': True,
                'attendance': existing.to_dict() if existing else None
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking attendance: {e}")
            return {
                'success': False,
                'message': f'Database error while marking attendance: {str(e)}',
                'already_marked': False,
                'attendance': None
            }

    def get_dashboard_stats(self):
        """Calculates real-time statistics for the dashboard."""
        today_str = date.today().strftime('%Y-%m-%d')

        total_students = Student.query.filter_by(is_active=True).count()
        present_today = Attendance.query.filter_by(date=today_str).count()
        absent_today = max(0, total_students - present_today)
        
        attendance_pct = round((present_today / total_students * 100.0), 1) if total_students > 0 else 0.0

        # Recent 8 attendance entries
        recent_records = Attendance.query.order_by(Attendance.created_at.desc()).limit(8).all()
        recent_list = [r.to_dict() for r in recent_records]

        # 7-day attendance trend data
        trend_dates = []
        trend_counts = []
        for i in range(6, -1, -1):
            day = date.today() - timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            day_label = day.strftime('%a (%d %b)')
            count = Attendance.query.filter_by(date=day_str).count()
            trend_dates.append(day_label)
            trend_counts.append(count)

        return {
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'attendance_percentage': attendance_pct,
            'recent_attendance': recent_list,
            'chart_labels': trend_dates,
            'chart_data': trend_counts,
            'today_date': today_str
        }

    def get_student_attendance_summary(self, student_id: int):
        """Calculates detailed attendance breakdown for an individual student."""
        student = Student.query.get(student_id)
        if not student:
            return None

        # Total distinct dates with attendance recorded in the system
        total_system_days = db.session.query(db.func.count(db.func.distinct(Attendance.date))).scalar() or 0
        if total_system_days == 0:
            total_system_days = 1 if Attendance.query.filter_by(student_id=student_id).first() else 0

        # Present days for this student
        present_days = Attendance.query.filter_by(student_id=student_id).count()
        
        # Calculate absent days
        absent_days = max(0, total_system_days - present_days)
        
        # Attendance %
        attendance_pct = round((present_days / total_system_days * 100.0), 1) if total_system_days > 0 else 0.0

        # Full history
        history = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc(), Attendance.time.desc()).all()

        return {
            'student': student,
            'total_classes': total_system_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'attendance_percentage': attendance_pct,
            'history': history
        }

attendance_service = AttendanceService()
