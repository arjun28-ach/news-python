from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.conf import settings
from ..models import User, UserProfile
import jwt
from datetime import datetime, timedelta
import json

@require_http_methods(["POST"])
@ensure_csrf_cookie
def signup(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Email already registered'
            }, status=400)

        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            is_active=True,
            email_verified=True
        )

        # Create user profile
        UserProfile.objects.create(user=user)

        # Authenticate and login the user
        authenticated_user = authenticate(request, username=email, password=password)
        if authenticated_user is not None:
            login(request, authenticated_user)
            return JsonResponse({
                'status': 'success',
                'user': {
                    'name': user.name,
                    'email': user.email
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to authenticate user'
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_http_methods(["POST"])
@ensure_csrf_cookie
def login_view(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            user.last_login_at = datetime.now()
            user.save()
            return JsonResponse({
                'status': 'success',
                'user': {
                    'name': user.name,
                    'email': user.email
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_http_methods(["POST"])
def google_auth(request):
    try:
        token = request.POST.get('token')
        # Verify Google token and get user info
        user_info = verify_google_token(token)
        
        user, created = User.objects.get_or_create(
            email=user_info['email'],
            defaults={
                'name': user_info['name'],
                'google_id': user_info['sub'],
                'profile_picture': user_info.get('picture'),
                'email_verified': True
            }
        )

        if created:
            UserProfile.objects.create(user=user)

        login(request, user)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_http_methods(["POST"])
def forgot_password(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'No account found with this email'
            }, status=404)

        # Generate reset token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'type': 'password_reset'
        }, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        # Create reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        # Send email
        html_message = render_to_string('emails/reset_password.html', {
            'user': user,
            'reset_url': reset_url
        })

        send_mail(
            subject='Reset Your Password - NewsNepal',
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Password reset instructions sent to your email'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_http_methods(["POST"])
def reset_password(request):
    try:
        data = json.loads(request.body)
        token = data.get('token')
        new_password = data.get('password')

        try:
            # Verify token
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            if payload.get('type') != 'password_reset':
                raise ValueError('Invalid token type')

            user = User.objects.get(id=payload['user_id'])
            user.set_password(new_password)
            user.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Password reset successful'
            })

        except jwt.ExpiredSignatureError:
            return JsonResponse({
                'status': 'error',
                'message': 'Reset link has expired'
            }, status=400)
        except (jwt.InvalidTokenError, User.DoesNotExist, ValueError) as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid reset link'
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

def verify_email(request, token):
    try:
        user = verify_verification_token(token)
        user.email_verified = True
        user.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return JsonResponse({'status': 'success'})

@require_http_methods(["GET"])
def check_auth(request):
    if request.user.is_authenticated:
        return JsonResponse({
            'isAuthenticated': True,
            'user': {
                'name': request.user.name,
                'email': request.user.email,
                'profile_picture': request.user.profile_picture
            }
        })
    return JsonResponse({
        'isAuthenticated': False,
        'user': None
    })

@require_http_methods(["POST"])
@login_required
def change_password(request):
    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        # Verify current password
        if not request.user.check_password(current_password):
            return JsonResponse({
                'status': 'error',
                'message': 'Current password is incorrect'
            }, status=400)

        # Set new password
        request.user.set_password(new_password)
        request.user.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Password changed successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_http_methods(["POST"])
@login_required
def delete_account(request):
    try:
        user = request.user
        logout(request)
        user.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Account deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400) 