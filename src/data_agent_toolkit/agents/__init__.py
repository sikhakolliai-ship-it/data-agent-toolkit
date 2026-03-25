"""LangGraph agent definitions for Data Engineering workflows.

Phase 1 (Individual Productivity):
    - feature_writer: ADO Feature Writer from ServiceNow tickets
    - sttm_writer: Source-to-Target Mapping generator
    - dq_checker: Data Quality Rule Writer + Auto-Healer
    - pipeline_config_writer: Declarative Automation Bundle YAML generator
    - test_data_generator: Synthetic test data from UC schemas

Phase 2 (Connected):
    - pipeline_healer: Auto-healing pipeline agent with cross-agent awareness
"""
