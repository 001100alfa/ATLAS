# 016.3 — İhtiyaç: ACP interaktif permission dialogu (opt-in)

## Bağlam
SPEC 016.2 tool tipine göre otomatik karar (read=allow_once,
write/bilinmeyen=reject). Otonom mod için doğru; ancak kullanıcı
"gerçekten ne oluyor?" görmek istediğinde manuel onay isteyebilir.
Opt-in dialog: `ATLAS_ACP_INTERACTIVE=1` env'inde stdin'den y/n
prompt sordurulsun.

## İhtiyaç (tek cümle)
`ATLAS_ACP_INTERACTIVE=1` env'inde `_acp_permission_response` tool
adını ekranda gösterip stdin'den karar sordursun; boş/hata → 016.2
auto-karara düş; kapalı env'de mevcut davranış bit-uyumlu.

## Ölçülebilir Başarı
- **M1 — Env kapalı bit-uyumlu:** `ATLAS_ACP_INTERACTIVE` set değil
  → 016.2 auto-karar (mevcut testler yeşil).
- **M2 — Env açık prompt:** açık → stderr'a
  `[acp permission] tool=<name>, options=[...]. Karar? (allow_once/
  reject) [<default>]: ` yaz; stdin'den satır oku.
- **M3 — Karar mantığı:** kullanıcı `allow_once`/`allow`/`reject`/`y`/`n`
  yazabilir. `y` = allow_once; `n` = reject; boş → default (016.2
  auto-karar).
- **M4 — Hata izolasyonu:** stdin okunamıyor (EOF, KeyboardInterrupt)
  → 016.2 auto-karar (fail-safe).
- **M5 — Test:** +4 test — env kapalı bit-uyumlu, açık y kabul,
  açık n red, boş → default.
- **M6 — DECISIONS:** [KARAR] neden opt-in; neden stderr prompt.

## Kapsam DIŞI
- GUI dialog — TTY yeter.
- Session-level "her zaman" hatırla — 016.4+.
- Timeout — kullanıcı düşünsün.

## Kısıt
- `sys.stdin.readline()` kullan; TTY tespiti YAGNI.
- Türkçe prompt metni.
- İstisna adları `*Error` sonekli.
