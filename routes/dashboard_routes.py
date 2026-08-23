from flask import Blueprint, render_template, jsonify
from utils.helpers import admin_required
from services.attendance_service import attendance_service

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@admin_required
def dashboard_view():
    stats = attendance_service.get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)


@dashboard_bp.route('/api/dashboard-stats')
@admin_required
def api_dashboard_stats():
    stats = attendance_service.get_dashboard_stats()
    return jsonify({
        'success': True,
        'data': stats
    })


@dashboard_bp.route('/api/attendance-chart')
@admin_required
def api_attendance_chart():
    stats = attendance_service.get_dashboard_stats()
    return jsonify({
        'success': True,
        'labels': stats['chart_labels'],
        'data': stats['chart_data']
    })


@dashboard_bp.route('/api/system-network')
@admin_required
def api_system_network():
    import socket
    import os
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Attempt connecting to public DNS to detect primary outbound interface IP
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "127.0.0.1"

    port = int(os.environ.get('PORT', 5000))
    return jsonify({
        'success': True,
        'local_ip': local_ip,
        'port': port,
        'attendance_url': f"http://{local_ip}:{port}/live-attendance",
        'dashboard_url': f"http://{local_ip}:{port}/dashboard"
    })

