import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from database.models import db, Student, Attendance
from utils.helpers import admin_required, decode_base64_image, save_face_image
from services.face_recognition_service import face_service
from services.attendance_service import attendance_service

student_bp = Blueprint('students', __name__)

@student_bp.route('/register-student', methods=['GET', 'POST'])
@admin_required
def register_student():
    if request.method == 'POST':
        # Accept either JSON (AJAX from webcam) or standard Form POST
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        name = data.get('name', '').strip()
        usn = data.get('usn', '').strip().upper()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        department = data.get('department', '').strip()
        semester = data.get('semester', '')
        section = data.get('section', '').strip().upper()
        image_b64 = data.get('image_data', '')

        # Basic Form Validations
        if not name or not usn or not department or not semester or not section:
            msg = 'Please fill in all required fields (Name, USN, Department, Semester, Section).'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('register_student.html')

        try:
            semester = int(semester)
        except ValueError:
            msg = 'Semester must be a valid number.'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('register_student.html')

        # Check duplicate USN
        existing = Student.query.filter_by(usn=usn).first()
        if existing:
            msg = f'A student with USN {usn} is already registered ({existing.name}).'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('register_student.html')

        # Process Face Image
        image_bgr = decode_base64_image(image_b64)
        if image_bgr is None:
            msg = 'No image captured. Please capture a live photo from your webcam.'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('register_student.html')

        # Run AI Face Detection and Encoding with strict single-face validation
        success, message, encoding, location = face_service.encode_face_from_image(image_bgr)
        if not success:
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'danger')
            return render_template('register_student.html')

        # Save face image to disk
        known_faces_dir = current_app.config['KNOWN_FACES_DIR']
        saved_filename = save_face_image(image_bgr, usn, known_faces_dir)

        # Save student to database
        try:
            student = Student(
                name=name,
                usn=usn,
                email=email if email else None,
                phone=phone if phone else None,
                department=department,
                semester=semester,
                section=section,
                face_image=saved_filename
            )
            student.set_encoding_list(encoding)
            
            db.session.add(student)
            db.session.commit()

            # Hot-reload in-memory face encodings for instant recognition
            face_service.reload_encodings()

            success_msg = f'Student {name} ({usn}) registered successfully!'
            if request.is_json:
                return jsonify({'success': True, 'message': success_msg, 'student_id': student.id}), 201
            
            flash(success_msg, 'success')
            return redirect(url_for('students.students_list'))

        except Exception as e:
            db.session.rollback()
            msg = f'Database error while saving student: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 500
            flash(msg, 'danger')
            return render_template('register_student.html')

    return render_template('register_student.html')


@student_bp.route('/students')
@admin_required
def students_list():
    search_query = request.args.get('q', '').strip()
    dept_filter = request.args.get('department', '').strip()
    sem_filter = request.args.get('semester', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Student.query

    if search_query:
        query = query.filter((Student.name.ilike(f'%{search_query}%')) | (Student.usn.ilike(f'%{search_query}%')))
    if dept_filter:
        query = query.filter(Student.department == dept_filter)
    if sem_filter:
        try:
            query = query.filter(Student.semester == int(sem_filter))
        except ValueError:
            pass
    if status_filter == 'active':
        query = query.filter(Student.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(Student.is_active == False)

    students = query.order_by(Student.created_at.desc()).all()

    # Calculate overall total attendance dates in system to determine percentage
    total_dates = db.session.query(db.func.count(db.func.distinct(Attendance.date))).scalar() or 0

    students_data = []
    for s in students:
        present_count = Attendance.query.filter_by(student_id=s.id).count()
        if total_dates > 0:
            att_pct = round((present_count / total_dates * 100.0), 1)
        else:
            att_pct = 100.0 if present_count > 0 else 0.0

        students_data.append({
            'student': s,
            'present_count': present_count,
            'attendance_percentage': att_pct
        })

    # Get distinct departments for filter dropdown
    departments = [d[0] for d in db.session.query(Student.department).distinct().all() if d[0]]

    return render_template('students.html', 
                           students_data=students_data, 
                           departments=departments,
                           search_query=search_query,
                           dept_filter=dept_filter,
                           sem_filter=sem_filter,
                           status_filter=status_filter)


@student_bp.route('/students/<int:student_id>')
@admin_required
def student_details(student_id):
    summary = attendance_service.get_student_attendance_summary(student_id)
    if not summary:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.students_list'))
    
    return render_template('student_details.html', **summary)


@student_bp.route('/students/<int:student_id>/edit', methods=['POST'])
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    student.name = request.form.get('name', student.name).strip()
    student.email = request.form.get('email', '').strip() or None
    student.phone = request.form.get('phone', '').strip() or None
    student.department = request.form.get('department', student.department).strip()
    
    sem = request.form.get('semester')
    if sem:
        try:
            student.semester = int(sem)
        except ValueError:
            pass
            
    student.section = request.form.get('section', student.section).strip().upper()

    try:
        db.session.commit()
        face_service.reload_encodings()
        flash(f'Student {student.name} profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating student: {str(e)}', 'danger')

    return redirect(url_for('students.student_details', student_id=student.id))


@student_bp.route('/students/<int:student_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_status(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_active = not student.is_active
    db.session.commit()
    
    face_service.reload_encodings()
    status_label = 'activated' if student.is_active else 'deactivated'
    flash(f'Student {student.name} has been {status_label}.', 'info')
    return redirect(request.referrer or url_for('students.students_list'))


@student_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    name = student.name
    
    # Remove photo if exists
    if student.face_image:
        photo_path = os.path.join(current_app.config['KNOWN_FACES_DIR'], student.face_image)
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception:
                pass

    db.session.delete(student)
    db.session.commit()
    face_service.reload_encodings()

    flash(f'Student {name} was permanently removed.', 'warning')
    return redirect(url_for('students.students_list'))


@student_bp.route('/students/face-image/<filename>')
@admin_required
def get_face_image(filename):
    """Protected endpoint to serve registered face images."""
    known_faces_dir = current_app.config['KNOWN_FACES_DIR']
    return send_from_directory(known_faces_dir, filename)
