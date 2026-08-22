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
