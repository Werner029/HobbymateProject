from drf_spectacular.extensions import OpenApiAuthenticationExtension


class KeycloakJWTAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'helper.auth.KeycloakJWTAuthentication'
    name = 'keycloakJWT'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
