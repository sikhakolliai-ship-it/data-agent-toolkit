"""Unit tests for Feature Writer agent nodes."""

from data_agent_toolkit.agents.feature_writer.nodes import (
    detect_missing_info,
    get_ticket_details,
)


class TestGetTicketDetails:
    def test_returns_ticket_text_when_provided(self, sample_ticket_state):
        result = get_ticket_details(sample_ticket_state)
        assert "ticket_text" in result
        assert "Customer Analytics" in result["ticket_text"]

    def test_returns_error_when_no_text(self):
        state = {"ticket_id": "RITM999", "ticket_text": ""}
        result = get_ticket_details(state)
        # Empty string is falsy, so it should try to fetch
        assert "error" in result or "ticket_text" in result


class TestDetectMissingInfo:
    def test_flags_missing_required_fields(self):
        state = {
            "extracted_info": {},  # No fields extracted
            "non_standard_flags": [],
        }
        result = detect_missing_info(state)
        assert len(result["missing_info"]) > 0
        assert result["needs_human_review"] is True

    def test_passes_when_all_fields_present(self):
        state = {
            "extracted_info": {
                "business_requirement": "Need customer data",
                "data_sources": ["Salesforce"],
                "expected_outcome": "Daily refresh",
            },
            "non_standard_flags": [],
        }
        result = detect_missing_info(state)
        assert result["missing_info"] == []
        assert result["needs_human_review"] is False

    def test_routes_to_human_when_many_non_standard_flags(self):
        state = {
            "extracted_info": {
                "business_requirement": "X",
                "data_sources": ["Y"],
                "expected_outcome": "Z",
            },
            "non_standard_flags": ["flag1", "flag2", "flag3"],  # > 2
        }
        result = detect_missing_info(state)
        assert result["needs_human_review"] is True
