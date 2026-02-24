"""SI3DC — Prometheus Metrics.

Application metrics for monitoring with Prometheus/Grafana.
"""

from __future__ import annotations

import time

from prometheus_client import Counter, Histogram, Info, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ── Metric definitions ───────────────────────────────────────────────

APP_INFO = Info("si3dc", "SI3DC Application Info")
APP_INFO.info({"version": "1.0.0", "service": "si3dc-backend"})

REQUEST_COUNT = Counter(
    "si3dc_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "si3dc_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

AI_PIPELINE_DURATION = Histogram(
    "si3dc_ai_pipeline_duration_seconds",
    "AI pipeline processing duration",
    ["pipeline_type"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

AI_PIPELINE_ERRORS = Counter(
    "si3dc_ai_pipeline_errors_total",
    "Total AI pipeline errors",
    ["pipeline_type", "error_type"],
)

PATIENT_ACCESS_COUNT = Counter(
    "si3dc_patient_access_total",
    "Patient record access count",
    ["action", "role"],
)

AUTH_EVENTS = Counter(
    "si3dc_auth_events_total",
    "Authentication events",
    ["event_type"],  # login_success, login_failure, token_refresh
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        endpoint = request.url.path
        method = request.method

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=response.status_code,
        ).inc()

        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

        return response
