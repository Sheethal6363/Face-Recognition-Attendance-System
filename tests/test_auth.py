import pytest
from app import create_app
from database.models import db, Admin

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Ensure test admin exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_page_renders(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'VYRON' in response.data
    assert b'Admin Identifier' in response.data

def test_admin_login_success(client):
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back, admin!' in response.data
    assert b'Command Center' in response.data

def test_admin_login_invalid_password(client):
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

def test_protected_routes_redirect_unauthenticated(client):
    protected_endpoints = ['/dashboard', '/students', '/attendance', '/reports', '/live-attendance']
    for ep in protected_endpoints:
        response = client.get(ep, follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

def test_logout(client):
    # Login first
    client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out successfully.' in response.data
    
    # Try accessing dashboard again
    res = client.get('/dashboard', follow_redirects=False)
    assert res.status_code == 302
