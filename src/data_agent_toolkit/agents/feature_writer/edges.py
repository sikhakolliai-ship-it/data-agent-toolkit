"""Conditional edge logic for the Feature Writer Agent.

Edges determine the flow between nodes based on state.
Separated from nodes so routing decisions are auditable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_agent_toolkit.agents.feature_writer.state import FeatureWriterState


def should_route_to_human(state: FeatureWriterState) -> str:
    """Decide whether to route to human review or proceed to template.

    Routes to human if:
    - Any required info is missing
    - More than 2 non-standard flags detected
    - An error occurred during extraction
    """
    if state.get("error"):
        return "human_review"

    if state.get("missing_info"):
        return "human_review"

    if len(state.get("non_standard_flags", [])) > 2:
        return "human_review"

    return "apply_template"


def should_request_approval(state: FeatureWriterState) -> str:
    """Decide whether the final output needs analyst approval.

    In enterprise settings, all agent outputs that create
    external artifacts (ADO work items) require approval.
    """
    # Always require approval for ADO feature creation
    return "get_approval"
