"""Shared test fixtures.

Provides mock LLM, mock Spark session, and sample data
for unit tests that don't need real infrastructure.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage


class MockLLM:
    """Mock LLM that returns predictable responses for testing."""

    def __init__(self, response: str = "Mock LLM response") -> None:
        self.response = response
        self.call_count = 0

    def invoke(self, messages: list, **kwargs: object) -> AIMessage:
        self.call_count += 1
        return AIMessage(content=self.response)


@pytest.fixture
def mock_llm() -> MockLLM:
    """Provide a mock LLM for unit tests."""
    return MockLLM()


@pytest.fixture
def mock_spark() -> MagicMock:
    """Provide a mock SparkSession for unit tests."""
    spark = MagicMock()
    spark.createDataFrame.return_value = MagicMock()
    spark.table.return_value = MagicMock()
    spark.sql.return_value = MagicMock()
    return spark


@pytest.fixture
def sample_ticket_state() -> dict:
    """Provide a sample Feature Writer state for testing."""
    return {
        "ticket_id": "RITM0012345",
        "ticket_text": """
        Request: New data pipeline for Customer Analytics
        Business Need: Marketing team needs daily customer segmentation data
        Source: Salesforce CRM (customer_accounts table)
        Target: Gold layer analytics database
        Priority: High
        Timeline: Need by end of Q2
        Requestor: Marketing Analytics Team
        """,
        "extracted_info": {},
        "non_standard_flags": [],
        "missing_info": [],
        "needs_human_review": False,
        "error": "",
    }
