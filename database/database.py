import os
from .models import db, Admin

def init_db(app):
    """Initialize database tables and create directories if needed."""
    db.init_app(app)
    
    with app.app_context():
        # Ensure directories exist
        instance_dir = app.config.get('INSTANCE_DIR', os.path.join(os.path.dirname(__file__), '..', 'instance'))
        known_faces_dir = app.config.get('KNOWN_FACES_DIR', os.path.join(os.path.dirname(__file__), '..', 'known_faces'))
        exports_dir = app.config.get('EXPORTS_DIR', os.path.join(os.path.dirname(__file__), '..', 'exports'))
        
        os.makedirs(instance_dir, exist_ok=True)
        os.makedirs(known_faces_dir, exist_ok=True)
        os.makedirs(exports_dir, exist_ok=True)
        
        # Create tables
        db.create_all()
        
        # Seed default admin if no admin exists
        default_admin = Admin.query.filter_by(username='admin').first()
        if not default_admin:
            admin = Admin(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: username='admin', password='admin123'")
