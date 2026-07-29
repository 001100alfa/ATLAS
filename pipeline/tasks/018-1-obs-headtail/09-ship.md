# 018.1 — Ship

## Sonuç
Gözlem kırpma stratejisi **head+tail keep**: uzun stderr'ın son
satırındaki hata mesajı kaybolmaz. Env-ayarlı:
- `ATLAS_LLM_OBS_HEAD` (varsayılan 100)
- `ATLAS_LLM_OBS_TAIL` (varsayılan 100)

Uzun obs → `head + "\n[... N char atlandı ...]\n" + tail` formatı.
head+tail=0 veya toplamı obs_chars'ı aşarsa 018 davranışı (kuyruğu
at) fallback.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +_read_obs_head_tail_env,
                                            +_trim_obs; _format_prompt
                                            _trim_obs kullanır)
tests/test_planner_obs_chars.py           (edit: 018 env_ile_500 testi
                                            head+tail semantik güncellemesi;
                                            +8 test)
pipeline/tasks/018-1-obs-headtail/*.md    (5 artefakt)
```

## Sözleşme değişmezliği
- `_format_prompt` imzası korundu.
- Varsayılan davranış:
  - obs_chars=200, head=100, tail=100 → head+tail=200 = obs_chars →
    018 fallback (`obs[:200]`). Yani 018 test suite bit-uyumlu kaldı.
  - obs_chars > head+tail → gerçek head+tail keep uygulanır.
- Env kapalı = varsayılan (100/100), obs_chars>200 olduğunda etkili.

## Kalite kapıları
- pytest: **530 passed** (522 → +8)
- mypy strict + ruff: temiz

## Branch
`feat/018.1-obs-headtail` — 016.3 üstünde tek commit.

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM_OBS_HEAD` | Head karakter sayısı (varsayılan 100) |
| `ATLAS_LLM_OBS_TAIL` | Tail karakter sayısı (varsayılan 100) |

## Bekleyen
- **018.2**: LLM ile gerçek özetleme (opt-in Goal.obs_summarize;
  ekstra LLM çağrısı + cost).
