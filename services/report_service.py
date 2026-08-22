import os
import io
import csv
from datetime import datetime, date
from database.models import db, Student, Attendance

class ReportService:
    def get_filtered_records(self, start_date=None, end_date=None, student_id=None, department=None, status=None):
        """
        Queries attendance with optional filters.
        Returns list of Attendance objects.
        """
        query = Attendance.query.join(Student, Attendance.student_id == Student.id)

        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        if student_id:
            query = query.filter(Attendance.student_id == student_id)
        if department:
            query = query.filter(Student.department == department)
        if status:
            query = query.filter(Attendance.status == status)

        return query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()

    def generate_report_summary(self, records):
        """Calculates report summary statistics."""
        total_present = len(records)
        total_students = Student.query.filter_by(is_active=True).count()
        
        # Unique students present in this report slice
        present_student_ids = len(set(r.student_id for r in records))
        total_absent = max(0, total_students - present_student_ids)
        
        avg_pct = round((present_student_ids / total_students * 100.0), 1) if total_students > 0 else 0.0

        return {
            'total_records': total_present,
            'total_students': total_students,
            'unique_present_students': present_student_ids,
            'total_absent': total_absent,
            'attendance_percentage': avg_pct
        }

    def export_csv_string(self, records):
        """
        Generates CSV format content as a string.
        Format: Name,USN,Date,Time,Status,Confidence
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Name', 'USN', 'Date', 'Time', 'Status', 'Confidence (%)'])
        
        # Write data rows
        for r in records:
            writer.writerow([
                r.name,
                r.usn,
                r.date,
                r.time,
                r.status,
                f"{r.confidence:.1f}"
            ])
            
        return output.getvalue()

    def save_csv_export(self, records, exports_dir):
        """Saves CSV file to exports directory and returns filepath."""
        os.makedirs(exports_dir, exist_ok=True)
        today_str = date.today().strftime('%Y-%m-%d')
        filename = f"attendance_report_{today_str}_{int(datetime.now().timestamp())}.csv"
        filepath = os.path.join(exports_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            f.write(self.export_csv_string(records))

        return filename, filepath

report_service = ReportService()
