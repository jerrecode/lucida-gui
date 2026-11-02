#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null || { echo "Python >=3.11 required" >&2; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python >=3.11 required"'
python3 -m venv "$root/.venv"
pip="$root/.venv/bin/python"
if [[ -n "${LUCIDA_API_SOURCE:-}" ]]; then
  "$pip" -m pip install -e "$LUCIDA_API_SOURCE"
else
  "$pip" -m pip install 'git+https://github.com/jerrecode/lucida-api.git@main'
fi
"$pip" -m pip install 'PySide6>=6.6,<7'
"$pip" -m pip install -e "$root" --no-deps
"$pip" -c 'import lucida_gui.app; print("GUI module import OK")'
echo "Run: $root/.venv/bin/lucida-gui"
