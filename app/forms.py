# app/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, SubmitField, DateField, 
    SelectField, IntegerField, PasswordField
)
from wtforms.validators import DataRequired, NumberRange, InputRequired, Email, EqualTo
from flask_wtf.file import FileAllowed, FileField
from wtforms.validators import Length
from flask_login import current_user

class ApplianceInputForm(FlaskForm):
    appliance = SelectField('Appliance', choices=[
        ('Household:Fan', 'Fan (Household)'),
        ('Household:Fridge', 'Fridge (Household)'),
        ('Household:TV', 'TV (Household)'),
        ('Business:Printer', 'Printer (Business)'),
        ('Business:AC', 'AC (Business)'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    other_appliance = StringField('Other Appliance')
    watts = IntegerField('Watts', validators=[DataRequired()])
    hours = FloatField('Hours', validators=[DataRequired()])
    submit = SubmitField('Add Usage')

class ApplianceUsageForm(FlaskForm):
    appliance = SelectField('Appliance', choices=[
        ('Household:Fan', 'Fan (Household)'),
        ('Household:Fridge', 'Fridge (Household)'),
        ('Household:TV', 'TV (Household)'),
        ('Business:Printer', 'Printer (Business)'),
        ('Business:AC', 'AC (Business)'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    other_appliance = StringField('Other Appliance')
    watts = FloatField('Watts', validators=[DataRequired()])
    hours = FloatField('Hours', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Add Usage')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')

class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Set New Password")



class ProfileUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update')

class GoalForm(FlaskForm):
    target_kwh = FloatField('Monthly Goal (kWh)', validators=[DataRequired()])
    submit = SubmitField('Save Goal')


