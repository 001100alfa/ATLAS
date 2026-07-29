# 026 — İhtiyaç: Sandbox iyileştirme (Docker YOK)

## Bağlam
`orchestrator/actions.py` zaten güçlü sandbox içerir: mutlak yol reddi,
`Path.resolve().is_relative_to(sandbox)`, symlink reddi, `shell=False`,
`shlex.split`, 10s sabit timeout, `shell_allow_regex`. Ancak:

- Shell subprocess'e verilen env = `os.environ` **tümü** — kullanıcının
  shell'inde ne varsa (API key'ler dahil) sandbox komutuna sızabilir.
- Timeout sabit — env-ayarlı değil.
- stderr yakalanmıyor, yalnız stdout.

Docker/container kullanmadan portable şekilde bu üç eksikliği kapatmak.

## İhtiyaç (tek cümle)
Shell action subprocess'ine **whitelist env** ver (PATH, HOME/USERPROFILE,
TEMP, LANG, SYSTEMROOT), timeout env-ayarlı yap, stdout+stderr birleşik
yakala.

## Ölçülebilir Başarı
- **M1 — Env scrub:** `_scrub_env()` yalnızca whitelist değişkenleri
  geçirir. `ANTHROPIC_API_KEY`, `ATLAS_LLM_PRICE_IN` gibi ATLAS/LLM
  env'ler sandbox subprocess'e ulaşmaz.
- **M2 — PATH kısıt:** `ATLAS_SANDBOX_PATH` env verilirse subprocess
  PATH'i o olur; yoksa mevcut PATH geçer (default fallback — env yok
  senaryosuna gölge düşürmez).
- **M3 — Timeout env:** `ATLAS_SANDBOX_TIMEOUT` (varsayılan 10.0 sn);
  parse hatası → 10.0.
- **M4 — stdout+stderr birleşik:** `capture_output=True` (mevcut) +
  observation'a stderr ilk 200 char eklenir (`err=<...>`).
- **M5 — Bit-uyumlu davranış:** env yoksa mevcut testler yeşil kalır.
- **M6 — Test:** +5 test — env scrub API key sızmaz, PATH kısıt aktif,
  timeout env okuma, stderr observation'da, sandbox dışı yazma reddi
  (mevcut).
- **M7 — DECISIONS:** [KARAR] neden whitelist; neden Docker DIŞI.

## Kapsam DIŞI
- Docker/container — YASAK (kullanıcı direktifi).
- Linux capability drop (`prctl`) — platform-özel, portable değil.
- Unix `resource` limits (RLIMIT_CPU, RLIMIT_AS) — 026.1 opt-in.
- Windows Job Objects — 026.2 opt-in.
- Network namespace — YAGNI.

## Kısıt
- `make_action` sözleşmesi korunur (Callable[[str], tuple[str, float]]).
- stdlib-only.
- Türkçe hata mesajı.
