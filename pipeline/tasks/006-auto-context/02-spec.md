# 006 — SPEC: Otomatik context injection

**Sözleşme değişmezliği:** `run_loop`, `Planner`, `make_planner` imzaları
korunur. `GBrain.context_for/recall/remember` imzaları korunur.
Yeni: opsiyonel `context` argümanı LLM planner fabrikasına, opsiyonel
`Goal.inject_context` alanı.

## 1. Fonksiyonel Gereksinimler

- **FR1 — Context çağrısı yeri:** `cli.py::_cmd_run_goal` içinde,
  `make_planner(goal)` çağrısından **önce**:
  ```python
  ctx: str | None = None
  if _context_enabled(goal):
      brain = GBrain(_vault_root())
      ctx = brain.context_for(goal.goal, limit=goal.context_limit)
  plan = make_planner(goal, context=ctx)
  ```
  Böylece context TEK KEZ hesaplanır (loop içinde değil).

- **FR2 — `_context_enabled` sözleşmesi:**
  1. `os.environ.get("ATLAS_CONTEXT", "on") == "off"` → `False`
  2. `goal.inject_context is False` → `False`
  3. `goal.plan_kind == "static"` → `False` (static görevler için gerek yok)
  4. Aksi hâlde `True`.

- **FR3 — `Goal` genişlemesi (opsiyonel alanlar):**
  ```
  inject_context: bool = True         # varsayılan: aç
  context_limit:  int  = 5            # recall limiti
  ```
  YAML'da yoksa default kullanılır; eski YAML'lar SpecError almaz.
  Doğrulama: `inject_context` bool; `context_limit` pozitif int (≤50).

- **FR4 — `make_planner(goal, context=None)`:** İmza genişler —
  ikinci pozisyonel/isimli argüman opsiyonel, default `None`. Static
  planner context'i **yok sayar** (M2). LLM stub planner da yok sayar.
  Sadece `claude` backend'i (ve gelecekteki gerçek LLM backend'leri)
  context'i prompt'a ekler.

- **FR5 — Prompt biçimi (context varken):** Mevcut sabit prompt
  başına (görev satırından hemen sonra) bloğu ekler:
  ```
  Sen ATLAS'ın planlama alt-ajansısın. Görev:
  <goal.goal>

  Önceden bilinen bağlam (GBrain):
  <context, empty ise "(bağlam yok)">

  Sözleşme: ... (mevcut)
  ```
  Context boş string veya None ise blok hiç eklenmez (M3). Mevcut
  prompt formatı (SPEC 003 FR4) bit-uyumlu korunur — sadece 4 satırlık
  ekleme, atlanabilir.

- **FR6 — Hata izolasyonu:** GBrain hatası (vault yok, index bozuk,
  disk hatası) **görevi kırmasın**. Try/except ile yakalanır, stderr'e
  `UYARI: GBrain context alınamadı: <exc>` yazılır, `ctx=None` ile
  devam edilir. Ajan yine de çalışır.

- **FR7 — Static görev regresyonu:** `_context_enabled(goal)` static
  için False dönüyor, `make_planner` static dalı `context` parametresini
  görmüyor. Sonuç: static görevler için `GBrain` **hiç instantiate
  edilmez** — Görev 005 index dosyası açılmaz, disk maliyeti sıfır.

- **FR8 — CLI görünürlüğü:** Context enjekte edildiğinde stdout'a bir
  başlık satırı: `Bağlam: <N> not enjekte edildi` — kullanıcı ne olduğunu
  görsün. Boşsa `Bağlam: yok`. Kapalıysa `Bağlam: (kapalı)` — üç
  durum ayrılabilir.

## 2. Arayüz Sözleşmeleri

```
src/atlas_core/orchestrator/planner.py            (edit)
  def make_planner(goal: Goal, context: str | None = None) -> Planner:
      # static / stub: context yok sayılır
      # claude: closure'a bind → prompt'a eklenir
  # _format_prompt yardımcısı `context: str | None` alır.

src/atlas_core/orchestrator/goals.py              (edit)
  @dataclass Goal:
      # ...mevcut alanlar...
      inject_context: bool = True                 # yeni, opsiyonel
      context_limit: int = 5                      # yeni, opsiyonel
  # load_goal doğrulaması: bool/int + range.

src/atlas_core/cli.py                             (edit)
  # _cmd_run_goal içinde make_planner öncesi context hesaplama.
  # _context_enabled(goal) yardımcısı iç fonksiyon.

# Env:
#   ATLAS_CONTEXT=on|off        varsayılan on (context enjekte edilir)
```

## 3. Kabul Kriterleri

- **AC1 — LLM+injection prompt'ta çıkar:** `plan_kind=llm`,
  `ATLAS_LLM=claude`, vault'ta ilgili not var → mock subprocess'in
  `input=` argümanı hem `Görev:` hem `Önceden bilinen bağlam (GBrain):`
  hem de not adını (`[[...]]`) içerir.
- **AC2 — Context boşsa "(bağlam yok)" yazılır:** vault boş →
  prompt'ta `## GBrain bağlamı:` yok, ama `Önceden bilinen bağlam
  (GBrain):\n(bağlam yok)` bloğu var. Planner çalışır.
- **AC3 — Static planner regresyonu:** `plan_kind=static` görev — GBrain
  hiç import edilmez (patch ile `context_for` asla çağrılmamalı).
- **AC4 — Stub backend regresyonu:** `plan_kind=llm` + `ATLAS_LLM=stub`
  → context hesaplansa bile stub planner `plan[stub]:noop` döner
  (context'i yok sayar).
- **AC5 — `ATLAS_CONTEXT=off` env:** llm+claude görev bile olsa
  `_context_enabled` False → GBrain çağrısı yok, prompt'ta bağlam
  bloğu yok.
- **AC6 — `Goal.inject_context: false` YAML:** aynı davranış (AC5),
  ama env yerine YAML.
- **AC7 — GBrain hata izolasyonu:** GBrain instantiation'ı raise
  ederse (monkeypatch) — görev exit 7 değil, context'siz devam
  (sadece stderr uyarı).
- **AC8 — Goal doğrulama:** `inject_context: "kırık"` (bool değil) →
  SpecError. `context_limit: -1` → SpecError. `context_limit: 51` →
  SpecError (üst sınır). Eski YAML alansız → default kullanılır.
- **AC9 — CLI görünürlük:** stdout'ta `Bağlam:` satırı bulunur;
  `on` / `off` / `(kapalı)` üç durum ayırt edilir.
- **AC10 — Kalite:** ruff + mypy strict + coverage ≥ %90.

## 4. Q → Kararlar

- **Q1 — Context her turda mı, tek kez mi?** Tek kez (görev başında).
  Turlar arası vault değişimi nadir; her tur çağırmak FTS bile olsa
  gereksiz. Prompt sabit context ile devam eder.
- **Q2 — Neden `make_planner`'a bind, `Planner`'ı değiştirmek değil?**
  `Planner` sözleşme değişmezi (`(goal, history) -> str`). Context'i
  imzaya eklemek her çağrı yerini kırar. Closure'a bind = zarif.
- **Q3 — `Goal.inject_context` neden `True` default?** CLAUDE.md
  "her göreve başlarken context_for çağrılır" diyor. Default açık;
  kapatma opt-out. Env de opt-out imkânı verir.
- **Q4 — Neden `context_limit ≤ 50`?** FTS için ölçü değil, prompt
  büyümesine karşı sağlık kontrolü. Kullanıcı elle daha büyük isterse
  spec revize edilebilir.
- **Q5 — Static planner'a niye hiç context vermeyelim?** Static plan
  sabit; context'i kullanmıyor. Bu enerji tasarrufu + isolation.
  `plan_kind=llm` + `ATLAS_LLM=stub`'da context enjekte hesaplanır
  ama kullanılmaz — testte belgeliyoruz.
