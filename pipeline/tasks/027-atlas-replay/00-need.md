# 027 — İhtiyaç: `atlas replay <run-id>`

## Bağlam
`atlas dashboard` son run'ları listeliyor; ancak bir run'ı yeniden
çalıştırmak için orijinal YAML dosyasını bulup elle çalıştırmak
gerekiyor. Regresyon testinde bu sıkıntı — YAML'ı bulup çağırmak
sürtünmeli.

## İhtiyaç (tek cümle)
`atlas run --goal-file X.yaml` her başarılı çağrıda YAML'ı
`.atlas/runs/<run-id>.yaml` olarak kopyalasın; `atlas replay <run-id>`
o kopyayı yükleyip yeniden çalıştırsın.

## Ölçülebilir Başarı
- **M1 — Kopya:** `_cmd_run_goal` YAML yüklendikten sonra
  `.atlas/runs/<run-id>.yaml` klasörüne kopyalanır. `run-id` env
  yoksa mevcut `run_id` (timestamp veya CLI arg) kullanılır.
- **M2 — Env override:** `ATLAS_RUNS_DIR` (varsayılan `.atlas/runs`).
- **M3 — Alt-komut:** `atlas replay <run-id>` — kopyayı bulur,
  `_cmd_run_goal` mantığını yeni bir args namespace ile çağırır.
- **M4 — Hata:** kopya yoksa `SPEC HATASI: run bulunamadı: <id>` +
  exit 2.
- **M5 — Dashboard entegrasyonu:** dashboard tablosuna `run_id`
  kolonu ekle (kısaltılmış ilk 8 char) — kullanıcı hangi id'yi
  replay edeceğini görsün.
- **M6 — Test:** +5 test — kopya oluşur, replay eş görev çalıştırır,
  yoksa exit 2, dashboard run_id gösterir, ATLAS_RUNS_DIR override.
- **M7 — DECISIONS:** [KARAR] neden yaml kopyası; run-id şeması.

## Kapsam DIŞI
- Aynı sandbox durumunu geri yükleme — YAGNI (kullanıcı tmpfs'i
  temizler).
- LLM cost yeniden hesabı (deterministik değil zaten).
- Replay içinde environment snapshot — env değişebilir.

## Kısıt
- `_cmd_run_goal` sözleşmesi korunur.
- `atlas run --goal-file X --run-id ID` mevcut arg akışı korunur.
- Türkçe hata mesajı.
