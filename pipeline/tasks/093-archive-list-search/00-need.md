# Görev 093 — İhtiyaç

SPEC 075 `--list` tüm arşivleri gösterir. Kullanıcı "backup-* arşivlerini
listele" veya "test-XX ile başlayanlar" için `atlas archive --list --json |
jq 'select(...)'` gerek. Doğal ad-regex filtresi yok. SPEC 065 `--search
PATTERN` içerik (arcname) arar; yeni ihtiyaç arşiv **AD** filtresi.

## Kabul

- `atlas archive --list --name-match PATTERN [--sort-by KEY] [--desc]
  [--limit N] [--json]`.
- `PATTERN` regex; geçersiz regex → SPEC HATASI exit 2 (net mesaj).
- Filtre: `entry["archive"]` üzerinde `re.search(PATTERN)`.
- Sıra: `list_entries → name-match filter → sort → limit → output`.
- `--name-match` VERİLMEZSE SPEC 075/079/085 BİT-UYUMLU (filter no-op).
- Boş sonuç: pretty "(esleme yok)", JSON `[]`.
- `--search` ile ORTOGONAL: `--search` içerik arama komutu (list-only
  değil), `--name-match` yalnız `--list` ile birlikte anlamlı (--list
  yoksa ignored — --list dışı archive komutları name-match kullanmaz).
