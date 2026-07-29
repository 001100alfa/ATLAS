# 018.2 — Ship

## Sonuç
- **Goal alanı:** `Goal.obs_summarize: bool = False` (opt-in). Eski
  YAML'lar davranış değiştirmez (bit-uyumlu).
- **Env override:** `ATLAS_LLM_OBS_SUMMARIZE` (`1`/`true`/`yes`/`on`
  case-insensitive) tüm goal'ler için aktif.
- **Effective flag:** `goal.obs_summarize OR env`. Herhangi biri true
  ise özet yolu.
- **Hook mekanizması:** `_maybe_summarize_or_trim(obs, obs_chars,
  goal)` — dispatch. Kısa obs (`len <= obs_chars`) hep no-op —
  ekstra maliyet yok.
- **Stub özet (deterministik):** `_stub_summarize_obs(obs) →
  "[özet: N char, L satır, baş: '...']"`. Aynı input → aynı output.
  Stub backend + claude/acp fallback + LLM olmayan test yolu.
- **Real özet (anthropic):** `_summarize_via_anthropic(obs, goal)`
  mevcut `_call_anthropic`'i minimal bir prompt ile çağırır:
  `"Türkçe TEK cümlede, en fazla 120 karakterde özetle..."`.
  Yan etki: metrics.jsonl'a ekstra satır (mevcut yol) — extra token
  görünür ve fatura edilir.
- **Claude/ACP:** real çağrı **YAPMAZ** — bir kez `stderr`'e "018.3
  kapsamı" uyarısı basar ve stub'a düşer. Deduplication set ile
  spam engelli.
- **Fail-safe:** Anthropic çağrısı `LLMPlannerError` fırlatırsa
  → stderr uyarı + `_trim_obs` fallback. Planner turu ölmez.
- **Prompt entegrasyonu:** `_format_prompt` `_trim_obs` yerine
  `_maybe_summarize_or_trim` çağırıyor; sözleşme değişmedi (yalnız
  içerik farklılaşabilir opt-in ile).

## Dosyalar
```
src/atlas_core/orchestrator/goals.py      (edit: +Goal.obs_summarize,
                                            +load_goal validation)
src/atlas_core/orchestrator/planner.py    (edit: +_read_env_flag,
                                            +_effective_obs_summarize,
                                            +_stub_summarize_obs,
                                            +_summarize_via_anthropic,
                                            +_maybe_summarize_or_trim,
                                            +_reset_obs_summarize_warnings
                                              (test helper);
                                            _format_prompt dispatch)
tests/test_planner_obs_summarize.py       (yeni, +17 test)
pipeline/tasks/018-2-obs-summarize/*.md   (2 artefakt)
```

## Sözleşme değişmezliği
- `Planner`, `make_planner`, `LLMPlannerError`, `RetryAfterError`,
  `_call_anthropic`, `_trim_obs`, `_format_prompt` imzaları
  KORUNDU (`_format_prompt` içi değişti ama sözleşme aynı).
- `Goal` dataclass yeni alan eklendi (opsiyonel, default False) —
  keyword-arg ile geriye uyumlu; positional tehlikesi yok (`Goal`
  frozen slots + `load_goal` her alanı named).
- `_write_metric_for_data` yan etkisi mevcut yol; extra özet çağrısı
  ayrı bir metrik satırı olur (kural: her API çağrısı = bir satır).

## Kalite kapıları
- pytest: **574 passed** (557 → +17)
- coverage: %91.47 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/018.2-llm-obs-summarize` — main üstünde tek commit.

## Env sözleşmesi (yeni ★)
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM_OBS_SUMMARIZE` ★ | **018.2** — `1`/`true`/`yes`/`on` iken tüm goal'ler için özet yolu (goal.obs_summarize ile OR) |

## Backend matrisi
| Backend | Opt-in kapalı | Opt-in açık + kısa obs | Opt-in açık + uzun obs |
|---|---|---|---|
| stub | 018.1 trim | dokunma | stub özet |
| claude | 018.1 trim | dokunma | stub özet + uyarı (bir kez) |
| anthropic | 018.1 trim | dokunma | **real çağrı**; hata → trim fallback |
| acp | 018.1 trim | dokunma | stub özet + uyarı (bir kez) |

## Kullanım örneği
```yaml
# goal.yaml
goal: build başarısız, düzelt
plan_kind: llm
plan_steps: []
action_allowlist: [shell, read]
shell_allow_regex: "^(pytest|ruff|mypy).*"
judge_kind: exit_zero
judge_arg: ""
budget: 500
max_steps: 12
obs_summarize: true       # 018.2: uzun test log'unu özetlet
llm_prompt: "..."
```

```bash
$ ATLAS_LLM=anthropic atlas run --goal-file goal.yaml
# 500 satırlık pytest log'u LLM'e "tek cümlede özetle" ile gönderilir,
# özet plan prompt'una gömülür. Metrics.jsonl'a hem plan hem özet
# çağrısı iki satır olarak yazılır.
```
