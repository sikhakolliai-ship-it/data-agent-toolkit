"""Observability setup — MLflow 3 for production, LangSmith for dev/debug.

Both coexist. MLflow stays inside the Databricks governance boundary.
LangSmith provides richer debugging UX during development.
"""

from __future__ import annotations

import logging
import os

import mlflow

from data_agent_toolkit.config.settings import settings

logger = logging.getLogger(__name__)


def setup_mlflow_tracing() -> None:
    """Initialize MLflow 3 GenAI tracing.

    Call this once at application startup. Every LangGraph execution
    will be automatically traced via mlflow.langchain.autolog().
    """
    mlflow.set_experiment(settings.mlflow_experiment_name)
    mlflow.langchain.autolog(
        log_models=False,  # Don't log model artifacts (saves storage)
        log_input_examples=True,
        log_model_signatures=True,
    )
    logger.info("MLflow tracing enabled — experiment: %s", settings.mlflow_experiment_name)


def setup_langsmith_tracing() -> None:
    """Initialize LangSmith tracing (dev/debug only).

    Requires LANGCHAIN_API_KEY environment variable.
    Set settings.langsmith_tracing_enabled = True to activate.
    """
    if not settings.langsmith_tracing_enabled:
        logger.info("LangSmith tracing disabled")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    logger.info("LangSmith tracing enabled — project: %s", settings.langsmith_project)


def setup_observability() -> None:
    """Initialize all observability. Call once at startup."""
    setup_mlflow_tracing()
    setup_langsmith_tracing()
    logger.info("Observability initialized")
