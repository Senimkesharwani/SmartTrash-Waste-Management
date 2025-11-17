"""
WSGI config for waste_project.

It exposes the WSGI callable as a module-level variable named `application`.
This file is used to serve your Django app using WSGI servers (like Gunicorn, uWSGI, etc.).
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the default settings module for the Django application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'waste_project.settings')

# Create the WSGI application instance
application = get_wsgi_application()
