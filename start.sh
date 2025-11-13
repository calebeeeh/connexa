#!/bin/bash
# Script de inicialização robusto para a Render

# Adiciona o diretório binário do venv ao PATH do shell
export PATH="/opt/render/project/src/.venv/bin:$PATH"

# Executa o uvicorn usando o python que agora está no PATH
exec python3 -m uvicorn src.app:app --host 0.0.0.0 --port $PORT