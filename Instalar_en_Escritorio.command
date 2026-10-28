#!/bin/bash
set -euo pipefail
litio_source="$(cd -- "$(dirname -- "$0")" && pwd -P)"
litio_destination="$HOME/Desktop/litio-planner"
if [[ "$litio_source" == "$litio_destination" ]]; then
  echo "El proyecto ya está en tu escritorio."
elif [[ -e "$litio_destination" || -L "$litio_destination" ]]; then
  echo "Ya existe $litio_destination. No se ha sobrescrito."
  echo "Renombra esa carpeta si quieres conservarla e instalar esta copia."
  read -r -p "Pulsa Enter para cerrar. "
  exit 1
else
  mkdir -p -- "$litio_destination"
  /usr/bin/rsync -a --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='.pytest_cache' --exclude='.runtime' --exclude='test-results' \
    "$litio_source/" "$litio_destination/"
  echo "Proyecto copiado a $litio_destination"
fi
chmod u+x "$litio_destination/Iniciar.command"
open "$litio_destination"
echo "Abre Iniciar.command dentro de la carpeta para ejecutar el simulador."
