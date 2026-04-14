"""Lazy MLflow tracing for LLM pipeline observability.

When ``ENABLE_MLFLOW_TRACING`` is set to ``true``, each decorated node
is recorded as an MLflow trace span (latency, inputs, outputs). When
disabled, the decorator is a zero-cost no-op — safe for tests and CI.

Environment variables:
    ENABLE_MLFLOW_TRACING   – "true" to enable (default: false)
    MLFLOW_TRACKING_URI     – MLflow server URI (default: http://localhost:5000)
    MLFLOW_EXPERIMENT_NAME  – experiment name (default: product-agent-llm-traces)
"""

from __future__ import annotations

import os
from typing import Any, Callable, TypeVar, cast

try:
    import mlflow  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    mlflow = None  # type: ignore[assignment]

from ceramicraft_product_agent.utils.logger import get_logger

F = TypeVar("F", bound=Callable[..., Any])

logger = get_logger(__name__)

MLFLOW_EXPERIMENT_NAME = os.environ.get(
    "MLFLOW_EXPERIMENT_NAME",
    "product-agent-llm-traces",
)
LLM_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")

_tracing_initialized = False


def _is_tracing_enabled() -> bool:
    return os.environ.get("ENABLE_MLFLOW_TRACING", "false").lower() == "true"


def init_tracing_context() -> None:
    """Initialize the MLflow tracking URI and experiment (idempotent)."""
    global _tracing_initialized

    if _tracing_initialized or not _is_tracing_enabled() or mlflow is None:
        return

    try:
        mlflow.set_tracking_uri(
            os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
        )
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        _tracing_initialized = True
        logger.info(
            "MLflow tracing enabled – experiment=%s model=%s",
            MLFLOW_EXPERIMENT_NAME,
            LLM_MODEL_NAME,
        )
    except Exception as e:
        logger.error("Failed to initialize MLflow tracing: %s", e)


def trace(name: str):
    """Lazy MLflow trace decorator.

    When tracing is disabled, returns the function unchanged so module
    import stays side-effect free in tests and CI.
    """

    def decorator(func: F) -> F:
        if not _is_tracing_enabled() or mlflow is None:
            return func

        init_tracing_context()
        return cast(F, mlflow.trace(name=name)(func))

    return decorator


def safe_update_trace(metadata: dict[str, Any]) -> None:
    """Update current trace metadata only when MLflow tracing is enabled."""
    if not _is_tracing_enabled() or mlflow is None:
        return

    try:
        mlflow.update_current_trace(metadata=metadata)
    except Exception as exc:
        logger.warning("Trace metadata update skipped: %s", exc)
