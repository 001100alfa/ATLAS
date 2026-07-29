# 006 — Ship

## Sonuç
CLAUDE.md'nin "her göreve başlarken context_for(konu) çağrılır" satırı
`atlas run --goal-file` altında **otomatik** çalışıyor:
- `_context_enabled(goal)` True ise GBrain.context_for **tek kez** hesaplanır.
- Context LLM claude planner'ının prompt'una görev satırından hemen sonra bir
  "Önceden bilinen bağlam (GBrain):" bloğu olarak eklenir.
- Static görevler ve `ATLAS_CONTEXT=off` için GBrain **hiç instantiate edilmez**
  (disk/CPU maliyeti sıfır).
- GBrain hatası (disk dolu, index bozuk) görevi kırmaz — stderr uyarı + devam.
- Kullanıcı görünürlüğü: stdout `Bağlam: N not enjekte edildi` / `yok` / `(kapalı)`.

## Dosyalar
```
src/atlas_core/orchestrator/goals.py    (edit: Goal +2 opsiyonel alan + doğrulama)
src/atlas_core/orchestrator/planner.py  (edit: make_planner context kwarg, _format_prompt context bloğu, _MAX_CONTEXT_CHARS=4000 emniyeti)
src/atlas_core/cli.py                   (edit: _context_enabled + _compute_context + _cmd_run_goal başında hesaplama & başlık)
tests/test_goals.py                     (edit: +5 test)
tests/test_planner_llm.py               (edit: +6 test)
tests/test_cli_direct.py                (edit: +6 test)
pipeline/tasks/006-auto-context/*.md    (5 artefakt)
```

## Sözleşme değişmezliği
- `run_loop`, `Action`, `Judge`, `CallBudget`, `LoopResult`, `StepKind` **korundu**.
- `Planner = Callable[[str, list[tuple[StepKind, str]]], str]` **korundu**.
- `make_planner` imzası **genişledi** — yeni pozisyonel/kwarg `context: str | None = None`,
  mevcut çağrılar aynen çalışır (default None).
- `Goal` alanları **genişledi** — yeni iki alan default'lu (`inject_context=True`,
  `context_limit=5`); mevcut YAML'lar aynı yüklenir.
- `GBrain.recall/remember/context_for` imzaları **korundu**.

## Env & YAML sözleşmesi
| Kaynak | Alan | Değer | Anlam |
|---|---|---|---|
| env | `ATLAS_CONTEXT` | `on` (varsayılan) \| `off` | Küresel context enjeksiyonu kapatma |
| YAML | `inject_context` | bool (varsayılan True) | Görev bazında opt-out |
| YAML | `context_limit` | int 1..50 (varsayılan 5) | recall limiti |

Öncelik: env `off` → global kapalı; yoksa `Goal.inject_context`; yoksa
`plan_kind==static` → kapalı; aksi hâlde açık.

## Kalite kapıları
- pytest: **319/319 passed**
- coverage: **%94.85** (eşik %90)
- mypy strict: temiz
- ruff: temiz

## Branch
`feat/006-auto-context` — tek commit, `feat/003-llm-planner` üstünde.

## Bekleyen (kapsam DIŞI)
- Context'in Judge / Action'a enjekte edilmesi — ileri görev
- Token budget (context uzunluk kırpma stratejileri) — Görev 011
- Semantic search / embedding — Görev 010+
