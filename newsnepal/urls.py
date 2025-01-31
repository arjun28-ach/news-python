from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from news import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('news.urls')),  # All API endpoints under /api/
    path('', TemplateView.as_view(template_name='index.html')),  # Serve React app
    path('api/csrf/', views.get_csrf_token, name='csrf'),
    path('api/accounts/signup/', views.signup, name='signup'),
    path('api/accounts/login/', views.login_view, name='login'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
