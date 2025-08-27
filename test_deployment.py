#!/usr/bin/env python3
"""
Test deployment script for Energy Monitoring App
"""
import os
import sys
import requests
from app import create_app, db

def test_database_connection():
    """Test database connection with production settings"""
    try:
        # Set environment variables
        os.environ['SECRET_KEY'] = 'your-very-secret-key'
        os.environ['SECURITY_PASSWORD_SALT'] = 'your-password-salt'
        os.environ['DATABASE_URL'] = 'postgresql://energy_monitoringapp_user:M67oorepelCNtil2oJJOpMmAkd8A9itE@dpg-d2ms252dbo4c73f67nug-a.oregon-postgres.render.com/energy_monitoringapp'
        os.environ['FLASK_ENV'] = 'production'
        
        app = create_app('production')
        
        with app.app_context():
            # Test database connection
            db.create_all()
            print("✅ Database connection successful")
            print("✅ Tables created/verified")
            
            # Test basic query
            from app.models import User
            users = User.query.all()
            print(f"✅ Database query successful - {len(users)} users found")
            
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def test_app_creation():
    """Test app creation and basic functionality"""
    try:
        app = create_app('production')
        
        with app.test_client() as client:
            # Test home redirect
            response = client.get('/')
            if response.status_code == 302:
                print("✅ Home page redirects correctly")
            
            # Test login page
            response = client.get('/login')
            if response.status_code == 200:
                print("✅ Login page loads successfully")
            
            # Test register page
            response = client.get('/register')
            if response.status_code == 200:
                print("✅ Register page loads successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ App test failed: {str(e)}")
        return False

if __name__ == '__main__':
    print("🧪 Testing Energy Monitoring App Deployment...")
    print("=" * 50)
    
    db_success = test_database_connection()
    app_success = test_app_creation()
    
    if db_success and app_success:
        print("\n🎉 All tests passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check configuration.")
        sys.exit(1)