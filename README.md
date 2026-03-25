# Data Agent Toolkit

> Enterprise-grade AI agents for Data Engineering teams — built on LangGraph + Databricks + MLflow 3.

[![CI](https://github.com/sikhakolliai-ship-it/data-agent-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/sikhakolliai-ship-it/data-agent-toolkit/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![LangGraph 1.0](https://img.shields.io/badge/LangGraph-1.0.10-green.svg)](https://github.com/langchain-ai/langgraph)
[![MLflow 3](https://img.shields.io/badge/MLflow-3.x-orange.svg)](https://mlflow.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What This Is

A production-ready toolkit for building AI agents that automate Data Engineering workflows. Not another chatbot or RAG demo — these agents read tickets, write features, generate configs, heal pipelines, and persist every decision to Delta Lake for audit.

Built for engineers transitioning from traditional Data Engineering to GenAI/Agentic AI architecture.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                  Human-led Agent Orchestration                 │
│                                                               │
│  Phase 1: Individual Productivity Agents (Disconnected)       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │  Feature     │ │  STTM       │ │  DQ Rule Writer +       │ │
│  │  Writer      │ │  Writer     │ │  Auto-Healer            │ │
│  └──────┬───────┘ └──────┬──────┘ └────────────┬────────────┘ │
│         │                │                      │              │
│  ┌──────▼────────────────▼──────────────────────▼───────────┐ │
│  │          Agent State & Memory Infrastructure              │ │
│  │     AgentRunRecord → Delta Lake (Unity Catalog)           │ │
│  │     get_related_runs() → Phase 2 agent discovery          │ │
│  └──────────────────────────┬────────────────────────────────┘ │
│                              │                                 │
│  Phase 2: Connected Agents   │                                 │
│  ┌───────────────────────────▼───────────────────────────────┐ │
│  │  Pipeline Healer (cross-agent awareness, auto-remediation)│ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Enterprise Layers: Guardrails │ Governance │ Resilience │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Observability: MLflow 3 Tracing + LangSmith (dev)      │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## What This Demonstrates

| Skill | Implementation |
|-------|---------------|
| **LangGraph 1.0 StateGraph** | Multi-node agents with conditional edges, human-in-the-loop |
| **Pydantic State Schemas** | Type-safe `FeatureWriterState`, `AgentRunRecord` with validation |
| **Delta Lake Persistence** | Execution audit trail via `AgentStateWriter` in Unity Catalog |
| **MLflow 3 GenAI Tracing** | Full observability — every LLM call, tool invocation, decision |
| **Enterprise Guardrails** | PII detection, prompt injection blocking, secret scrubbing |
| **Governance & Compliance** | UC ACLs, audit logging, Databricks Secrets, data classification |
| **Production Resilience** | Exponential backoff, circuit breaker, fallback model routing |
| **Declarative Automation Bundles** | Multi-environment deployment via CI/CD |
| **Agent Evaluation** | LLM-as-judge quality scoring with golden datasets |

## Agents

### Feature Writer Agent (Phase 1)
`ServiceNow RITM → Extract Key Info → Check Non-Standard Patterns → Detect Missing Info → [Human Review] → Apply Template → Draft ADO Feature → [Approval] → END`

### STTM Writer Agent (Phase 1)
`UC Source Columns → Generate Mappings via Mosaic AI Model Serving → Validate → Write to Delta`

### DQ Checker + Auto-Healer (Phase 1)
`Read UC Schema → Sample Data → Generate Lakeflow Spark Declarative Pipeline Expectations → On Failure: Diagnose → Propose Fix → [Auto-Apply | Human Review]`

### Pipeline Config Writer (Phase 1)
`Natural Language Requirements → Generate Declarative Automation Bundle YAML → Output databricks.yml + Lakeflow Job Definitions`

### Pipeline Healer (Phase 2)
`Monitor Lakeflow Jobs → Read Error Logs → Diagnose Root Cause → Apply Remediation → Create Incident Report`

## Quick Start

```bash
# Prerequisites: Python 3.11+, uv
# Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/sikhakolliai-ship-it/data-agent-toolkit.git
cd data-agent-toolkit
uv sync --all-extras

# Run tests
make test

# Run the Feature Writer agent (demo mode)
uv run python -c "
from data_agent_toolkit.agents.feature_writer import create_feature_writer_agent
# agent = create_feature_writer_agent()  # Requires Databricks connection
print('Feature Writer agent module loaded successfully')
"
```

## Project Structure

```
data-agent-toolkit/
├── .github/workflows/ci.yml       # CI: lint + type-check + test
├── bundles/                        # Declarative Automation Bundles
│   ├── databricks.yml              # Multi-environment config
│   └── resources/                  # Lakeflow Jobs, pipelines
├── src/data_agent_toolkit/         # Production source code
│   ├── agents/                     # LangGraph agent definitions
│   │   ├── feature_writer/         # graph.py, state.py, nodes.py, edges.py
│   │   ├── sttm_writer/
│   │   ├── dq_checker/
│   │   ├── pipeline_config_writer/
│   │   ├── test_data_generator/
│   │   └── pipeline_healer/
│   ├── state/                      # AgentRunRecord + Delta persistence
│   ├── guardrails/                 # Input/output validation
│   ├── governance/                 # Access control, audit, secrets
│   ├── resilience/                 # Retry, circuit breaker
│   ├── observability/              # MLflow 3 + LangSmith tracing
│   ├── tools/                      # MCP-compatible tool wrappers
│   ├── pipelines/                  # RAG indexer, PBI refresh
│   ├── knowledge/                  # Retriever, embeddings
│   └── config/                     # Pydantic Settings
├── tests/
│   ├── unit/                       # Fast, no infra needed
│   ├── integration/                # Requires Databricks cluster
│   └── evaluation/                 # LLM-as-judge (costs tokens)
├── notebooks/                      # Interactive demos
├── docs/                           # Architecture, decision log
├── pyproject.toml                  # Single source of truth (uv)
├── Makefile                        # Developer shortcuts
└── README.md                       # You are here
```

## Architecture Decision Log

See [docs/decision-log.md](docs/decision-log.md) for why:
- **LangGraph over CrewAI** → Production maturity, durable execution, explicit control
- **MLflow 3 over standalone LangSmith** → Inside Databricks governance boundary
- **Delta Lake over PostgreSQL for state** → Unified lakehouse, UC governance
- **Pydantic over dataclasses** → Validation, serialization, Settings integration
- **uv over Poetry** → Required by Databricks default-python bundle template

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Agent Framework | LangGraph | 1.0.10 |
| LLM Integration | databricks-langchain (ChatDatabricks) | 0.5+ |
| Observability | MLflow 3 + LangSmith | 3.7+ |
| State Persistence | Delta Lake + Unity Catalog | — |
| Deployment | Declarative Automation Bundles | CLI 0.275+ |
| Orchestration | Lakeflow Jobs | GA |
| Pipelines | Lakeflow Spark Declarative Pipelines | GA |
| Package Manager | uv | 0.6+ |
| Type Safety | Pydantic | 2.7+ |
| Testing | pytest + LLM-as-judge | 8.0+ |

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-agent`)
3. Install pre-commit hooks (`uv run pre-commit install`)
4. Write tests first, then implement
5. Run `make ci` before pushing
6. Open a PR with a clear description

## License

MIT — see [LICENSE](LICENSE) for details.
