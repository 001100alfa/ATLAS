# 008 — SPEC: LLM retry/backoff sarmalayıcısı

## 1. Fonksiyonel Gereksinimler

### FR1 — `make_retrying_planner` fabrikası
`orchestrator/planner.py` içine yeni public fonksiyon:
```
def make_retrying_planner(
    inner: Planner,
    retries: int,
    backoff_s: float,
) -> Planner
```
- `retries <= 0` → sarmadan `inner` döner (kimlik-geçiş, no-op).
- `retries > 0` → yeni closure; her plan çağrısında en fazla
  `1 + retries` deneme.
- Denemeler arası uyku: `backoff_s * (2 ** attempt)` (attempt = 0..retries-1).
  Yani `backoff=1, retries=3` → 1s, 2s, 4s.

### FR2 — Hata seçiciliği
- **Sadece `LLMPlannerError`** yakalanır ve retry'e neden olur.
- `PlannerExhaustedError` (static planner), `KeyboardInterrupt`,
  `SystemExit`, diğer istisnalar **hemen** raise (sarma).

### FR3 — Son deneme
Tüm `1 + retries` deneme başarısızsa **son yakalanan istisna** yeniden
raise edilir. `raise ... from last_exc` KULLANILMAZ (aynı istisnadır).
Chain: her retry `logging`e/stderr'a yazılabilir ama exception
zincirinde saklanmaz.

### FR4 — Trace
`ATLAS_LLM_TRACE=1` env'inde her başarısız deneme (son dahil) stderr'a:
```
[retry] deneme <n>/<total> başarısız: <exc mesajı ilk 200 karakter>
```
Kapalı varsayılan.

### FR5 — Env okuma yardımcısı
```
def _read_retry_env() -> tuple[int, float]:
    retries = int(os.environ.get("ATLAS_LLM_RETRIES", "0"))
    backoff = float(os.environ.get("ATLAS_LLM_BACKOFF", "1.0"))
    return max(0, retries), max(0.0, backoff)
```
Negatif değerler sessizce 0'a düşürülür (kullanıcı yanlış env → bug
yerine kapalı).

### FR6 — CLI entegrasyonu
`cli.py::_cmd_run_goal`:
```python
inner = make_planner(goal, context=context)
retries, backoff = _read_retry_env()
planner = make_retrying_planner(inner, retries, backoff)
```
Bu satır, `LLMPlannerError` yakalama noktasını değiştirmez — sarmalayıcı
zaten aynı istisnayı raise ediyor.

### FR7 — `time.sleep` yerine `_sleep_hook`
Test için `planner._sleep = time.sleep` modül seviyesi bağlanır;
`make_retrying_planner` `planner_mod._sleep(...)` çağırır. Test
monkeypatch ile kontrol eder.

## 2. Arayüz Sözleşmeleri
```
src/atlas_core/orchestrator/planner.py    (edit)
  _sleep = time.sleep                       # yeni (test hook)
  def make_retrying_planner(inner, retries, backoff_s) -> Planner
  def _read_retry_env() -> tuple[int, float]

src/atlas_core/cli.py                     (edit: _cmd_run_goal)
  # inner = make_planner(...); planner = make_retrying_planner(inner, *_read_retry_env())

tests/test_planner_retry.py               (yeni, ~10 test)
tests/test_cli_direct.py                  (edit: +1 test — retry env + LLM hata → 3 deneme)
pipeline/tasks/008-retry-backoff/*.md     (5 artefakt)
```

## 3. Kabul Kriterleri

- **AC1 — retries=0 kimlik:** `make_retrying_planner(inner, 0, 1.0) is inner`.
- **AC2 — retries=1 başarılı 2. denemede:** inner counter; 1. çağrı
  `LLMPlannerError` fırlatır, 2. çağrı `"write:x"` döner → sarmalayıcı
  `"write:x"` döner; 2 çağrı yapıldı.
- **AC3 — retries=3 hepsi başarısız:** 4 çağrı yapıldı; son `LLMPlannerError`
  raise (mesajı 4. çağrının hatasıdır).
- **AC4 — Backoff geometrik:** monkeypatch `_sleep` çağrılarını kaydeder;
  retries=3, backoff=1.0 → sleep argümanları `[1.0, 2.0, 4.0]`.
- **AC5 — Backoff=0 sleep atlanır:** backoff=0 → sleep hiç çağrılmaz
  (test hızlı).
- **AC6 — PlannerExhausted geçer:** static planner sarılırsa
  `PlannerExhaustedError` retry'e girmez, hemen raise.
- **AC7 — KeyboardInterrupt geçer:** simüle edilen `KeyboardInterrupt`
  sarmalayıcıdan direkt geçer.
- **AC8 — Trace stderr:** `ATLAS_LLM_TRACE=1` + retries=2 tüm hata →
  stderr'de 3 satır (`deneme 1/3`, `deneme 2/3`, `deneme 3/3`).
- **AC9 — Trace kapalı:** `ATLAS_LLM_TRACE` yok → stderr temiz.
- **AC10 — Env okuma:** `_read_retry_env()` `ATLAS_LLM_RETRIES=-5`
  → `(0, ...)`; `ATLAS_LLM_BACKOFF=abc` → `ValueError` normal (kullanıcı
  fark eder).
- **AC11 — CLI entegrasyonu:** `test_cli_direct.py` env retries=2 +
  fake failing planner → 3 subprocess çağrısı, sonunda exit 7.
- **AC12 — Kalite kapıları:** ruff + mypy strict + pytest yeşil;
  coverage ≥ %90.

## 4. Q → Kararlar
- **Q1 — Neden `make_planner` içine gömülmedi?** Sözleşme kirlenmesin;
  `make_retrying_planner` opsiyonel kompozisyon. Test yalıtımı da kolay.
- **Q2 — Neden jitter yok?** Görev 013'te. Deterministik backoff test
  edilebilir ve yeterli.
- **Q3 — Neden `time.sleep` hook'u?** Test 4s uykuyu geçemez; monkeypatch
  şart. `planner_mod._sleep` global hook en basit yol.
- **Q4 — Neden `retry-after` header'ı okumak yok?** 011 kapsamında
  (Anthropic response header'ları).
