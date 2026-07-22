# Sentrylens — Setup & Test Commands

## 1. Clone and set up

```bash
git clone https://github.com/AhmedMostafaAttiaaa/Sentrylens.git
cd Sentrylens

cp .env.example .env
# edit .env to add GROQ_API_KEY (fallback LLM) or LLAMAPARSE_API_KEY (optional)

pip install uv
uv pip install --system -e ".[dev]"
```

## 2. Start infrastructure (Qdrant, Postgres, Redis, Ollama)

```bash
docker compose -f docker/docker-compose.yml up -d qdrant postgres redis ollama

docker compose -f docker/docker-compose.yml ps
```

## 3. Pull the required Ollama models

```bash
bash scripts/pull_ollama_models.sh

# or manually
curl http://localhost:11434/api/pull -d '{"name": "qwen3:8b"}'
curl http://localhost:11434/api/pull -d '{"name": "bge-m3"}'
curl http://localhost:11434/api/pull -d '{"name": "qwen2.5-vl:7b"}'
```

## 4. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 5. Run the automated tests

```bash
pytest -v
```

## 6. Manual smoke test (curl)

```bash
# health check
curl http://localhost:8000/health

# issue a demo JWT
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "test-user", "roles": ["admin"]}'

# list available MCP skills
curl http://localhost:8000/skills

# upload a document
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@/path/to/sample.pdf"

# search indexed documents
curl "http://localhost:8000/documents/search?query=your+search+term&top_k=5"

# ask a question via the chat/agent pipeline
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session", "message": "What does the document say about pricing?"}'

# streaming chat
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session", "message": "Summarize the key points"}'

# run a skill directly (calculator example)
curl -X POST http://localhost:8000/skills/calculator/run \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"expression": "12 * (3 + 4)"}}'
```

## 7. Open the UI and API docs

```bash
open http://localhost:8000/ui/          # macOS
xdg-open http://localhost:8000/ui/      # Linux

open http://localhost:8000/docs
```

## 8. Optional: run the MCP server standalone

```bash
uv pip install --system mcp
python -m app.mcp.server
```

## 9. Optional: run everything in Docker

```bash
make docker-up
# equivalent to:
docker compose -f docker/docker-compose.yml up --build
```

## 10. Tear down

```bash
docker compose -f docker/docker-compose.yml down

# to also wipe volumes (qdrant/postgres/ollama data)
docker compose -f docker/docker-compose.yml down -v
```

## 11. Troubleshooting

```bash
# check container logs if a service fails to start
docker compose -f docker/docker-compose.yml logs -f api

# confirm Ollama has the required models pulled
curl http://localhost:11434/api/tags

# confirm Qdrant is reachable and check the collection
curl http://localhost:6333/collections/vision_rag_documents
```