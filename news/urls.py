# urls.py

from django.urls import path
from . import views

urlpatterns = [
    # News endpoints
    path('news/', views.news_api, name='news_api'),
    path('news/bookmarks/', views.get_bookmarks, name='get_bookmarks'),
    path('news/bookmark/', views.bookmark_article, name='bookmark_article'),
    path('news/bookmark-count/', views.get_bookmark_count, name='get_bookmark_count'),
    
    # Auth endpoints
    path('csrf/', views.get_csrf_token, name='csrf'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/status/', views.auth_status, name='auth_status'),
]
