#!/usr/bin/env sh
# SPEC 048: ATLAS vault backup systemd --user birimi + timer kurulumu.
# Kullanım: bash tools/scheduling/install-linux.sh [--keep N]
#
# %I% / %P% / %R% / %K% placeholder'ları sed ile doldurulur.
set -eu

KEEP=30
while [ $# -gt 0 ]; do
    case "$1" in
        --keep)
            shift
            KEEP="${1:-30}"
            ;;
        --keep=*)
            KEEP="${1#--keep=}"
            ;;
        -h|--help)
            echo "Kullanım: $0 [--keep N]"
            echo "  --keep N   retention (varsayılan 30)"
            exit 0
            ;;
        *)
            echo "Bilinmeyen argüman: $1" >&2
            exit 2
            ;;
    esac
    shift
done

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ATLAS_BIN="$(command -v atlas || true)"
if [ -z "$ATLAS_BIN" ]; then
    echo "HATA: 'atlas' PATH'te bulunamadı. Önce ATLAS'ı kur:" >&2
    echo "  uv pip install -e $REPO_ROOT" >&2
    exit 1
fi
ARCHIVE_ROOT="$REPO_ROOT/archive"

UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$UNIT_DIR"

TEMPLATE_DIR="$(dirname "$0")"
sed -e "s|%I%|$REPO_ROOT|g" \
    -e "s|%P%|$ATLAS_BIN|g" \
    -e "s|%R%|$ARCHIVE_ROOT|g" \
    -e "s|%K%|$KEEP|g" \
    "$TEMPLATE_DIR/atlas-vault-backup.service" \
    > "$UNIT_DIR/atlas-vault-backup.service"
cp "$TEMPLATE_DIR/atlas-vault-backup.timer" \
   "$UNIT_DIR/atlas-vault-backup.timer"

systemctl --user daemon-reload
systemctl --user enable --now atlas-vault-backup.timer

echo ""
echo "OK: atlas-vault-backup.timer kuruldu."
echo "  repo:      $REPO_ROOT"
echo "  atlas:     $ATLAS_BIN"
echo "  archive:   $ARCHIVE_ROOT"
echo "  keep:      $KEEP"
echo "  schedule:  günlük 03:00 UTC (±10 dk jitter)"
echo ""
echo "Durum:      systemctl --user status atlas-vault-backup.timer"
echo "Loglar:     journalctl --user -u atlas-vault-backup"
echo "Manuel tetik: systemctl --user start atlas-vault-backup.service"
