"""
URL configuration for gas_management_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    path('api/v1/gas-service/', include('gas_management_service.apps.gas_sales_and_stock.urls')),
    re_path(r'^$', RedirectView.as_view(url='api/schema/redoc/', permanent=False), name='redoc-root'),
]


# Add a prefix for deployment (e.g., 'dev' or 'prod')
from django.conf import settings

base_prefix = settings.BASE_PREFIX if hasattr(settings, 'BASE_PREFIX') else ''
if base_prefix:
    urlpatterns = [path(f'{base_prefix}/', include(urlpatterns))]