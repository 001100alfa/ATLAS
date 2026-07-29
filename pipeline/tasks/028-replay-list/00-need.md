# 028 — İhtiyaç: `atlas replay --list`

## Bağlam
027 `atlas replay <run-id>` çalışıyor ama kullanıcı hangi id'yi
replay edeceğini bilmiyor: `atlas dashboard` son run'ları gösterir
ama run_id kolonu 24 karakterle sınırlı ve YAML kopyası yoksa
(örneğin başka makineden gelmiş `.atlas/runs/`) dashboard boş çıkar.
`.atlas/runs/` klasörünü elle `ls` etmek çözüm değil.

## İhtiyaç (tek cümle)
`atlas replay --list` `.atlas/runs/*.yaml` kayıtlarını mtime azalan
sırayla listelesin: run-id, dosya zamanı, hedef metnin ilk satırı.

## Ölçülebilir Başarı
- **M1 — Listeleme:** `atlas replay --list` `.atlas/runs/*.yaml`
  dosyalarını okur; her biri için `{run_id (yaml stem), mtime
  (YYYY-MM-DD HH:MM:SS), goal (ilk `^goal:` satırı, en fazla 60
  char)}` çıkarır ve mtime desc yazar.
- **M2 — JSON:** `atlas replay --list --json` aynı verinin JSON
  listesini basar (`[{run_id, mtime, goal}, ...]`).
- **M3 — Limit:** `atlas replay --list --limit N` (varsayılan 20)
  en yeni N kaydı verir.
- **M4 — Yaml-dışı yoksay:** `.atlas/runs/`de `.txt` gibi dosya
  varsa listeye girmez.
- **M5 — Boş kayıt:** klasör yok veya boşsa `(hiç kayıt yok)` +
  exit 0 (hata değil).
- **M6 — Arg dallanması:** `atlas replay` (run-id yok, --list yok)
  → parser hatası (exit 2 SPEC HATASI).
- **M7 — Test:** +6 test (boş, iki run mtime desc, JSON, limit,
  yaml-dışı yok, arg hatası).
- **M8 — DECISIONS:** [KARAR] neden ayrı `--list` (`atlas replay list`
  alt-alt-komut yerine `--list` bayrağı, çünkü 027 sözleşmesi tek
  positional `run_id`; bayrak eklemek geriye uyumlu).

## Kapsam DIŞI
- Silme (`--rm <id>`) — YAGNI, kullanıcı `rm .atlas/runs/<id>.yaml`.
- Kopyalama / dışa aktarma — yalnız görüntüleme.
- Filtre (`--after DATE`, `--goal-contains X`) — 028'e girmiyor;
  ihtiyaç doğarsa 028.1.
- `dashboard` ile birleştirme — dashboard audit-based, replay
  file-based; iki farklı kaynak, birleştirme sözleşme bozar.

## Kısıt
- `_cmd_replay` sözleşmesi korunur; `--list` bayrağı ile dallanır.
- `run_id` positional argümanı **opsiyonel** olur (`nargs='?'`);
  `--list` yoksa ve `run_id` de yoksa açık hata (`SPEC HATASI: run-id
  ya da --list gerekli`, exit 2).
- `ATLAS_RUNS_DIR` env override 027 ile aynı davranış.
- Türkçe hata mesajı.
- Windows cp1254 uyumu — üstsimge yok, UTF-8 reconfigure zaten var.
