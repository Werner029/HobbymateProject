from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include('api.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
]

if settings.DEBUG:
    import debug_toolbar  # pragma: no cover

    urlpatterns = [  # pragma: no cover
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns  # pragma: no cover
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )  # pragma: no cover
    urlpatterns += [
        path(
            'swagger/',
            SpectacularSwaggerView.as_view(url_name='schema'),
            name='swagger-ui',
        ),
        path(
            'redoc/',
            SpectacularRedocView.as_view(url_name='schema'),
            name='redoc',
        ),
    ]
