"""
ASGI config for chess_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chess_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_project.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chess_app.routing.websocket_urlpatterns
        )
    ),
})
