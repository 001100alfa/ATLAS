# 026 — Ship

## Sonuç
Sandbox shell subprocess'i sertleştirildi — Docker YOK, portable
stdlib-only iyileştirme:

- **Env scrub**: whitelist (PATH, HOME/USERPROFILE, TEMP, LANG,
  SYSTEMROOT, ...) — `ANTHROPIC_API_KEY`, `ATLAS_LLM_PRICE_*` gibi
  hassas env'ler sandbox'a **sızmaz**.
- **PATH override**: `ATLAS_SANDBOX_PATH` env verilirse subprocess
  PATH'i o olur.
- **Timeout env**: `ATLAS_SANDBOX_TIMEOUT` (varsayılan 10.0 sn);
  parse hatası → varsayılan.
- **stderr birleşik**: observation `exit=N out=<...> err=<...>`
  — stderr ilk 200 char görünür.

## Dosyalar
```
src/atlas_core/orchestrator/actions.py    (edit: +os import,
                                            +_SANDBOX_ENV_WHITELIST,
                                            +_scrub_env,
                                            +_read_sandbox_timeout;
                                            _shell env=/timeout/stderr uygular)
tests/test_actions.py                     (+6 test — API key sızmaz,
                                            PATH scrub, PATH override,
                                            timeout env okuma, stderr obs,
                                            whitelist)
pipeline/tasks/026-sandbox-hardening/*.md (5 artefakt)
```

## Sözleşme değişmezliği
- `make_action` imzası korundu.
- Mevcut testler bit-uyumlu (env yok senaryosunda davranış aynı).
- `Goal`, `Action`, `ActionDeniedError` — dokunulmadı.

## Kalite kapıları
- pytest: **539 passed** (533 → +6)
- mypy strict + ruff: temiz
- `atlas scan src`: sır bulunamadı

## Branch
`feat/026-sandbox-hardening` — 025 üstünde tek commit.

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_SANDBOX_PATH` | Sandbox subprocess PATH override (varsayılan mevcut PATH) |
| `ATLAS_SANDBOX_TIMEOUT` | Sandbox subprocess timeout sn (varsayılan 10.0) |

## Bekleyen
- **026.1**: Unix `resource` limits (RLIMIT_CPU, RLIMIT_AS) — opt-in.
- **026.2**: Windows Job Objects — opt-in.
- **026.3**: Network isolation (block outbound) — Linux capabilities.

## Notlar (Docker YOK gerekçesi)
Kullanıcı direktifi Docker yasağı; portable stdlib-only sertleştirme
çoğu tehdit modelini kapsar:
- **API key sızıntısı** → env whitelist (bu görev)
- **Sandbox path escape** → mevcut `_jail` + `Path.resolve()`
- **Runtime aşımı** → timeout env
- **shell injection** → `shell=False` + `shlex.split` + `shell_allow_regex`
- **Fork bomb / OOM** → 026.1 opt-in (Unix resource)
