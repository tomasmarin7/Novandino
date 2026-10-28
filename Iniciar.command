#!/bin/bash
set -u
cd -- "$(dirname -- "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
litio_python=""
for candidate in python3.12 python3.13 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    litio_python="$candidate"
    break
  fi
done
if [[ -z "$litio_python" ]]; then
  echo "Necesitas Python 3.11 o posterior. Recomendado: Python 3.12 para macOS."
  echo "Instálalo desde https://www.python.org/downloads/macos/ y vuelve a abrir este archivo."
  read -r -p "Pulsa Enter para cerrar. "
  exit 1
fi
"$litio_python" iniciar.py
litio_status=$?
if [[ $litio_status -ne 0 && $litio_status -ne 130 ]]; then
  echo ""
  echo "No se pudo iniciar el simulador. Copia el error de arriba para revisarlo."
  read -r -p "Pulsa Enter para cerrar. "
fi
exit "$litio_status"
