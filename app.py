import os
from flask import Flask, render_template
from config import config_by_name
from database import db, init_db
from routes import auth_bp, dashboard_bp, student_bp, attendance_bp
from services import face_service

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    config_class = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_class)

    # Initialize Database & seed default admin
    init_db(app)

    # Preload student face encodings into memory if not testing
    if not app.config.get('TESTING'):
        with app.app_context():
            try:
                face_service.match_threshold = app.config.get('FACE_MATCH_THRESHOLD', 0.50)
                loaded_count = face_service.load_known_faces()
                print(f"[*] Preloaded {loaded_count} student face encodings into AI cache.")
            except Exception as e:
                print(f"[!] Warning: Could not preload face encodings at startup: {e}")

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(attendance_bp)

    # Custom 404 & 500 Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('404.html', error_title="500 - Server Error", error_msg="An internal server error occurred. Please try again."), 500

    return app

# Only instantiate default instance if not run within pytest
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"[*] Starting VYRON — AI Biometric Attendance System on http://127.0.0.1:{port}")
    print(f"[*] Default Admin -> Username: admin | Password: admin123")
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    # WSGI application object
    app = create_app()
