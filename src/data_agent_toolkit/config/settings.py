"""Application configuration using Pydantic Settings.

All config is loaded from environment variables or .env files.
Never hardcode credentials or catalog names.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Data Agent Toolkit.

    Environment variables override defaults. Use a .env file for local dev.
    In Databricks, set these via cluster env vars or Databricks Secrets.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DAT_",  # DAT_CATALOG_NAME -> catalog_name
        case_sensitive=False,
    )

    # ── Databricks workspace ──
    databricks_host: str = ""
    databricks_token: str = ""  # Only for local dev; use OAuth in production

    # ── Unity Catalog ──
    catalog_name: str = "agent_toolkit"
    schema_name: str = "default"
    agent_history_table: str = "agent_run_history"
    template_registry_table: str = "template_registry"

    # ── Mosaic AI Model Serving ──
    model_serving_endpoint: str = "databricks-meta-llama-3-1-70b-instruct"
    embedding_endpoint: str = "databricks-bge-large-en"

    # ── Observability ──
    mlflow_experiment_name: str = "/Shared/data-agent-toolkit"
    langsmith_tracing_enabled: bool = False
    langsmith_project: str = "data-agent-toolkit"

    # ── Guardrails ──
    max_input_length: int = 10000
    pii_detection_enabled: bool = True
    human_approval_required_tools: list[str] = [
        "create_ado_feature",
        "delete_table",
        "trigger_pbi_refresh",
    ]

    @property
    def agent_history_path(self) -> str:
        return f"{self.catalog_name}.{self.schema_name}.{self.agent_history_table}"

    @property
    def template_registry_path(self) -> str:
        return f"{self.catalog_name}.{self.schema_name}.{self.template_registry_table}"


# Singleton — import this everywhere
settings = Settings()
