import pytest
from app import create_app
from database.models import db, Admin, Student, Attendance
from sqlalchemy.exc import IntegrityError

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_admin_model(app):
    with app.app_context():
        admin = Admin(username='testadmin')
        admin.set_password('securepass123')
        db.session.add(admin)
        db.session.commit()

        retrieved = Admin.query.filter_by(username='testadmin').first()
        assert retrieved is not None
        assert retrieved.check_password('securepass123') is True
        assert retrieved.check_password('wrongpass') is False

def test_student_model_and_encoding(app):
    with app.app_context():
        student = Student(
            name='Sheethal',
            usn='4MH23CS139',
            department='Computer Science',
            semester=6,
            section='B',
            email='sheethal@example.com'
        )
        sample_encoding = [0.12, -0.45, 0.88, 0.0]
        student.set_encoding_list(sample_encoding)

        db.session.add(student)
        db.session.commit()

        retrieved = Student.query.filter_by(usn='4MH23CS139').first()
        assert retrieved is not None
        assert retrieved.name == 'Sheethal'
        assert retrieved.get_encoding_list() == sample_encoding
        assert retrieved.is_active is True

def test_unique_usn_constraint(app):
    with app.app_context():
        s1 = Student(name='Student 1', usn='USN001', department='CSE', semester=4, section='A')
        s2 = Student(name='Student 2', usn='USN001', department='ISE', semester=4, section='B')
        db.session.add(s1)
        db.session.commit()

        db.session.add(s2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_attendance_unique_per_day_constraint(app):
    with app.app_context():
        s = Student(name='John Doe', usn='USN002', department='CSE', semester=4, section='A')
        db.session.add(s)
        db.session.commit()

        att1 = Attendance(student_id=s.id, name=s.name, usn=s.usn, date='2026-08-20', time='09:00:00', status='Present', confidence=95.0)
        db.session.add(att1)
        db.session.commit()

        # Duplicate on same date should raise IntegrityError
        att2 = Attendance(student_id=s.id, name=s.name, usn=s.usn, date='2026-08-20', time='10:30:00', status='Present', confidence=94.0)
        db.session.add(att2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
