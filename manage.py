#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from user_management.apps.base.config import DEBUG


def main():
    """Run administrative tasks."""

    if DEBUG:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_management.user_management.settings.dev_settings")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_management.user_management.settings.prod_settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
