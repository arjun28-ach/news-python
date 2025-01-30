# urls.py

from django.urls import path
from .views import auth, news

urlpatterns = [
    path('news/', news.news_api, name='news_api'),
    path('accounts/signup/', auth.signup, name='signup'),
    path('accounts/login/', auth.login_view, name='login'),
    path('accounts/logout/', auth.logout_view, name='logout'),
    path('bookmarks/', news.get_bookmarks, name='get_bookmarks'),
    path('bookmarks/add/', news.bookmark_article, name='bookmark_article'),
    path('bookmarks/remove/', news.remove_bookmark, name='remove_bookmark'),
    path('bookmarks/count/', news.get_bookmark_count, name='bookmark_count'),
    path('accounts/status/', auth.check_auth, name='check_auth'),
    path('accounts/forgot-password/', auth.forgot_password, name='forgot_password'),
    path('accounts/reset-password/', auth.reset_password, name='reset_password'),
    path('accounts/change-password/', auth.change_password, name='change_password'),
    path('accounts/delete/', auth.delete_account, name='delete_account'),
]
