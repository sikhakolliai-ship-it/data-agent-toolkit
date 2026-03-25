"""Agent state schemas — the data contracts for agent execution records.

Every agent execution writes an AgentRunRecord to Delta Lake.
This is the shared memory that enables Phase 2 connected agents.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AgentRunStatus(StrEnum):
    """Lifecycle status of an agent execution."""

    STARTED = "started"
    RUNNING = "running"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class AgentRunRecord(BaseModel):
    """Immutable record of a single agent execution.

    Written to Delta Lake at:
        {catalog}.{schema}.agent_run_history

    Phase 2 agents use get_related_runs() to discover
    what other agents have already done for the same trigger.
    """

    run_id: str = Field(description="Unique execution ID (UUID4)")
    agent_name: str = Field(description="e.g. 'feature_writer', 'dq_checker'")
    agent_version: str = Field(default="0.1.0")

    # What triggered this run
    trigger_source: str = Field(description="e.g. 'RITM0012345'")
    trigger_type: str = Field(description="e.g. 'servicenow_ticket', 'schedule', 'pipeline_failure'")

    # Status tracking
    status: AgentRunStatus = AgentRunStatus.STARTED

    # What the agent consumed
    input_artifacts: list[str] = Field(
        default_factory=list,
        description="URIs to input docs/tickets consumed",
    )
    knowledge_bases_consulted: list[str] = Field(
        default_factory=list,
        description="Which KB entries were retrieved via RAG",
    )

    # What the agent produced
    output_artifact_uri: str | None = Field(
        default=None,
        description="URI to the output (e.g. ADO feature URL, Delta table path)",
    )
    output_artifact_type: str | None = Field(
        default=None,
        description="e.g. 'ado_feature', 'sttm', 'dq_rule', 'pipeline_config'",
    )

    # Reasoning trace — for audit AND downstream agent consumption
    extracted_entities: dict = Field(
        default_factory=dict,
        description="Structured data extracted by the agent",
    )
    decisions_made: list[dict] = Field(
        default_factory=list,
        description="List of decision points with reasoning",
    )

    # Human interaction
    human_review_required: bool = False
    human_reviewer: str | None = None
    human_decision: str | None = None  # "approved", "rejected", "modified"

    # Token usage and cost tracking
    total_tokens_used: int = 0
    total_llm_calls: int = 0
    estimated_cost_usd: float = 0.0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    duration_seconds: float | None = None


class TemplateRegistryEntry(BaseModel):
    """A template that agents use for structured output generation.

    Stored in Delta Lake at:
        {catalog}.{schema}.template_registry

    Shared across all agents — the Feature Writer, STTM Writer,
    Pipeline Config Writer all query this registry.
    """

    template_id: str
    template_name: str
    template_version: str = "1.0.0"
    domain: str = Field(description="e.g. 'ado_feature', 'sttm', 'dq_rule', 'pipeline_config'")
    signature_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords that help the agent select this template",
    )
    template_path: str = Field(description="UC Volumes path to the template file")
    owner: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
