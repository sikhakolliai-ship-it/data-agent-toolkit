"""Agent state persistence to Delta Lake via Unity Catalog.

This is the bridge between Phase 1 (disconnected agents) and
Phase 2 (connected agents). Every agent writes here. Connected
agents read here to discover what other agents have done.
"""

from __future__ import annotations

import logging
from datetime import datetime

from data_agent_toolkit.config.settings import settings
from data_agent_toolkit.state.schemas import AgentRunRecord, AgentRunStatus

logger = logging.getLogger(__name__)


class AgentStateWriter:
    """Persists agent run records to a Unity Catalog managed Delta table.

    Usage:
        writer = AgentStateWriter(spark)
        writer.write_run(record)

        # Phase 2: discover other agents' work on the same ticket
        related = writer.get_related_runs("RITM0012345")
    """

    def __init__(self, spark: SparkSession) -> None:  # noqa: F821
        self.spark = spark
        self.table_path = settings.agent_history_path

    def write_run(self, record: AgentRunRecord) -> None:
        """Append an agent run record to Delta Lake."""
        row = record.model_dump(mode="json")
        df = self.spark.createDataFrame([row])
        df.write.mode("append").saveAsTable(self.table_path)
        logger.info("Wrote agent run %s (%s) to %s", record.run_id, record.agent_name, self.table_path)

    def update_status(
        self,
        run_id: str,
        status: AgentRunStatus,
        output_uri: str | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Update the status of an existing run using MERGE."""
        completed = completed_at or datetime.utcnow()
        self.spark.sql(f"""
            MERGE INTO {self.table_path} AS target
            USING (SELECT '{run_id}' AS run_id) AS source
            ON target.run_id = source.run_id
            WHEN MATCHED THEN UPDATE SET
                target.status = '{status.value}',
                target.output_artifact_uri = '{output_uri or ""}',
                target.completed_at = '{completed.isoformat()}'
        """)
        logger.info("Updated run %s to status %s", run_id, status.value)

    def get_related_runs(self, trigger_source: str) -> list[dict]:
        """Find all completed agent runs for the same trigger source.

        This is the Phase 2 discovery mechanism: when the STTM Writer
        starts processing RITM0012345, it calls this to see if the
        Feature Writer already extracted entities from the same ticket.
        """
        rows = (
            self.spark.table(self.table_path)
            .filter(f"trigger_source = '{trigger_source}'")
            .filter("status = 'completed'")
            .orderBy("created_at")
            .collect()
        )
        logger.info("Found %d related runs for %s", len(rows), trigger_source)
        return [row.asDict() for row in rows]

    def get_latest_run(self, agent_name: str, trigger_source: str) -> dict | None:
        """Get the most recent completed run for a specific agent + trigger."""
        rows = (
            self.spark.table(self.table_path)
            .filter(f"agent_name = '{agent_name}'")
            .filter(f"trigger_source = '{trigger_source}'")
            .filter("status = 'completed'")
            .orderBy("created_at", ascending=False)
            .limit(1)
            .collect()
        )
        return rows[0].asDict() if rows else None
