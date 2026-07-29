# 007 — SPEC: `atlas archive` CLI komutu

## 1. Fonksiyonel Gereksinimler
- **FR1 — Alt-komut:** `atlas archive <task> [--apply] [--summary TEXT]
  [--tasks-root DIR] [--archive-root DIR]`.
  - `<task>`: `pipeline/tasks/<task>` altındaki klasörün adı.
  - `--apply`: yıkıcı işlemi çalıştır (varsayılan **dry-run**).
  - `--summary`: vault notunun gövdesi; verilmezse 09-ship.md'nin ilk
    50 satırı okunur (yoksa `"<task> arşivlendi"`).
  - `--tasks-root` (varsayılan `pipeline/tasks`) ve `--archive-root`
    (varsayılan `archive`) — test için override.

- **FR2 — Dry-run çıktı sözleşmesi:**
  ```
  [dry-run] arşivleme planı:
    kaynak: pipeline/tasks/003-llm-planner
    hedef:  archive/003-llm-planner-YYYY-MM-DD.tar.gz
    vault:  vault/tasks/task-003-llm-planner.md
  Uygulamak için: atlas archive 003-llm-planner --apply
  ```

- **FR3 — Apply çıktı sözleşmesi (başarılı):**
  ```
  arşivlendi: archive/003-llm-planner-YYYY-MM-DD.tar.gz
  vault:      vault/tasks/task-003-llm-planner.md
  kaldırıldı: pipeline/tasks/003-llm-planner
  ```

- **FR4 — Hata dallanması:**
  - Klasör yok (dry-run VE apply) → stderr `SPEC HATASI: görev klasörü
    yok: <path>`, exit **2**.
  - `archive_task` içi `OSError` / `tarfile` hatası → stderr
    `ARŞİV HATASI: <mesaj>`, exit **6**, audit kaydı hata ile.
  - Vault yazma hatası (izin) → aynı yol (`OSError` genellikle burada
    yakalanır).

- **FR5 — Audit sözleşmesi:** `--apply` başarılı → `AuditLog.record(
  "atlas-archive", "archive", "<task>")`. Hata → `"error", str(exc)[:200]`.
  Dry-run → audit **yok** (yıkıcı değil).

- **FR6 — Özet okuma:** Öncelik:
  1. `--summary` argümanı.
  2. `pipeline/tasks/<task>/09-ship.md` — ilk 50 satır (H1'den sonrası
     dahil, boş satırla ilk paragraf kesilir).
  3. Fallback: `"<task> arşivlendi"`.

## 2. Arayüz Sözleşmeleri
```
src/atlas_core/cli.py                        (edit)
  # yeni: _cmd_archive(args) -> int
  # yeni: _read_ship_summary(task_dir) -> str
  # sub.add_parser("archive", ...) — add_argument * 4
  # LLMPlannerError yakalama yok (ilgisiz).

tests/test_cli_direct.py                     (edit: +6 test)
  # AC1..AC7 kapsamı.

pipeline/tasks/007-archive-cli/*.md          (5 artefakt)
```

## 3. Kabul Kriterleri
- **AC1 — Dry-run hazırlanır:** `--apply` yok → çıktıda `[dry-run]`,
  hedef dosya oluşmaz, klasör durur.
- **AC2 — Apply çalışır:** tmp_path'te sahte görev klasörü + `--apply`
  → `archive/<task>-<tarih>.tar.gz` var, klasör silinir.
- **AC3 — Klasör yok:** exit 2 + "görev klasörü yok" stderr.
- **AC4 — Ship.md özeti okunur:** `--summary` yok + 09-ship.md var →
  vault notunda ship.md'nin ilk paragrafı geçer.
- **AC5 — Summary override:** `--summary "el ile"` → vault notunda
  "el ile" geçer, ship.md yok sayılır.
- **AC6 — Fallback özet:** ship.md yok + `--summary` yok → `"<task>
  arşivlendi"` metni notta.
- **AC7 — Audit yazılır:** `--apply` sonrası audit dosyasında
  `"atlas-archive"` + `"archive"` + task adı geçer.
- **AC8 — Kalite kapıları:** ruff + mypy + pytest yeşil; coverage ≥ %90.

## 4. Q → Kararlar
- **Q1 — Neden yeni exit kodu değil (6 tekrar)?** Handler ile aynı
  semantik (arşiv işi kırıldı) — kullanıcı iki koddan seçim yapmasın.
- **Q2 — Neden yıkıcı işlem dry-run varsayılan?** CLAUDE.md kuralı:
  "Yıkıcı işlem öncesi MUTLAKA onay iste". `--apply` bilinçli seçim.
- **Q3 — Neden 09-ship.md?** SHIP aşaması bir görevin sözleşmesi
  gereği yazılmış olur (pipeline gate); özet için doğal kaynak.
- **Q4 — Neden `atlas archive` yerine `atlas task archive`?** Tek
  alt-komut daha kısa; ileride `atlas task list` gerekirse yeniden
  isim değişebilir (sözleşme henüz basit).
