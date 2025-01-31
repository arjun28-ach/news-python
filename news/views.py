# views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from .scraper import fetch_and_summarize_news, maybe_clear_cache
import logging
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import UserBookmark
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.template.loader import render_to_string
from django.conf import settings
import json
import concurrent.futures
from django.middleware.csrf import get_token

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def home(request):
    manifest_path = settings.BASE_DIR / 'frontend' / 'dist' / 'manifest.json'
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except:
        manifest = {}
        
    return render(request, 'index.html', {
        'manifest': manifest
    })

@ensure_csrf_cookie
def news_api(request):
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        language = request.GET.get('language', 'en')
        
        maybe_clear_cache()
        news_data = fetch_and_summarize_news(page=page, per_page=per_page)
        
        return JsonResponse(news_data)
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return JsonResponse({
            'error': 'Invalid parameters provided'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in news_api: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
@require_POST
def bookmark_article(request):
    try:
        data = request.POST
        UserBookmark.objects.create(
            user=request.user,
            article_url=data['url'],
            title=data['title'],
            summary=data['summary'],
            image_url=data['image_url'],
            published_at=data['published_at'],
            category=data['category'],
            source=data['source'],
            language=data['language']
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def get_bookmarks(request):
    bookmarks = UserBookmark.objects.filter(user=request.user).order_by('-created_at')
    return JsonResponse({
        'bookmarks': list(bookmarks.values())
    })

@ensure_csrf_cookie
def get_csrf_token(request):
    """Get CSRF token for frontend"""
    return JsonResponse({'csrfToken': get_token(request)})

@csrf_exempt  # Temporarily exempt signup from CSRF
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            form = UserCreationForm({
                'username': data.get('username'),
                'password1': data.get('password'),
                'password2': data.get('password')
            })
            if form.is_valid():
                user = form.save()
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'user': {
                        'username': user.username,
                        'email': user.email
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt  # Temporarily exempt login from CSRF
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'user': {
                        'username': user.username,
                        'email': user.email
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def get_bookmark_count(request):
    count = UserBookmark.objects.filter(user=request.user).count()
    return JsonResponse({'count': count})

@ensure_csrf_cookie
def auth_status(request):
    return JsonResponse({
        'isAuthenticated': request.user.is_authenticated,
        'user': {
            'username': request.user.username,
            'email': request.user.email
        } if request.user.is_authenticated else None
    })
