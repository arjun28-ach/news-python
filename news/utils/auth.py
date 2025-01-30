import jwt
from django.conf import settings
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string

def generate_verification_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=1),
        'type': 'email_verification'
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def generate_reset_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'type': 'password_reset'
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_google_token(token):
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        return idinfo
    except ValueError:
        raise Exception('Invalid token')

def send_verification_email(user, token):
    subject = 'Verify your email - NewsNepal'
    html_message = render_to_string('emails/verify_email.html', {
        'user': user,
        'token': token
    })
    send_mail(
        subject,
        '',
        settings.EMAIL_HOST_USER,
        [user.email],
        html_message=html_message
    ) 