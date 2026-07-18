"""
Individual LangGraph node implementations.

Each node is a small, focused function with one responsibility, mirroring
the specialized-agent design called for in the spec:
  - security_node        -> Security Agent  (input guardrails)
  - retrieval_node        -> Retrieval Agent (hybrid search)
  - reasoning_node        -> Reasoning Agent (LLM answer synthesis)
  - output_guardrail_node -> Security Agent, output side

Ingestion and Vision agents live in services/ingestion_service.py since
they run on a different trigger (document upload) than the chat graph.
"""

from __future__ import annotations

from app.agents.state import AgentState
from app.guardrails.pipeline import GuardrailsPipeline
from app.llm.router import LLMRouter
from app.retrieval.interfaces import Retriever

_ANSWER_PROMPT = (
    "You are an enterprise assistant. Answer the user's question using ONLY the "
    "context below. Cite sources inline using [chunk_id]. If the context does not "
    "contain the answer, say you do not have enough information.\n\n"
    "Context:\n{context}\n\n"
    "Conversation so far:\n{history}\n\n"
    "Question: {question}\n\nAnswer:"
)


def make_security_node(guardrails: GuardrailsPipeline):
    async def security_node(state: AgentState) -> AgentState:
        report = guardrails.check_user_input(state["user_message"])
        return {**state, "guardrail_flags": report.flags, "blocked": report.blocked}

    return security_node


def make_retrieval_node(retriever: Retriever, guardrails: GuardrailsPipeline, top_k: int):
    async def retrieval_node(state: AgentState) -> AgentState:
        if state.get("blocked"):
            return {**state, "retrieved_chunks": []}

        results = await retriever.retrieve(state["user_message"], top_k=top_k)
        texts = [r.text for r in results]
        clean_texts, context_flags = guardrails.sanitize_retrieved_context(texts)

        chunks = [
            {"chunk_id": r.chunk_id, "text": clean_text, "document_id": r.metadata.document_id, "score": r.score}
            for r, clean_text in zip(results, clean_texts, strict=True)
        ]
        flags = list(state.get("guardrail_flags", [])) + context_flags
        return {**state, "retrieved_chunks": chunks, "guardrail_flags": flags}

    return retrieval_node


def make_reasoning_node(llm_router: LLMRouter):
    async def reasoning_node(state: AgentState) -> AgentState:
        if state.get("blocked"):
            return {
                **state,
                "answer": "Your message was blocked by input safety checks and was not processed.",
                "used_provider": "none",
                "citations": [],
            }

        chunks = state.get("retrieved_chunks", [])
        context = "\n\n".join(f"[{c['chunk_id']}] {c['text']}" for c in chunks) or "No relevant documents found."
        history = "\n".join(
            f"{turn['role']}: {turn['content']}" for turn in state.get("conversation_history", [])
        )

        prompt = _ANSWER_PROMPT.format(context=context, history=history, question=state["user_message"])
        answer, provider = await llm_router.complete(prompt, model_alias="reasoning")

        citations = [{"chunk_id": c["chunk_id"], "document_id": c["document_id"], "snippet": c["text"][:200]} for c in chunks]
        return {**state, "answer": answer.strip(), "used_provider": provider, "citations": citations}

    return reasoning_node


def make_output_guardrail_node(guardrails: GuardrailsPipeline):
    async def output_guardrail_node(state: AgentState) -> AgentState:
        if state.get("blocked"):
            return state

        chunk_ids = {c["chunk_id"] for c in state.get("retrieved_chunks", [])}
        citation_ids = [c["chunk_id"] for c in state.get("citations", [])]
        had_context = bool(state.get("retrieved_chunks"))

        report = guardrails.check_output(state["answer"], citation_ids, chunk_ids, had_context)
        flags = list(state.get("guardrail_flags", [])) + report.flags
        answer = report.sanitized_text or state["answer"]
        return {**state, "answer": answer, "guardrail_flags": flags}

    return output_guardrail_node
