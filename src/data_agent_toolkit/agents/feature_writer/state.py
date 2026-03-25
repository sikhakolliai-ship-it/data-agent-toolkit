"""State schema for the ADO Feature Writer Agent.

This TypedDict defines every piece of data that flows through the
LangGraph StateGraph. Each node reads from and writes to this state.
"""

from typing import TypedDict


class FeatureWriterState(TypedDict, total=False):
    """State flowing through the Feature Writer graph.

    Maps 1:1 to the Mural diagram nodes:
    Get Ticket Details → Extract Key Info → Identify Non-Standard →
    Detect Missing Info → [Human Review] → Apply Template →
    Produce Final Output → [Get Approval] → END
    """

    # ── Input ──
    ticket_id: str  # RITM###### from ServiceNow
    ticket_text: str  # Raw ticket content

    # ── Extraction ──
    extracted_info: dict  # Structured fields from unstructured ticket
    non_standard_flags: list[str]  # Patterns that don't match known templates
    missing_info: list[str]  # Required fields not found in ticket

    # ── Routing ──
    needs_human_review: bool  # True if missing_info or too many non_standard_flags
    human_feedback: str  # Feedback from human reviewer

    # ── Template selection ──
    selected_template_id: str  # Template chosen from registry
    feature_template: str  # Rendered template content

    # ── Output ──
    draft_feature: str  # Generated ADO feature text
    final_output: str  # Final output after human approval
    analyst_approved: bool  # Approval gate result

    # ── Metadata ──
    error: str  # Error message if something fails
    run_id: str  # Links back to AgentRunRecord
