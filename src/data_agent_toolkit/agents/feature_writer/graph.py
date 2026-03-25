"""ADO Feature Writer Agent — LangGraph StateGraph definition.

This is the entry point. It wires together nodes and edges into
a compilable graph that can be executed, checkpointed, and traced.

Architecture (from Mural diagram):
    SNOW Ticket → Get Ticket Details → Extract Key Info →
    Identify Non-Standard → Detect Missing Info →
    [conditional: Human Review OR Apply Template] →
    Produce Final Output → [approval gate] → END
"""

from __future__ import annotations

import functools
import logging

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph

from data_agent_toolkit.agents.feature_writer.edges import should_route_to_human
from data_agent_toolkit.agents.feature_writer.nodes import (
    apply_feature_template,
    detect_missing_info,
    extract_key_info,
    get_ticket_details,
    identify_non_standard,
    produce_final_output,
    wait_for_human,
)
from data_agent_toolkit.agents.feature_writer.state import FeatureWriterState

logger = logging.getLogger(__name__)


def build_feature_writer_graph(llm: BaseChatModel) -> StateGraph:
    """Construct the Feature Writer StateGraph.

    Args:
        llm: The language model to use (ChatDatabricks, ChatOpenAI, etc.)

    Returns:
        Compiled StateGraph ready for execution.
    """
    graph = StateGraph(FeatureWriterState)

    # ── Add nodes ──
    # Nodes that need the LLM get it via functools.partial
    graph.add_node("get_ticket", get_ticket_details)
    graph.add_node("extract_info", functools.partial(extract_key_info, llm=llm))
    graph.add_node("check_non_standard", functools.partial(identify_non_standard, llm=llm))
    graph.add_node("detect_missing", detect_missing_info)
    graph.add_node("human_review", wait_for_human)
    graph.add_node("apply_template", functools.partial(apply_feature_template, llm=llm))
    graph.add_node("produce_output", produce_final_output)

    # ── Add edges ──
    graph.set_entry_point("get_ticket")
    graph.add_edge("get_ticket", "extract_info")
    graph.add_edge("extract_info", "check_non_standard")
    graph.add_edge("check_non_standard", "detect_missing")

    # Conditional: route to human or proceed to template
    graph.add_conditional_edges(
        "detect_missing",
        should_route_to_human,
        {
            "human_review": "human_review",
            "apply_template": "apply_template",
        },
    )

    # After human review, proceed to template
    graph.add_edge("human_review", "apply_template")
    graph.add_edge("apply_template", "produce_output")
    graph.add_edge("produce_output", END)

    return graph


def create_feature_writer_agent(llm: BaseChatModel | None = None):
    """Create and compile the Feature Writer agent.

    If no LLM is provided, uses ChatDatabricks with the configured
    model serving endpoint.
    """
    if llm is None:
        from databricks_langchain import ChatDatabricks

        from data_agent_toolkit.config.settings import settings

        llm = ChatDatabricks(endpoint=settings.model_serving_endpoint)

    graph = build_feature_writer_graph(llm)
    agent = graph.compile()

    logger.info("Feature Writer agent compiled successfully")
    return agent
