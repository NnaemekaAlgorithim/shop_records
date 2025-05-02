"""
WSGI config for owneet_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from user_management.apps.base.config import DEBUG

from django.core.wsgi import get_wsgi_application

if DEBUG:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_management.user_management.settings.dev_settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_management.user_management.settings.prod_settings")

application = get_wsgi_application()
