"""
WSGI config for chess_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_project.settings')

application = get_wsgi_application()

# Development server configuration
if os.environ.get('DJANGO_DEVELOPMENT') == 'True':
    from django.core.management.commands.runserver import Command
    Command.default_port = '8000'
    Command.default_addr = '127.0.0.1'
    Command.use_reloader = True
