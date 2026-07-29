# 012 — İhtiyaç: `atlas archive --all` toplu arşivleme

## Bağlam
Görev 007 tekil arşivleme (`atlas archive <task>`) verdi. `pipeline/tasks/`
altında **çoklu** bitmiş görev birikince tek tek çağırmak sürtünmeli.
`archive_task()` idempotent değil (klasör siler); toplu iş bir kaç
komut yerine tek `atlas archive --all` ile çözülmeli.

## İhtiyaç (tek cümle)
`atlas archive --all` alt-komutu, `pipeline/tasks/` altındaki
**09-ship.md dosyası olan** her görevi sıraya alsın; varsayılan
dry-run (liste + toplam), `--apply --yes` ikili onayla gerçek toplu
arşivleme; ilk hata varsa **dur** (fail-fast) ve o ana kadar
arşivlenenleri raporla.

## Ölçülebilir Başarı
- **M1 — Alt-komut:** `atlas archive --all [--apply] [--yes]
  [--tasks-root DIR] [--archive-root DIR]`. `--all` verildiğinde
  `<task>` argümanı yok sayılır (`nargs="?"` olarak taşınır).
- **M2 — Aday seçimi:** `pipeline/tasks/*/09-ship.md` glob'u; sadece
  ship.md bulunan görevler arşive uygun sayılır. Ship yoksa
  "tamamlanmamış" → atla.
- **M3 — Dry-run çıktı:** Aday listesi (isim + tarih) + toplam sayı;
  audit yok.
- **M4 — Apply koruması:** `--apply` yalnız `--yes` ile birlikte
  gerçek işi yapar; `--yes` yoksa stderr `TOPLU ARŞİV: --yes ile
  onaylayın (çoklu yıkıcı işlem)`, exit 2 — kullanıcının çift-onaylı
  kararı.
- **M5 — Fail-fast:** İlk hata sonrası kalan görevleri işleme;
  audit son duruma yazılır (kaç başarılı, kaç kaldı, hata mesajı).
- **M6 — Rapor:** Apply sonu:
  ```
  arşivlendi: 3/5 görev
  başarılı: 003-llm-planner, 004-workflow-handlers, 005-gbrain-fts
  başarısız: 006-auto-context — <hata>
  atlanan: 007-archive-cli
  ```
- **M7 — Tek görev yolu (007) korunur:** `atlas archive <task>`
  komutu değişmez; sadece `--all` yeni yol.
- **M8 — Test:** +5 test — aday seçimi (ship.md filtresi), dry-run
  liste, --apply --yes yok exit 2, --apply --yes hepsi başarılı,
  --apply --yes ortada başarısızlık fail-fast + audit.
- **M9 — DECISIONS:** [KARAR] --yes çift-onay + fail-fast neden.

## Kapsam DIŞI
- Görev-yaşı filtresi (`--older-than N`) — YAGNI, ship.md filtresi
  yeter.
- Paralel arşivleme — tar.gz üretimi disk-yoğun, seri yeter.
- Custom summary per-task — 007 zaten görev başına summary üretiyor
  (09-ship.md ilk paragraf).
- İnteraktif onay (y/N prompt) — script'lenebilir yol yeterli.

## Kısıt
- `atlas archive <task>` mevcut yolu korunur.
- Yeni exit kodu YOK — 007 ile aynı (2 SPEC, 6 arşiv).
- Audit yalnız `--apply` yolunda yazılır.
- Türkçe rapor.
