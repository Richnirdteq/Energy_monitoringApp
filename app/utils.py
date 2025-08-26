import os
import secrets
from PIL import Image
from flask import current_app
from flask_mail import Message
from flask import url_for, current_app
from .extension import mail  # assuming you initialized Flask-Mail in extension.py

def save_profile_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    # Resize image
    output_size = (300, 300)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn

def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('main.reset_password', token=token, _external=True)

    msg = Message("Password Reset Request",
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f"""Hello {user.username},

To reset your password, click the link below:

{reset_url}

If you did not make this request, simply ignore this email.
"""
    mail.send(msg)
