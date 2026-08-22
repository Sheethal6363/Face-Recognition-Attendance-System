from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database.models import Admin

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard.dashboard_view'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            session.clear()
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session.permanent = remember

            flash(f'Welcome back, {admin.username}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.dashboard_view'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
