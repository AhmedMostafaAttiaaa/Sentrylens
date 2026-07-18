"""
Coordinator Agent - assembles the LangGraph state graph wiring together
the Security, Retrieval, Reasoning and output-guardrail nodes.

    security -> retrieval -> reasoning -> output_guardrail -> END

Each stage only depends on AgentState, so new nodes (a dedicated Tool
Agent step that calls MCP skills, a Vision Agent step for multimodal
questions, etc.) can be inserted by adding a node and an edge, without
modifying the others.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.nodes import (
    make_output_guardrail_node,
    make_reasoning_node,
    make_retrieval_node,
    make_security_node,
)
from app.agents.state import AgentState
from app.core.config import Settings
from app.guardrails.pipeline import GuardrailsPipeline
from app.llm.router import LLMRouter
from app.retrieval.interfaces import Retriever


def build_chat_graph(settings: Settings, retriever: Retriever, llm_router: LLMRouter, guardrails: GuardrailsPipeline):
    graph = StateGraph(AgentState)

    graph.add_node("security", make_security_node(guardrails))
    graph.add_node("retrieval", make_retrieval_node(retriever, guardrails, settings.retrieval.top_k))
    graph.add_node("reasoning", make_reasoning_node(llm_router))
    graph.add_node("output_guardrail", make_output_guardrail_node(guardrails))

    graph.set_entry_point("security")
    graph.add_edge("security", "retrieval")
    graph.add_edge("retrieval", "reasoning")
    graph.add_edge("reasoning", "output_guardrail")
    graph.add_edge("output_guardrail", END)

    return graph.compile()
