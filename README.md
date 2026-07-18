# Vision RAG

A modular, local-first Vision RAG platform. Documents (PDF, scanned PDF, images,
Word, PowerPoint, Excel, Markdown, HTML) are parsed, described (for figures/
charts/tables), chunked, embedded and indexed in Qdrant. Questions are answered
through a hybrid dense + BM25 retrieval pipeline, a cross-encoder reranker, and
an LLM router that prefers local Ollama models and falls back to Groq
automatically. A LangGraph agent graph enforces guardrails on both the way in
and the way out. Every capability is also exposed as an MCP tool.

This is a working reference implementation, not a hosted product. It is meant
to be read, forked, and adapted.

## What is actually implemented vs. pluggable

Everything below runs end to end with the default configuration and no paid
API keys, using Ollama + Tesseract + the local document parser:

- FastAPI backend, async throughout
- LLM router: Ollama primary, Groq fallback, retries, timeouts, health checks
- bge-m3 embeddings via Ollama
- Document parsing for PDF, DOCX, PPTX, XLSX, Markdown, HTML
- Vision descriptions of figures via an Ollama vision model (qwen2.5-vl)
- Four chunking strategies: recursive, sentence window, parent-child, semantic
- Qdrant vector store with metadata filters
- Hybrid retrieval (dense + BM25 + weighted fusion) and cross-encoder reranking
- Guardrails: input validation, PII detection, secrets detection, prompt
  injection / jailbreak heuristics, citation validation, hallucination flagging
- A context firewall that strips instruction-like text out of retrieved
  document chunks before they reach the LLM prompt
- A LangGraph coordinator graph: security -> retrieval -> reasoning -> output
  guardrail
- MCP server exposing every skill as a tool, plus a plain HTTP equivalent
- JWT auth, role checks, a Redis-backed rate limiter
- Conversation memory in Redis
- A plain HTML/CSS/JS UI (no framework, no build step) for upload, search and chat
- Docker Compose stack: api, ollama, qdrant, postgres, redis
- Unit and integration tests (pytest)

The following are wired in as isolated adapters behind their interfaces, but
require an optional dependency or API key you provide, since they are heavy or
paid:

- LlamaParse (cloud parsing) - set `LLAMAPARSE_API_KEY` and
  `parsing.provider: llamaparse` in `configs/base.yaml`; falls back to the
  local parser automatically if unset
- Surya OCR / PaddleOCR - install `surya-ocr` or `paddleocr` and set
  `ocr.provider`; falls back to Tesseract automatically
- Web Search skill - set `WEB_SEARCH_API_URL` / `WEB_SEARCH_API_KEY` for a
  provider of your choice
- Langfuse / OpenTelemetry tracing - config keys are present under
  `observability`; wiring the actual exporter is a small addition in
  `app/core/logging.py` once you pick a backend

## Architecture

```
Client (HTML UI / API client / MCP client)
        |
   FastAPI routers  ->  Guardrails (input)  ->  LangGraph agent graph
        |                                            |
        |                          security -> retrieval -> reasoning -> output guardrail
        |                                            |
        |                                     Hybrid Retriever
        |                                    /              \
        |                          Dense (Qdrant)        BM25 (in-memory)
        |                                    \              /
        |                                  Cross-encoder reranker
        |
   Ingestion pipeline: parser -> vision describer -> chunker -> embedder -> Qdrant
        |
   LLM Router: Ollama (primary) -> Groq (fallback)
```

## Project layout

```
app/
  core/         configuration, logging, security, dependency injection
  schemas/      pydantic request/response and domain models
  llm/          LLM provider interface, Ollama, Groq, router
  embeddings/   embedding provider interface and Ollama (bge-m3) implementation
  parsing/      document parser interface, local parser, LlamaParse adapter
  ocr/          OCR interface, Tesseract, Surya, PaddleOCR, factory
  vision/       vision describer interface and Ollama vision implementation
  chunking/     recursive, sentence window, parent-child, semantic strategies
  vector_db/    vector store interface and Qdrant implementation
  retrieval/    dense, BM25 and hybrid retrievers
  reranker/     reranker interface and cross-encoder implementation
  guardrails/   PII, secrets, prompt injection detectors and the pipeline
  memory/       Redis-backed conversation memory
  mcp/          MCP server and skills (search, summarize, translate, OCR,
                vision analysis, extract tables/images, generate report,
                SQL query, knowledge graph search, calculator, web search,
                filesystem)
  agents/       LangGraph state, nodes, and the coordinator graph
  services/     ingestion service and chat service (orchestration layer)
  routers/      FastAPI endpoints
  repositories/ Postgres data access
  db/           Postgres connection pool and schema bootstrap
configs/        base.yaml plus per-environment overrides
ui/             plain HTML/CSS/JS front end
tests/          pytest unit and integration tests
docker/         Dockerfile and docker-compose.yml
scripts/        helper scripts (pulling Ollama models)
```

## Running locally

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker (for
Qdrant/Postgres/Redis, or Ollama if not installed natively).

```bash
cp .env.example .env
# edit .env if you want Groq fallback (GROQ_API_KEY) or LlamaParse

docker compose -f docker/docker-compose.yml up -d qdrant postgres redis ollama
bash scripts/pull_ollama_models.sh

uv pip install --system -e ".[dev]"
uvicorn app.main:app --reload
```

Then open `http://localhost:8000/ui/` for the web interface, or
`http://localhost:8000/docs` for the OpenAPI docs.

To run the whole stack (including the API) in Docker:

```bash
make docker-up
```

## Running the MCP server standalone

```bash
uv pip install --system mcp
python -m app.mcp.server
```

## Configuration

All behavior is controlled from `configs/base.yaml`, with `configs/development.yaml`,
`configs/staging.yaml` and `configs/production.yaml` overriding it depending on
`APP_ENV`. Values wrapped in `${VAR_NAME}` are resolved from environment
variables / `.env`. Nothing is hardcoded in application code: swapping the
chunking strategy, retrieval mode, reranker, or OCR engine is a one-line
YAML change.

## Testing

```bash
make test
```

## Security notes

- Retrieved document content is treated strictly as data. The context firewall
  (`app/guardrails/pipeline.py::sanitize_retrieved_context`) strips
  instruction-like text out of every chunk before it is placed into a prompt.
- The calculator skill evaluates expressions through Python's `ast` module,
  never `eval`.
- The SQL query skill only accepts `SELECT` statements.
- The filesystem skill is sandboxed to a configured root directory and
  rejects path traversal.
- JWT secret and database credentials in `.env.example` are placeholders -
  replace them before any real deployment.

## License

MIT. See `LICENSE`.
