from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from users.models import CustomUser

from .auth import KeycloakJWTAuthentication


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get('query_string', b'').decode())
        token_list = query.get('token')
        user = AnonymousUser()

        if token_list:
            token = token_list[0]
            try:
                authenticator = KeycloakJWTAuthentication()
                validated = authenticator._decode(token)
                authenticator._check_audience(validated)
                username = (
                    validated.get('preferred_username')
                    or validated.get('email')
                    or validated['sub']
                )
                user, _ = await database_sync_to_async(
                    CustomUser.objects.update_or_create,
                )(
                    username=username,
                    defaults={
                        'email': validated.get('email', ''),
                        'first_name': validated.get('given_name', ''),
                        'last_name': validated.get('family_name', ''),
                        'is_active': True,
                    },
                )
            except Exception:
                user = AnonymousUser()

        scope['user'] = user
        return await super().__call__(scope, receive, send)


def token_auth_middleware_stack(inner):
    from channels.auth import AuthMiddlewareStack

    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
