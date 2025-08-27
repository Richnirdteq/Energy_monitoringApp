from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extension import db
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

DEFAULT_PROFILE_IMG = 'default.png'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    monthly_goal = db.Column(db.Float, nullable=True)
    profile_image = db.Column(db.String(120), nullable=True, default='default.png')

    # Token generation for password reset
    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.secret_key)
        return s.dumps(self.email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

    @staticmethod
    def verify_reset_token(token):
        s = URLSafeTimedSerializer(current_app.secret_key)
        try:
            email = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=1800)
        except:
            return
        return User.query.filter_by(email=email).first()

    # Relationships
    inputs = db.relationship('EnergyInput', backref='user', lazy=True)
    usages = db.relationship('ApplianceUsage', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)



    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class EnergyInput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    appliance = db.Column(db.String(100), nullable=False)
    watts = db.Column(db.Float, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    kwh = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ApplianceUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    appliance = db.Column(db.String(100), nullable=False)
    watts = db.Column(db.Float, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    kwh = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_kwh = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



