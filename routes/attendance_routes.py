import time
import io
import cv2
from flask import Blueprint, render_template, request, Response, jsonify, current_app, send_file
from database.models import db, Student, Attendance
from utils.helpers import admin_required, decode_base64_image
from services.face_recognition_service import face_service
from services.attendance_service import attendance_service
from services.report_service import report_service

attendance_bp = Blueprint('attendance', __name__)

# Video Stream Generator
def generate_mjpeg_stream():
    """Generates OpenCV MJPEG video stream with live face recognition overlays."""
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        # Fallback placeholder image frame if camera cannot be opened
        placeholder = cv2.imread(None)
        return

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            # Recognize faces in current frame
            recognition_results = face_service.recognize_faces_in_frame(frame)

            # Mark attendance for any recognized student
            for res in recognition_results:
                if res['recognized'] and res.get('student_id'):
                    attendance_service.mark_attendance(
                        student_id=res['student_id'],
                        confidence=res.get('confidence', 0.0)
                    )

            # Draw aesthetic overlays
            annotated_frame = face_service.draw_recognition_overlays(frame, recognition_results)

            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04) # ~25 FPS
    finally:
        cap.release()


@attendance_bp.route('/live-attendance')
@admin_required
def live_attendance():
    """Renders the interactive real-time attendance recognition console."""
    stats = attendance_service.get_dashboard_stats()
    return render_template('live_attendance.html', stats=stats)


@attendance_bp.route('/video-feed')
@admin_required
def video_feed():
    """Returns multipart MJPEG webcam video stream."""
    return Response(
        generate_mjpeg_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@attendance_bp.route('/api/recognize-frame', methods=['POST'])
@admin_required
def api_recognize_frame():
    """
    Processes a frame captured by the client's webcam in real-time.
    Detects/recognizes faces, draws overlays, and marks attendance.
    """
    data = request.get_json() or {}
    image_b64 = data.get('image', '')

    if not image_b64:
        return jsonify({'success': False, 'message': 'No frame image provided.'}), 400

    frame_bgr = decode_base64_image(image_b64)
    if frame_bgr is None:
        return jsonify({'success': False, 'message': 'Failed to decode image frame.'}), 400

    # Recognize faces in the frame
    results = face_service.recognize_faces_in_frame(frame_bgr)
    
    marked_students = []
    for res in results:
        if res['recognized'] and res.get('student_id'):
            mark_res = attendance_service.mark_attendance(
                student_id=res['student_id'],
                confidence=res['confidence']
            )
            res['attendance_status'] = mark_res['message']
            res['is_new_mark'] = mark_res['success']
            if mark_res['success']:
                marked_students.append({
                    'name': res['name'],
                    'usn': res['usn'],
                    'confidence': res['confidence'],
                    'time': mark_res['attendance']['time'] if mark_res.get('attendance') else ''
                })
        else:
            res['attendance_status'] = 'Unknown Face - Not Marked'
            res['is_new_mark'] = False

    return jsonify({
        'success': True,
        'faces': results,
        'marked_students': marked_students
    })


@attendance_bp.route('/attendance')
@admin_required
def attendance_list():
    date_filter = request.args.get('date', '').strip()
    search_query = request.args.get('q', '').strip()
    dept_filter = request.args.get('department', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Attendance.query.join(Student, Attendance.student_id == Student.id)

    if date_filter:
        query = query.filter(Attendance.date == date_filter)
    if search_query:
        query = query.filter(
            (Attendance.name.ilike(f'%{search_query}%')) | 
            (Attendance.usn.ilike(f'%{search_query}%'))
        )
    if dept_filter:
        query = query.filter(Student.department == dept_filter)
    if status_filter:
        query = query.filter(Attendance.status == status_filter)

    records = query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()
    departments = [d[0] for d in db.session.query(Student.department).distinct().all() if d[0]]

    return render_template('attendance.html',
                           records=records,
                           departments=departments,
                           date_filter=date_filter,
                           search_query=search_query,
                           dept_filter=dept_filter,
                           status_filter=status_filter)


@attendance_bp.route('/reports')
@admin_required
def reports_view():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    dept_filter = request.args.get('department', '').strip()
    student_usn = request.args.get('usn', '').strip()

    student_id = None
    if student_usn:
        st = Student.query.filter_by(usn=student_usn.upper()).first()
        if st:
            student_id = st.id

    records = report_service.get_filtered_records(
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
        student_id=student_id,
        department=dept_filter if dept_filter else None
    )

    summary = report_service.generate_report_summary(records)
    departments = [d[0] for d in db.session.query(Student.department).distinct().all() if d[0]]

    return render_template('reports.html',
                           records=records,
                           summary=summary,
                           departments=departments,
                           start_date=start_date,
                           end_date=end_date,
                           dept_filter=dept_filter,
                           student_usn=student_usn)


@attendance_bp.route('/reports/export')
@admin_required
def export_attendance_csv():
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    dept_filter = request.args.get('department', '').strip()
    student_usn = request.args.get('usn', '').strip()

    student_id = None
    if student_usn:
        st = Student.query.filter_by(usn=student_usn.upper()).first()
        if st:
            student_id = st.id

    records = report_service.get_filtered_records(
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
        student_id=student_id,
        department=dept_filter if dept_filter else None
    )

    csv_data = report_service.export_csv_string(records)
    
    filename = f"attendance_report_{start_date or 'all'}_to_{end_date or 'current'}.csv"
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
