"""Shared logging utility for the Product Agent.

Includes OpenTelemetry context fields (trace_id / span_id) in every log line
so logs can be correlated with traces in Grafana / Tempo.
"""

import logging
import sys


class OTelContextDefaultsFilter(logging.Filter):
    """Inject default OTel context fields when the OTel logging
    instrumentation hasn't attached them (e.g. outside a request span).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "otelTraceID"):
            record.otelTraceID = "-"
        if not hasattr(record, "otelSpanID"):
            record.otelSpanID = "-"
        if not hasattr(record, "otelTraceSampled"):
            record.otelTraceSampled = False
        return True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(OTelContextDefaultsFilter())
        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s %(levelname)s [%(name)s] "
                "[trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] "
                "- %(message)s"
            ),
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
