import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helper.settings')

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter

import dialogs.routing

from .ws_auth import token_auth_middleware_stack

application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': token_auth_middleware_stack(
            URLRouter(dialogs.routing.websocket_urlpatterns),
        ),
    },
)
