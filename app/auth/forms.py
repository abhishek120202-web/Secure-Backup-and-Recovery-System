"""
WTForms for authentication.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    """Form for user login."""
    
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=64)],
        render_kw={"placeholder": "Enter your username"}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter your password"}
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """Form for user registration."""
    
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=64)],
        render_kw={"placeholder": "Choose a username"}
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your email"}
    )
    full_name = StringField(
        'Full Name',
        validators=[Length(min=0, max=120)],
        render_kw={"placeholder": "Enter your full name"}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=8)],
        render_kw={"placeholder": "Password (minimum 8 characters)"}
    )
    password_confirm = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
        render_kw={"placeholder": "Confirm your password"}
    )
    submit = SubmitField('Register')
    
    def validate_username(self, field):
        """Validate that username is unique."""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')
    
    def validate_email(self, field):
        """Validate that email is unique."""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangePasswordForm(FlaskForm):
    """Form for changing user password."""
    
    current_password = PasswordField(
        'Current Password',
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter your current password"}
    )
    new_password = PasswordField(
        'New Password',
        validators=[DataRequired(), Length(min=8)],
        render_kw={"placeholder": "Enter new password (minimum 8 characters)"}
    )
    new_password_confirm = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')],
        render_kw={"placeholder": "Confirm new password"}
    )
    submit = SubmitField('Change Password')
