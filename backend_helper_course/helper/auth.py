import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidSignatureError,
    InvalidTokenError,
    PyJWKClient,
)
from rest_framework import authentication, exceptions

User = get_user_model()
_jwks_client = PyJWKClient(settings.KEYCLOAK_JWKS_URL)

SPA_CLIENT = 'spa'
ALLOWED_ALG = ['RS256']


class KeycloakJWTAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def _decode(self, token: str) -> dict:
        signing_key = _jwks_client.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            signing_key,
            algorithms=ALLOWED_ALG,
            options={
                'verify_exp': True,
                'verify_aud': False,
            },
        )

    @staticmethod
    def _check_audience(payload: dict):
        aud = payload.get('aud', [])
        if isinstance(aud, str):
            aud = [aud]
        if SPA_CLIENT not in aud and payload.get('azp') != SPA_CLIENT:
            raise InvalidAudienceError('Audience mismatch')

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode()
        if not header.lower().startswith(f'{self.keyword.lower()} '):
            return None

        token = header.split()[1]

        try:
            try:
                payload = self._decode(token)
            except InvalidSignatureError:
                _jwks_client.fetch_data()
                payload = self._decode(token)

            self._check_audience(payload)
        except ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('JWT expired')
        except InvalidAudienceError:
            raise exceptions.AuthenticationFailed('JWT audience mismatch')
        except InvalidTokenError:
            raise exceptions.AuthenticationFailed('JWT error: Invalid Token')
        username = (
            payload.get('preferred_username')
            or payload.get('email')
            or payload['sub']
        )
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                'email': payload.get('email', ''),
                'first_name': payload.get('given_name')
                or payload.get('first_name', ''),
                'last_name': payload.get('family_name')
                or payload.get('last_name', ''),
                'is_active': True,
            },
        )
        return (user, payload)
