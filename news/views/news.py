from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from ..scraper import fetch_and_summarize_news, maybe_clear_cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from ..models import UserBookmark
from django.views.decorators.csrf import ensure_csrf_cookie
import logging
import json

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def home(request):
    return render(request, 'index.html')

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
        data = json.loads(request.body)
        UserBookmark.objects.create(
            user=request.user,
            article_url=data['article_url'],
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

@login_required
def get_bookmark_count(request):
    count = UserBookmark.objects.filter(user=request.user).count()
    return JsonResponse({'count': count})

@login_required
@require_POST
def remove_bookmark(request):
    try:
        data = json.loads(request.body)
        article_url = data.get('article_url')
        
        # Delete the bookmark
        bookmark = UserBookmark.objects.filter(
            user=request.user,
            article_url=article_url
        ).first()
        
        if bookmark:
            bookmark.delete()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Bookmark not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400) 