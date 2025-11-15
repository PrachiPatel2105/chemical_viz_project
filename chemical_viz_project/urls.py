"""
URL configuration for chemical_viz_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # DRF Login/Logout Authentication Endpoints (for Basic/Session Auth)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Data API Endpoints (This is the crucial line for /api/)
    path('api/', include('data_api.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)