# Architecture Decision Log

This document records key architectural decisions, their context, and reasoning.

---

## ADR-001: LangGraph over CrewAI / AutoGen

**Date:** 2026-03  
**Status:** Accepted

**Context:** Multiple agent frameworks exist (LangGraph 1.0, CrewAI 1.10, OpenAI Agents SDK, AG2/AutoGen, Pydantic AI). Need to choose one for enterprise DE agent workflows.

**Decision:** LangGraph 1.0

**Reasoning:**
- Durable execution: agents can crash and resume from checkpoint
- Explicit control: no hidden prompts, no hidden context engineering
- Human-in-the-loop: first-class interrupt/resume support
- Production maturity: used by LinkedIn, Uber, Klarna, BlackRock
- Databricks native: `databricks-langchain` provides `ChatDatabricks` integration
- 38M+ monthly PyPI downloads vs CrewAI's higher GitHub stars but lower actual usage

**Trade-off:** Steeper learning curve than CrewAI. Accepted because we need production control, not rapid prototyping.

---

## ADR-002: MLflow 3 as primary observability (LangSmith as dev companion)

**Date:** 2026-03  
**Status:** Accepted

**Context:** Need agent tracing, evaluation, and monitoring. MLflow 3 and LangSmith both support LangGraph.

**Decision:** MLflow 3 for production, LangSmith for dev/debug. Both coexist.

**Reasoning:**
- MLflow 3 is native to Databricks — traces stay inside Unity Catalog governance boundary
- MLflow 3 GenAI evaluation with LLM-as-judge scorers meets enterprise audit requirements
- LangSmith provides superior debugging UX during development
- No vendor lock-in: MLflow is open-source, OpenTelemetry-compatible

---

## ADR-003: Delta Lake for agent state persistence (not PostgreSQL)

**Date:** 2026-03  
**Status:** Accepted

**Context:** Agent execution records (AgentRunRecord) need persistent storage for audit and Phase 2 agent discovery.

**Decision:** Delta Lake tables in Unity Catalog

**Reasoning:**
- Unified lakehouse: same governance, same catalog, same permissions as all DE data
- Time travel: can query historical agent states at any point in time
- Schema evolution: AgentRunRecord schema will grow as we add agents
- No additional infrastructure: no separate Postgres instance to manage
- Phase 2 discovery: `get_related_runs()` is a simple Spark SQL query

---

## ADR-004: uv over Poetry for package management

**Date:** 2026-03  
**Status:** Accepted

**Context:** Databricks default-python bundle template now requires uv.

**Decision:** uv with pyproject.toml

**Reasoning:**
- Required by Databricks CLI 0.258+ for bundle template
- 10-100x faster than Poetry for dependency resolution
- Single lockfile (uv.lock) for reproducible builds
- Workspace support for future monorepo growth

---

## ADR-005: Pydantic over dataclasses for state schemas

**Date:** 2026-03  
**Status:** Accepted

**Decision:** Pydantic BaseModel for AgentRunRecord, TemplateRegistryEntry. TypedDict for LangGraph state.

**Reasoning:**
- Pydantic provides validation, serialization (model_dump), and Settings
- TypedDict is what LangGraph StateGraph expects for state
- Both are type-safe and mypy-compatible
- Pydantic Settings handles env-based configuration cleanly
