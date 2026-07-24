#!/usr/bin/env bash
# ATLAS çok-platform taşınabilir bundle ÜRETİCİ — bakımcı için, İNTERNET GEREKİR.
# Windows/Linux/macOS için dist/atlas-<hedef>/ altında bağımsız ağaçlar üretir.
#
#   ./make-portable.sh                         # tüm hedefler
#   ./make-portable.sh --targets linux-x86_64  # seçili hedef
#   ./make-portable.sh --list                  # hedefleri listele
set -euo pipefail
H="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python)"
exec "$PY" "$H/tools/make_portable.py" "$@"
