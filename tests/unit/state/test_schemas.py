"""Unit tests for agent state schemas."""

from datetime import datetime

from data_agent_toolkit.state.schemas import AgentRunRecord, AgentRunStatus, TemplateRegistryEntry


class TestAgentRunRecord:
    def test_creates_with_required_fields(self):
        record = AgentRunRecord(
            run_id="test-123",
            agent_name="feature_writer",
            trigger_source="RITM0012345",
            trigger_type="servicenow_ticket",
        )
        assert record.status == AgentRunStatus.STARTED
        assert record.human_review_required is False
        assert record.total_tokens_used == 0
        assert isinstance(record.created_at, datetime)

    def test_serializes_to_dict(self):
        record = AgentRunRecord(
            run_id="test-456",
            agent_name="dq_checker",
            trigger_source="pipeline_failure_001",
            trigger_type="pipeline_failure",
            status=AgentRunStatus.COMPLETED,
            extracted_entities={"table": "customers", "issue": "null_count_spike"},
        )
        data = record.model_dump()
        assert data["agent_name"] == "dq_checker"
        assert data["status"] == "completed"
        assert data["extracted_entities"]["table"] == "customers"

    def test_all_statuses_valid(self):
        for status in AgentRunStatus:
            record = AgentRunRecord(
                run_id=f"test-{status.value}",
                agent_name="test",
                trigger_source="test",
                trigger_type="test",
                status=status,
            )
            assert record.status == status


class TestTemplateRegistryEntry:
    def test_creates_template_entry(self):
        entry = TemplateRegistryEntry(
            template_id="tmpl-001",
            template_name="Standard ETL Feature",
            domain="ado_feature",
            signature_keywords=["etl", "pipeline", "data migration"],
            template_path="/Volumes/agent_toolkit/templates/etl_feature.md",
            owner="data_engineering_team",
        )
        assert entry.is_active is True
        assert "etl" in entry.signature_keywords
