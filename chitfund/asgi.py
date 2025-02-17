"""
ASGI config for chitfund project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chitfund.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": AuthMiddlewareStack(
        URLRouter([
            re_path(r"", django_asgi_app),
        ])
    ),
})
