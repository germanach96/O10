#!/bin/bash
# Instala las dependencias del motor al empezar cada sesión en la nube de Claude Code,
# para que el pipeline, los tests y el análisis (scipy, statsmodels) funcionen siempre.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"
pip install -q --disable-pip-version-check --root-user-action=ignore -r requirements.txt

# El motor se importa como paquete (python -m motor.pipeline) desde la raíz del repo
echo "export PYTHONPATH=\"$CLAUDE_PROJECT_DIR\${PYTHONPATH:+:\$PYTHONPATH}\"" >> "$CLAUDE_ENV_FILE"
