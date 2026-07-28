# 004 — SPEC: WorkflowEngine handler kaydı & gerçek yürütme

**Durum:** TASLAK — sözleşme dokunulmazlığı: `WorkflowEngine.register()`,
`run()`, `StepResult`, `WorkflowError` **değişmez**.

## 1. Fonksiyonel Gereksinimler

- **FR1 — CLI:** `atlas workflow run <yaml> [--dry-run]` komutu eklenir.
  - `--dry-run`: handler'lar no-op çalışır (yan etki yok); sadece
    hangi handler hangi argümanla çağrılacaktı, onu raporlar.
  - `<yaml>` yolu geçersizse exit 2, `SpecError` mesajı.
- **FR2 — Handler kayıt fabrikası:** `atlas_core.workflows.handlers`
  paketi altında `register_builtins(engine)` fonksiyonu — CLI onu
  çağırır. Yeni handler ekleyen kişi burayı düzenler.
- **FR3 — Handler `pipeline.gate`:** parametre `file: <path>`. Verilen
  yol mevcutsa handler `f"gate GEÇTİ: {path}"` döner; yoksa
  `HandlerError` atar (mesajda beklenen yol).
- **FR4 — Handler `pipeline.test`:** parametre `paths: [<path>...]`
  (varsayılan `[tests]`). `uv run pytest -q <paths>` subprocess'i
  çalışır; exit 0 → `"pytest OK ({n} test)"`, exit ≠ 0 → `HandlerError`
  (stdout'un son 500 karakteri).
  - `--dry-run` durumunda subprocess çağrılmaz; komut satırı raporlanır.
  - Timeout 300s; aşarsa `HandlerError("pytest timeout")`.
- **FR5 — Handler `memory.archive`:** parametre `task: <name>` (örn.
  `002-orkestrator-canlanma`). `archive_task()` çağrılır:
  `pipeline/tasks/<task>` → `archive/` altına tar.gz + vault düğümü.
  - `--dry-run` durumunda gerçek arşivleme yapılmaz; hedef yol raporlanır.
  - `summary:` opsiyonel; verilmezse `f"{task} arşivlendi"` kullanılır.
- **FR6 — Hata semantiği:** herhangi bir `HandlerError` → workflow
  durur, audit'e `workflow_error` kaydı düşülür, exit 6.
- **FR7 — Audit:** her handler başarısı `AuditLog.record("workflow",
  <step_name>, output[:200])` (motor zaten yapıyor); başarısızlıkta
  `record("workflow", "error", <hata mesajı>)`.
- **FR8 — Exit kodları:** `0` başarı, `2` YAML/spec hatası, `6` handler
  başarısız / bilinmeyen handler.

## 2. Arayüz Sözleşmeleri (imza — kod DEĞİL)

```
src/atlas_core/workflows/handlers/__init__.py
  def register_builtins(engine: WorkflowEngine) -> None

src/atlas_core/workflows/handlers/gate.py
  def make_gate_handler() -> Handler
  class HandlerError(RuntimeError)

src/atlas_core/workflows/handlers/test.py
  def make_test_handler(dry_run: bool = False) -> Handler

src/atlas_core/workflows/handlers/archive.py
  def make_archive_handler(dry_run: bool = False) -> Handler
```

`Handler = Callable[[dict[str, object]], str]` — mevcut engine.py sözleşmesi.

## 3. Kabul Kriterleri

- **AC1 — Happy path:** `tests/workflows/mini.yaml` (3 adım: gate → test →
  archive[dry_run]) tek koşuda exit 0; audit'te 3 kayıt.
- **AC2 — Bilinmeyen handler:** yaml'da `uses: bogus.step` → exit 6,
  `WorkflowError` mesajı, audit'te error kaydı.
- **AC3 — Gate başarısız:** `file: yok.md` → exit 6, sonraki adımlar
  çalışmadı (audit'te 1 error kaydı, hiçbir başarı kaydı).
- **AC4 — pytest handler dry-run:** `--dry-run` → subprocess çağrılmaz;
  çıktıda `[dry-run]` prefix'i, gerçek pytest yok.
- **AC5 — archive handler dry-run:** `pipeline/tasks/<x>` dokunulmaz.
- **AC6 — CLI regresyon:** mevcut `atlas run`, `atlas recall`, `atlas
  context`, `atlas scan`, `atlas audit-verify` etkilenmez.
- **AC7 — Audit zinciri:** koşu sonrası `atlas audit-verify` exit 0.
- **AC8 — Coverage:** yeni dosyalar ≥ %90; toplam ≥ %90.

## 4. Q → Kararlar

- **Q1 — Handler paketi mi tek dosya mı?** → **Paket** (`handlers/`
  klasörü). Her handler kendi dosyasında, testi de ayrı. Yeni handler
  eklemek düşük sürtünme.
- **Q2 — pytest subprocess `uv run` mu direkt `python -m pytest` mi?**
  → **`sys.executable -m pytest`**. `uv` bağımlılığını handler'a
  taşımayız; taşınabilir bundle'da bile çalışır.
- **Q3 — `archive_task` `pipeline/tasks/<x>` dizinini SİLİYOR** (mevcut
  davranış: `shutil.rmtree`). Dry-run olmadan çalıştırırsak canlı görev
  klasörü kaybolur. → Handler varsayılan **`dry_run=True`**; gerçek
  arşivleme için YAML'da `with: {dry_run: false}` istenir.
