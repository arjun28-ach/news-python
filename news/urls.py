# urls.py

from django.urls import path
from .views import auth_views, news_views

urlpatterns = [
    # News endpoints
    path('news/', news_views.news_api, name='news_api'),
    path('news/bookmarks/', news_views.get_bookmarks, name='get_bookmarks'),
    path('news/bookmark/', news_views.bookmark_article, name='bookmark_article'),
    path('news/bookmark-count/', news_views.get_bookmark_count, name='get_bookmark_count'),
    
    # Auth endpoints
    path('csrf/', auth_views.get_csrf_token, name='csrf'),
    path('accounts/signup/', auth_views.signup, name='signup'),
    path('accounts/login/', auth_views.login_view, name='login'),
    path('accounts/logout/', auth_views.logout_view, name='logout'),
    path('accounts/status/', auth_views.auth_status, name='auth_status'),
]
