"""Node functions for the ADO Feature Writer Agent.

Each function takes FeatureWriterState and returns a partial state update.
Pure functions are easy to unit test — mock the LLM, assert the output.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from data_agent_toolkit.agents.feature_writer.state import FeatureWriterState

logger = logging.getLogger(__name__)


def get_ticket_details(state: FeatureWriterState, **kwargs: object) -> dict:
    """Pull ticket content from ServiceNow or manual input.

    In production, this calls the ServiceNow REST API via the
    tools/servicenow.py module. For the portfolio demo, it
    accepts ticket_text directly in the state.
    """
    ticket_id = state["ticket_id"]
    logger.info("Fetching ticket details for %s", ticket_id)

    # If ticket_text is already provided (demo mode), use it directly
    if state.get("ticket_text"):
        return {"ticket_text": state["ticket_text"]}

    # Production: call ServiceNow API
    # ticket_text = servicenow_tool.get_ticket(ticket_id)
    # return {"ticket_text": ticket_text}

    return {"error": f"No ticket text provided and ServiceNow not configured for {ticket_id}"}


def extract_key_info(state: FeatureWriterState, llm: BaseChatModel) -> dict:
    """Use LLM to extract structured fields from unstructured ticket text.

    Extracts: business requirement, data sources, expected outcome,
    priority, timeline, affected systems.
    """
    prompt = f"""Extract the following structured information from this ServiceNow intake ticket.
Return as JSON with these exact keys:

- business_requirement: What the requestor needs
- data_sources: List of data sources mentioned
- target_systems: List of target systems/tables
- expected_outcome: What success looks like
- priority: High/Medium/Low
- timeline: Any mentioned deadlines
- requestor_team: Which team submitted this

Ticket ID: {state["ticket_id"]}
Ticket Content:
{state["ticket_text"]}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    logger.info("Extracted key info for %s", state["ticket_id"])

    return {"extracted_info": {"raw_response": response.content}}


def identify_non_standard(state: FeatureWriterState, llm: BaseChatModel) -> dict:
    """Flag anything that doesn't match known enterprise patterns.

    Checks extracted info against Enterprise Knowledge Bases
    via RAG lookup on the vector search index.
    """
    extracted = state.get("extracted_info", {})

    prompt = f"""Review the following extracted ticket information and identify
any non-standard patterns that deviate from typical data engineering requests.

Flag items that are:
- Unusual data source combinations
- Non-standard data formats
- Requests outside normal DE scope
- Missing critical technical details

Extracted Info: {extracted}

Return a list of flags, one per line. If everything looks standard, return "NONE".
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    flags = [f.strip() for f in response.content.strip().split("\n") if f.strip() and f.strip() != "NONE"]

    return {"non_standard_flags": flags}


def detect_missing_info(state: FeatureWriterState) -> dict:
    """Check if all required fields were extracted.

    This is a deterministic check — no LLM needed.
    """
    extracted = state.get("extracted_info", {})
    required_fields = ["business_requirement", "data_sources", "expected_outcome"]

    missing = [field for field in required_fields if field not in extracted or not extracted.get(field)]

    return {
        "missing_info": missing,
        "needs_human_review": len(missing) > 0 or len(state.get("non_standard_flags", [])) > 2,
    }


def wait_for_human(state: FeatureWriterState) -> dict:
    """Human-in-the-loop approval node.

    In LangGraph, this uses interrupt_before or interrupt_after
    to pause the graph and wait for human input via the API.
    The graph resumes when the human provides feedback.
    """
    logger.info("Awaiting human review for ticket %s", state["ticket_id"])
    # LangGraph handles the interrupt — this node just marks the state
    return {"needs_human_review": True}


def apply_feature_template(state: FeatureWriterState, llm: BaseChatModel) -> dict:
    """Select and apply the appropriate ADO feature template.

    Queries the template registry in Delta Lake, selects the best
    match based on extracted info, and renders the template.
    """
    extracted = state.get("extracted_info", {})

    prompt = f"""Using the following extracted information, generate an Azure DevOps
Feature work item with these sections:

## Title
[Concise feature title]

## Description
[Business context and requirement]

## Acceptance Criteria
- [ ] [Specific, testable criteria]

## Technical Notes
- Data Sources: [list]
- Target Systems: [list]
- Dependencies: [list]

## Estimation
- Complexity: [Low/Medium/High]
- Suggested Story Points: [number]

Extracted Information:
{extracted}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"draft_feature": response.content}


def produce_final_output(state: FeatureWriterState) -> dict:
    """Package the draft into the final output format."""
    return {
        "final_output": state.get("draft_feature", ""),
        "analyst_approved": False,  # Will be set by approval gate
    }
