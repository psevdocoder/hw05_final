from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about/', include('about.urls')),
    path('', include('posts.urls', namespace='posts')),
]

handler404 = 'core.views.page_not_found'

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
