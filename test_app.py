#!/usr/bin/env python3
"""
Basic test script to validate the Energy Monitoring App
"""
import os
import sys
import tempfile
import unittest
from app import create_app, db
from app.models import User, EnergyInput

class EnergyAppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Set test environment variables
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['SECURITY_PASSWORD_SALT'] = 'test-salt'
        os.environ['DATABASE_URL'] = f'sqlite:///{self.db_path}'
        os.environ['FLASK_ENV'] = 'testing'
        
        self.app = create_app('production')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after tests"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_app_creation(self):
        """Test that the app can be created"""
        self.assertIsNotNone(self.app)

    def test_home_redirect(self):
        """Test that home page redirects to login"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_login_page_loads(self):
        """Test that login page loads"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_register_page_loads(self):
        """Test that register page loads"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'register', response.data.lower())

    def test_user_model(self):
        """Test user model creation"""
        with self.app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
            # Verify user was created
            found_user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(found_user)
            self.assertEqual(found_user.email, 'test@example.com')
            self.assertTrue(found_user.check_password('testpass'))

    def test_database_connection(self):
        """Test database connection"""
        with self.app.app_context():
            # Try to create tables
            db.create_all()
            
            # Verify tables exist by trying to query
            users = User.query.all()
            self.assertIsInstance(users, list)

def run_basic_health_check():
    """Run a basic health check without full test suite"""
    try:
        # Set minimal environment
        os.environ.setdefault('SECRET_KEY', 'test-key')
        os.environ.setdefault('SECURITY_PASSWORD_SALT', 'test-salt')
        os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')
        
        # Create app
        app = create_app('production')
        
        with app.app_context():
            # Try to create tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Test basic app functionality
            with app.test_client() as client:
                response = client.get('/')
                if response.status_code in [200, 302]:
                    print("✅ App responds to requests")
                else:
                    print(f"⚠️  App response code: {response.status_code}")
        
        print("✅ Basic health check passed!")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'health':
        # Run basic health check
        success = run_basic_health_check()
        sys.exit(0 if success else 1)
    else:
        # Run full test suite
        unittest.main()