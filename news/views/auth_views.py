from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.middleware.csrf import get_token
import json
import logging

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def get_csrf_token(request):
    """Get CSRF token for frontend"""
    return JsonResponse({'csrfToken': get_token(request)})

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            # Validate input
            if not username or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username and password are required'
                }, status=400)
            
            # Check if username exists
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username already exists'
                }, status=400)
            
            # Create user with proper password confirmation
            form = UserCreationForm({
                'username': username,
                'password1': password,
                'password2': password  # Password confirmation
            })
            
            if form.is_valid():
                try:
                    user = form.save()
                    login(request, user)
                    return JsonResponse({
                        'status': 'success',
                        'user': {
                            'username': user.username
                        }
                    })
                except Exception as e:
                    logger.error(f"Error saving user: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Error creating user account'
                    }, status=500)
            else:
                # Return specific form errors
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'status': 'error',
                    'errors': errors
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in signup: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            # Validate input
            if not username or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username and password are required'
                }, status=400)
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'user': {
                        'username': user.username
                    }
                })
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in login: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

def logout_view(request):
    logout(request)
    return JsonResponse({'status': 'success'})

@ensure_csrf_cookie
def auth_status(request):
    return JsonResponse({
        'isAuthenticated': request.user.is_authenticated,
        'user': {
            'username': request.user.username
        } if request.user.is_authenticated else None
    }) 