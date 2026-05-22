import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        print(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )
        return response
