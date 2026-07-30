# 032.1 — İhtiyaç: `atlas doctor --strict` ek denetimler

## Bağlam
032 `atlas doctor --strict` DECISIONS drift'i tarih üzerinden yakalar
— "son giriş 7 gün önce" gibi. Ancak bir hafta boyunca çok commit
atılsa ve DECISIONS'a tek satır yazılsa drift 0 olur, disiplin
görünmez. Ayrıca vault (GBrain notları) yolu bozulsa doctor ne env
tarafında ne quality tarafında hiçbir şey söylemez — sessiz drift.

032'nin hook mekanı (`quality.decisions_drift` alanı +
`_check_decisions_drift`) hazır. Aynı kalıpla iki ek denetim
eklemek küçük iş.

## İhtiyaç (tek cümle)
`quality` bölümüne (a) son 30 gündeki DECISIONS entry sayısı ve
(b) vault sağlık denetimi eklensin; her ikisi `--strict` altında
uyarı verirse exit 9 (mevcut kod aynı).

## Ölçülebilir Başarı
- **M1 — `_count_recent_decisions(days=30)`:** DECISIONS.md'de son
  N günün içindeki `^## YYYY-MM-DD` başlık sayısı. Env override:
  `ATLAS_STRICT_ENTRY_WINDOW_DAYS` (varsayılan 30).
- **M2 — Entry count denetimi:** son 30 günde `entry_count == 0`
  → uyarı ("son 30 günde DECISIONS'a giriş yok"). Alt eşik env:
  `ATLAS_STRICT_MIN_ENTRIES` (varsayılan 1).
- **M3 — `_check_vault_health()`:** vault yolu (`_vault_root()`)
  var mı, içinde en az 1 `.md` var mı. Yoksa uyarı ("vault yok /
  boş"). Var + tamamen boş → uyarı; sadece bir dosya bile olsa
  temiz.
- **M4 — Rapor entegrasyonu:** `quality`'e iki alan eklenir:
  `entry_count: {count, threshold_days, min_entries, warning}` +
  `vault_health: {path, exists, note_count, warning}`.
- **M5 — İnsan format:** `[Kalite kapıları]` bölümüne iki alt satır
  eklenir; uyarı varsa `[!]` prefix.
- **M6 — Strict davranışı:** hem insan hem JSON yolunda **herhangi
  bir `quality.*.warning` doluysa** exit 9 (drift + entry_count +
  vault_health). Yani strict tek kanaldan çıkar (3 kaynaktan).
- **M7 — Bit-uyumluluk:** `--strict` YOKSA her şey mevcut davranış
  gibi (uyarılar bilgi amaçlı görünür).
- **M8 — Test:** +6-8 test — entry count denetim (0 giriş, N giriş,
  eşik env override), vault yok, vault boş, vault dolu, hepsi
  kombine.
- **M9 — DECISIONS:** [KARAR] neden 30 gün penceresi; vault boş
  eşiğinin bir dosya olması; hepsi tek exit 9 yolu.

## Kapsam DIŞI
- Test coverage denetimi (pytest çalıştır) — 032 kararı: "doctor
  pytest çalıştırmaz" (bir aracın işini başka araca gömme).
- Git log entegrasyonu (commit sayısı vs entry) — subprocess dış
  bağımlılık, YAGNI. Yalnız DECISIONS.md dosya-bazlı denetim.
- Env drift denetimi (DEVAM_NOKTASI env tablosu ile senkron mu) —
  YAGNI, dokümantasyon sorumlulu.
- Vault içindeki not-format doğrulaması (Obsidian sözleşme) —
  YAGNI, dokunmadan çalışır.

## Kısıt
- `_cmd_doctor`, `_collect_doctor_report` çıktı sözleşmesi
  KORUNUR; yeni `quality.*` alanları eklenir.
- `_check_decisions_drift` (032) davranışı değişmez.
- Yeni env: `ATLAS_STRICT_ENTRY_WINDOW_DAYS` (30),
  `ATLAS_STRICT_MIN_ENTRIES` (1).
- Yeni exit kodu YOK (9 mevcut).
- Türkçe uyarı.
