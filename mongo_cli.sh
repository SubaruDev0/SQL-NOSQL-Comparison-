#!/usr/bin/env bash
# Wrapper para usar mongosh si está instalado; si no, usa mongo_inspect.py
# Uso:
#   ./mongo_cli.sh --dbs
#   ./mongo_cli.sh --count
#   ./mongo_cli.sh --sample

set -euo pipefail

if command -v mongosh >/dev/null 2>&1; then
  mongosh "$@"
else
  # Fallback: usar el script Python incluido
  python3 mongo_inspect.py "$@"
fi

