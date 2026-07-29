# 018 — Ship

## Sonuç
`_format_prompt` gözlem başına karakter üst sınırı artık env-ayarlı:
- **`ATLAS_LLM_OBS_CHARS`** (varsayılan 200, aralık [1, 2000]).
- Parse hatası / aralık dışı → varsayılan 200 (fail-safe).
- Her `_format_prompt` çağrısında runtime okunur — env değişikliği
  hemen etkili.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +_DEFAULT_OBS_CHARS
                                            + _MAX_OBS_CHARS sabitleri;
                                            +_read_obs_chars_env yardımcı;
                                            _format_prompt runtime kullanım)
tests/test_planner_obs_chars.py           (yeni, 9 test)
pipeline/tasks/018-obs-chars-env/*.md     (5 artefakt)
```

## Sözleşme değişmezliği
- `_format_prompt` imzası korundu.
- Varsayılan davranış (env yok → 200) **bit-uyumlu** — mevcut testler
  yeşil.
- Yeni exception YOK.

## Kalite kapıları
- pytest: **469 passed** (460 → +9)
- mypy strict + ruff: temiz

## Branch
`feat/018-obs-chars-env` — 016.1 üstünde tek commit.

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM_OBS_CHARS` | Gözlem başına karakter üst sınırı (varsayılan 200, aralık [1, 2000]) |

## Bekleyen
- 018.1: LLM ile gözlem özetleme (uzunca stderr → 3 satır özet).
