"""
OpenTelemetry middleware for FastAPI.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi_bootstrap.utils.telemetry import add_span_attributes
import time
from typing import Callable, Any

class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds request context to the current span.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        # Record start time
        start_time = time.perf_counter()

        # Add request information to the current span
        add_span_attributes({
            "http.method": request.method,
            "http.url": str(request.url),
            "http.host": request.headers.get("host", ""),
            "http.user_agent": request.headers.get("user-agent", ""),
            "http.client_ip": request.client.host if request.client else "",
        })

        # Process the request
        try:
            response = await call_next(request)

            # Add response information to the current span
            add_span_attributes({
                "http.status_code": response.status_code,
                "http.response_content_length": int(response.headers.get("content-length", 0)),
            })

            # Record request duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            add_span_attributes({
                "http.request_duration_ms": duration_ms,
            })

            return response

        except Exception as e:
            # Add error information to the current span
            add_span_attributes({
                "error": True,
                "error.type": e.__class__.__name__,
                "error.message": str(e),
            })

            # Record request duration even on error
            duration_ms = (time.perf_counter() - start_time) * 1000
            add_span_attributes({
                "http.request_duration_ms": duration_ms,
            })

            raise
