from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
import debug_toolbar

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about/', include('about.urls')),
    path('', include('posts.urls', namespace='posts')),
]

handler404 = 'core.views.page_not_found'
handler403 = 'core.views.csrf_failure'
handler500 = 'core.views.internal_error'

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
