# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('news/', views.news_api, name='news_api'),
    path('bookmarks/', views.get_bookmarks, name='get_bookmarks'),
    path('bookmarks/add/', views.bookmark_article, name='bookmark_article'),
    path('bookmarks/count/', views.get_bookmark_count, name='get_bookmark_count'),
    path('auth/status/', views.auth_status, name='auth_status'),
    path('csrf/', views.get_csrf_token, name='csrf'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/forgot-password/', views.forgot_password, name='forgot_password'),
    path('accounts/reset-password/', views.reset_password, name='reset_password'),
    path('accounts/change-password/', views.change_password, name='change_password'),
    path('accounts/delete/', views.delete_account, name='delete_account'),
]
