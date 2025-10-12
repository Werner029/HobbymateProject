import logging

__all__ = []


class DRFRequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('drf.request')

    def __call__(self, request):
        body = request.body.decode(errors='replace')[:2_000]
        self.logger.info(
            'REQUEST %s %s body=%s',
            request.method,
            request.path,
            body,
        )
        response = self.get_response(request)
        if hasattr(response, 'render') and callable(response.render):
            response.render()

        resp_body = getattr(response, 'content', b'')[:2_000]

        self.logger.info(
            'RESPONSE %s %s %s body=%s',
            request.method,
            request.path,
            response.status_code,
            resp_body,
        )
        return response
