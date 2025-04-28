"""
ASGI config for owneet_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from user_management.apps.base.config import DEBUG

from django.core.asgi import get_asgi_application

if DEBUG:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_management.user_management.settings.dev_settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_management.user_management.settings.prod_settings")

application = get_asgi_application()
