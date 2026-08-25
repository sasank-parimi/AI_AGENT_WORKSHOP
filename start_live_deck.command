#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -x ".venv/bin/python" ]; then
  exec .venv/bin/python server.py
fi

echo "The local virtual environment is not ready."
echo "Run the setup commands in README.md, then open this launcher again."
exit 1
