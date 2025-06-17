import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class CacheBustingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Adds a timestamp to static file URLs to prevent caching issues.
        Example: /static/css/styles.css -> /static/css/styles.css?t=1678886400
        """
        if request.url.path.startswith("/static/") and "t=" not in request.url.query:
            timestamp = int(time.time())
            request.scope["query_string"] = f"t={timestamp}".encode()

        response = await call_next(request)
        return response
