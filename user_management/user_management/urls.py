from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('social/', include('social_django.urls', namespace='social')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/users/', include('user_management.apps.users.urls')),
    path('api/v1/gas/', include('user_management.apps.gas_sales_and_stock.urls')),
    re_path(r'^$', RedirectView.as_view(url='api/schema/redoc/', permanent=False), name='redoc-root'),
]


# Add a prefix for deployment (e.g., 'dev' or 'prod')
from django.conf import settings

base_prefix = settings.BASE_PREFIX if hasattr(settings, 'BASE_PREFIX') else ''
if base_prefix:
    urlpatterns = [path(f'{base_prefix}/', include(urlpatterns))]
