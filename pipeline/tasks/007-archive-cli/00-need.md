# 007 — İhtiyaç: `atlas archive` CLI komutu

## Bağlam
`memory.archive.archive_task()` (Görev 004 ile eklendi) ve
`workflows.handlers.archive.make_archive_handler` (aynı görev) mevcut,
ancak **doğrudan CLI erişimi yok**. Kullanıcı bir görevi arşivlemek
için ya YAML workflow yazmak zorunda ya da Python REPL'e girmek zorunda.
Bu sürtünme "pipeline/tasks şişmesin" doktriniyle çelişiyor —
CLAUDE.md'de belirtilmiş olmasına rağmen (`Arşiv: biten görev
archive_task() ile taşınır — pipeline/tasks şişmez.`) günlük kullanımda
komut yok. Sonuç: pipeline/tasks'te 6 tamamlanmış görev (002, 003, 004,
005, 006, 003.1, 003.2) klasörü birikmiş durumda.

## İhtiyaç (tek cümle)
`atlas archive <task>` CLI komutu ile kullanıcı tek satırda tamamlanmış
bir görevi tar.gz'e alıp, özet notu vault'a yazıp, `pipeline/tasks/<task>`
klasörünü kaldırabilsin (varsayılan **dry-run** — yıkıcı işlem asla
istem-dışı tetiklenmesin).

## Ölçülebilir Başarı
- **M1 — Komut var:** `atlas archive --help` alt-komutu listeler;
  yardım metni Türkçe.
- **M2 — Dry-run varsayılan:** `atlas archive 003-llm-planner` sadece
  planlanan işlemi rapor eder; dosya yok, klasör silinmez, vault
  değişmez. Çıktı: `[dry-run] taşınacak: pipeline/tasks/003-llm-planner
  → archive/003-llm-planner-<tarih>.tar.gz`.
- **M3 — Gerçek arşivleme:** `atlas archive 003-llm-planner --apply`
  ile tar.gz oluşur, vault'a `tasks/task-003-llm-planner.md` notu
  yazılır, klasör silinir.
- **M4 — Özet:** `--summary "<metin>"` opsiyonel; verilmezse mevcut
  09-ship.md dosyasının ilk paragrafı okunur (yoksa
  `"<task> arşivlendi"`).
- **M5 — Hata dallanması:**
  - Görev klasörü yok → `SPEC HATASI: görev klasörü yok: ...` + exit 2.
  - `--apply` yıkıcı; klasör yoksa aynı hata + exit 2.
  - archive_task() içi hata (disk dolu, izin) → `ARŞİV HATASI: ...` +
    exit 6 (workflow-handler kalıbıyla aynı — mevcut).
- **M6 — Audit:** Her `--apply` çağrısı denetime yazılır:
  `("atlas-archive", "archive", "<task>")` — hash zincirine düşer.
- **M7 — Test kapsamı:** 6-8 test (dry-run, apply, ship.md okuma,
  hata dallanması, audit); coverage ≥ %90.
- **M8 — Flaky düzeltme kapsam DIŞI** (adım 7'de ayrı — SPEC 003.2
  DECISIONS'da beyan edilmiş "Görev 007 son adımı").

## Kapsam DIŞI
- Toplu arşivleme (`atlas archive --all`) — tek görev yeter; toplu
  iş için workflow YAML zaten var.
- Görev-öncesi/-sonrası hook'lar (git commit, PR açma).
- Vault'ta arşiv listesi görüntüleyici (`atlas archive list`) — YAGNI.
- Arşiv üzerinden geri yükleme (`atlas restore`) — Görev 013+.

## Kısıt
- `cli.py` mevcut komut sözleşmeleri (`context`, `remember`, `recall`,
  `run`, `reindex`, `workflow`, `audit-verify`, `scan`) korunur.
- Yeni exit kodu yok; **6** (handler/arşiv hataları) yeniden kullanılır.
- Türkçe hata/çıktı mesajları.
- stdlib-only.
