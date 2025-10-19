from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from . import increment_counter, observe_histogram


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, buckets=None) -> None:
        super().__init__(app)
        self.buckets = buckets or [0.1, 0.3, 1, 3, 10]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration = time.perf_counter() - start
            route = request.url.path
            status = getattr(response, "status_code", 500) if response else 500
            increment_counter(
                "http_requests_total",
                labels={"method": request.method, "path": route, "status": str(status)},
                help_text="Total HTTP requests received",
            )
            observe_histogram(
                "http_request_duration_seconds",
                duration,
                labels={"method": request.method, "path": route},
                help_text="HTTP request duration in seconds",
                buckets=self.buckets,
            )
