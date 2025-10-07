from prometheus_client import (
    Counter,
    Histogram,
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

REQUESTS_TOTAL = Counter(
    "ps_requests_total",
    "Total requests received",
    labelnames=["route", "method", "tenant", "outcome"],
)

REDACTIONS_TOTAL = Counter(
    "ps_redactions_total",
    "Total redactions performed",
    labelnames=["tenant", "type"],
)
