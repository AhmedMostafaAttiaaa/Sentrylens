#!/usr/bin/env bash
# Pulls every model referenced in configs/base.yaml into the running Ollama instance.
set -euo pipefail

OLLAMA_HOST_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

MODELS=(
  "qwen3:8b"
  "llama3.3:8b"
  "deepseek-r1:8b"
  "gemma3:4b"
  "qwen2.5-vl:7b"
  "bge-m3"
)

for model in "${MODELS[@]}"; do
  echo "Pulling ${model} ..."
  curl -s "${OLLAMA_HOST_URL}/api/pull" -d "{\"name\": \"${model}\"}"
  echo
done
