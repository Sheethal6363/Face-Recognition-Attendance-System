import pytest
from app import create_app
from database.models import db, Student, Attendance
from services.attendance_service import attendance_service
from services.report_service import report_service

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_mark_attendance_and_duplicate_prevention(app):
    with app.app_context():
        student = Student(
            name='Sheethal',
            usn='4MH23CS139',
            department='Computer Science',
            semester=6,
            section='A'
        )
        db.session.add(student)
        db.session.commit()

        # Mark attendance first time
        res1 = attendance_service.mark_attendance(student.id, confidence=94.5)
        assert res1['success'] is True
        assert res1['already_marked'] is False
        assert res1['attendance']['name'] == 'Sheethal'
        assert res1['attendance']['usn'] == '4MH23CS139'

        # Reset in-memory cooldown to specifically test database duplicate protection
        attendance_service.last_marked_timestamps[student.id] = 0

        # Attempt marking attendance second time on same day
        res2 = attendance_service.mark_attendance(student.id, confidence=96.0)
        assert res2['success'] is False
        assert res2['already_marked'] is True
        assert 'already marked' in res2['message'].lower()

        # Ensure only 1 record exists in database
        count = Attendance.query.filter_by(student_id=student.id).count()
        assert count == 1

def test_attendance_percentage_calculation(app):
    with app.app_context():
        s1 = Student(name='Student 1', usn='USN101', department='CSE', semester=4, section='A')
        s2 = Student(name='Student 2', usn='USN102', department='CSE', semester=4, section='A')
        db.session.add_all([s1, s2])
        db.session.commit()

        # Simulate 2 classes on 2 different days
        # Day 1: s1 and s2 both present
        att1 = Attendance(student_id=s1.id, name=s1.name, usn=s1.usn, date='2026-08-18', time='09:00:00', status='Present', confidence=95.0)
        att2 = Attendance(student_id=s2.id, name=s2.name, usn=s2.usn, date='2026-08-18', time='09:02:00', status='Present', confidence=93.0)
        
        # Day 2: only s1 present
        att3 = Attendance(student_id=s1.id, name=s1.name, usn=s1.usn, date='2026-08-19', time='09:00:00', status='Present', confidence=96.0)
        
        db.session.add_all([att1, att2, att3])
        db.session.commit()

        # Summary for s1 (Present 2 out of 2 = 100%)
        sum1 = attendance_service.get_student_attendance_summary(s1.id)
        assert sum1['total_classes'] == 2
        assert sum1['present_days'] == 2
        assert sum1['absent_days'] == 0
        assert sum1['attendance_percentage'] == 100.0

        # Summary for s2 (Present 1 out of 2 = 50%)
        sum2 = attendance_service.get_student_attendance_summary(s2.id)
        assert sum2['total_classes'] == 2
        assert sum2['present_days'] == 1
        assert sum2['absent_days'] == 1
        assert sum2['attendance_percentage'] == 50.0

def test_report_service_csv_export(app):
    with app.app_context():
        s = Student(name='Test Student', usn='TESTUSN', department='ISE', semester=6, section='B')
        db.session.add(s)
        db.session.commit()

        att = Attendance(student_id=s.id, name=s.name, usn=s.usn, date='2026-08-20', time='10:15:30', status='Present', confidence=92.4)
        db.session.add(att)
        db.session.commit()

        records = report_service.get_filtered_records(student_id=s.id)
        assert len(records) == 1

        csv_text = report_service.export_csv_string(records)
        assert 'Name,USN,Date,Time,Status,Confidence (%)' in csv_text
        assert 'Test Student,TESTUSN,2026-08-20,10:15:30,Present,92.4' in csv_text
