# 003 — SPEC: LLM planner entegrasyonu

**Sözleşme değişmezliği:** `orchestrator/core.py::{run_loop, Action,
Judge, CallBudget, LoopResult, StepKind}` ve `orchestrator/planner.py::
{Planner, make_planner, PlannerExhaustedError}` imzaları korunur.
Yeni sınıf/istisna eklenir; eskisi değiştirilmez.

## 1. Fonksiyonel Gereksinimler

- **FR1 — Backend seçimi:** `ATLAS_LLM` env değişkeni planner backend'ini
  seçer:
  - `stub` (varsayılan / env yok): mevcut davranış (`plan[stub]:noop`).
  - `claude`: `claude --print --output-format text <prompt>` subprocess.
  - `acp`, `anthropic`: `NotImplementedError("Görev 003.1'de eklenecek: "
    "backend='<name>'")` — açık mesajla düşer.
  - Bilinmeyen değer: `NotImplementedError` (aynı kalıp, kullanıcı
    farkına varsın).

- **FR2 — Claude komutu çözümlemesi:** Komut önceliği:
  1. `ATLAS_LLM_CLAUDE_BIN` env (mutlak yol) — verilmişse doğrulama:
     dosya var + `os.access(..., X_OK)`.
  2. `shutil.which("claude")` — Windows'ta `.cmd`/`.exe` uzantısı otomatik.
  3. Hiçbiri yoksa: `LLMPlannerError("claude bulunamadı: PATH'e ekleyin "
     "veya ATLAS_LLM_CLAUDE_BIN ile mutlak yolu verin")` — planner
     **fabrika anında** patlar (run_loop'a girmez), kullanıcı YAML'ı
     düzelmeden zaman kaybetmez.

- **FR3 — Subprocess güvenliği (Windows uyumlu):**
  - `shell=False` **sabit** — kabuk açılmaz.
  - `text=True, encoding="utf-8", errors="replace"` — Türkçe/emoji
    yutulmaz, kod sayfası bozulsa bile crash yok (DECISIONS 2026-07-24).
  - `timeout=int(os.environ.get("ATLAS_LLM_TIMEOUT", "60"))` — asılı
    subprocess yok. `TimeoutExpired` → `LLMPlannerError("timeout: "
    "<n>s")`; alt-process `communicate()`'in kendi kill'i yeterli.
  - `input=prompt` — prompt stdin'den geçer (arg-limit ve boşluk
    escape sorunları elenir).
  - `capture_output=True` — stdout planın metni, stderr sadece hata
    ayıklama için (loglanmaz; hata durumunda ilk 200 karakter mesaja
    eklenir).
  - `check=False` + manuel `returncode` kontrol: sıfırsa stdout,
    değilse `LLMPlannerError(f"exit={rc}: {stderr[:200]}")`.
  - Komut, tam yol bir `.cmd` shim'iyse subprocess doğrudan çalıştırır
    (Python 3.12 subprocess `.cmd` uzantısını tam yol verildiğinde
    `CreateProcessW` ile açar; CVE-2024-4030 sonrası özel escape
    devrededir).

- **FR4 — Prompt formatı (sabit, kısa):**
  ```
  Sen ATLAS'ın planlama alt-ajansısın. Görev:
  <goal.goal>

  Sözleşme: TEK SATIRLIK plan komutu üret. İzin verilen fiiller:
  <sorted(goal.action_allowlist)>. Biçim: fiil:arg1[:arg2].
  Örnek: "write:notes.txt:merhaba" veya "shell:echo ok".

  Son <=3 gözlem (varsa):
  <history son 3 OBSERVE metni; yoksa "(yok)">

  Sadece plan satırını yaz, başka açıklama YOK.
  ```
  Prompt kesinlikle kısadır (< 800 karakter); LLM istese uzatsın —
  planner cevabın **ilk satırını** alır, kalanı atar. Beyaz boşluk
  temizlenir; boşsa `LLMPlannerError("boş plan cevabı")`.

- **FR5 — LLMPlannerError sözleşmesi:** Yeni sınıf
  `LLMPlannerError(RuntimeError)`. Mesaj formatı Türkçe, ilk cümle
  kök nedeni verir. `orchestrator/planner.py` içinde tanımlı;
  `cli.py` import edip yakalar.

- **FR6 — CLI entegrasyonu:** `cli.py::_cmd_run_goal` `LLMPlannerError`
  yakalar → audit'e `("atlas-run", "llm_error", str(exc)[:200])`,
  stderr `LLM PLANNER HATASI: <exc>`, **exit 7**.

- **FR7 — Fabrika seviyesi vs. çağrı seviyesi hata:** `make_planner`
  şu şartlarda **fabrika anında** patlar (test edilebilirlik +
  erken uyarı):
  - `plan_kind=="llm"` + `ATLAS_LLM=claude` + komut bulunamadı → FR2.
  - `plan_kind=="llm"` + `ATLAS_LLM in {acp, anthropic, <unknown>}` →
    NotImplementedError.

  Çağrı-zamanı hataları (timeout, non-zero exit, boş cevap) çalışma
  sırasında `LLMPlannerError`. Sözleşme: planner closure'ı yalnızca
  bu iki hata tipini raise eder.

- **FR8 — Stub geriye uyumluluk:** `ATLAS_LLM` set edilmemişse veya
  `stub` ise davranış bit-uyumlu (`plan[stub]:noop`). Mevcut
  `test_planner.py::test_llm_bilinmeyen_backend` — `claude`
  backend'i artık NotImplementedError döndürmez → test güncellenir
  (yeni claude testleri onun yerine).

## 2. Arayüz Sözleşmeleri

```
src/atlas_core/orchestrator/planner.py                (edit)
  class LLMPlannerError(RuntimeError): ...           # yeni
  def _resolve_claude_bin() -> str: ...              # yeni, iç
  def _format_prompt(goal, history) -> str: ...      # yeni, iç
  def _call_claude(bin: str, prompt: str, timeout_s: int) -> str: ...  # yeni, iç
  def _claude_planner(goal: Goal) -> Planner: ...    # yeni, iç
  def make_planner(goal: Goal) -> Planner: ...       # edit: llm dallı

src/atlas_core/cli.py                                 (edit)
  # _cmd_run_goal içine LLMPlannerError yakalama + exit 7.

# Env değişken sözleşmesi (docs/DECISIONS 2026-07-29):
#   ATLAS_LLM                stub | claude | acp | anthropic
#   ATLAS_LLM_CLAUDE_BIN     opsiyonel, mutlak yol
#   ATLAS_LLM_TIMEOUT        opsiyonel, saniye (varsayılan 60)
```

## 3. Kabul Kriterleri

- **AC1 — Stub değişmez:** `test_planner.py::test_llm_stub_deterministik`
  aynen geçer (Görev 002'den regresyon).
- **AC2 — Claude backend fabrika:** `ATLAS_LLM=claude` +
  `ATLAS_LLM_CLAUDE_BIN=<mevcut dosya>` → `make_planner(goal)` bir
  callable döner (raise YOK).
- **AC3 — Komut yok = erken hata:** `ATLAS_LLM=claude` + bin yok +
  PATH'te claude yok → `LLMPlannerError` fabrika anında; mesaj
  "claude bulunamadı" cümlesini içerir.
- **AC4 — Happy plan çağrısı (mock):** `subprocess.run` monkeypatch'i
  fake `CompletedProcess(stdout="write:x.txt:1\n", returncode=0)`
  döner → planner("goal", []) == "write:x.txt:1"; boşluk temizlenir.
- **AC5 — Timeout (mock):** monkeypatch subprocess.run
  `TimeoutExpired` fırlatır → `LLMPlannerError("timeout" içerir)`;
  planner iki kez çağrılabilir (kalıcı bozulma yok).
- **AC6 — Non-zero exit:** returncode=1, stderr="model overload" →
  `LLMPlannerError("exit=1" ve "model overload" içerir)`.
- **AC7 — Boş cevap:** stdout="   \n\n" → `LLMPlannerError("boş plan"
  içerir)`.
- **AC8 — Çok satırlı cevap:** stdout="write:x.txt:1\naçıklama\n" →
  ilk satır alınır (`write:x.txt:1`).
- **AC9 — UTF-8 sağlamlığı:** stdout içinde Türkçe karakter (`ü, ş`) +
  emoji → hatasız `str` döner (encoding="utf-8" errors="replace"
  garanti).
- **AC10 — CLI exit 7 (in-process):** `_cmd_run_goal` mock'la
  `LLMPlannerError` alır → `main(["run","--goal-file",...])` = 7;
  stderr'de "LLM PLANNER HATASI"; audit'e `llm_error` kaydı yazılır.
- **AC11 — Bilinmeyen backend:** `ATLAS_LLM=xyz` + `plan_kind=llm` →
  `NotImplementedError("Görev 003.1")`; make_planner anında; mesaj
  backend adını içerir.
- **AC12 — Kalite kapıları:** ruff + mypy strict + pytest yeşil;
  coverage ≥ %90 (baseline %95 korunur).

## 4. Q → Kararlar

- **Q1 — Prompt niye YAML'da değil, sabit?** Küçük tutmak için
  (kapsam DIŞI). Ayrıca prompt kaçısı planner sözleşmesi dışıdır;
  ileride `Goal.llm_prompt` opsiyonel alanı eklenebilir. Şu an
  eklemezsek Goal doğrulaması bozulmaz.
- **Q2 — `claude --print` yerine ACP session neden değil?** ACP
  auth handshake + session state yönetimi bu görevin boyutunu
  ikiye katlar; kapsam dışı. Basit stdio subprocess iş görür.
- **Q3 — Timeout kalıcı mı, adaptif mi?** Env değişkeni ile
  kalıcı. `run_loop` her adımda planlarını çağırıyor, adaptif
  ölçme run_loop dışında ele alınır.
- **Q4 — Retry?** Yok. Planner sözleşmesi 1 çağrı 1 yanıt. Retry
  sözleşme değişikliğidir; farkındalıklı ertelendi (Görev 013).
- **Q5 — Neden yeni exit 7 (6 değil)?** 6 workflow-handler
  hatalarına ayrıldı (DECISIONS 2026-07-28). Karışmasın diye 7.
- **Q6 — `.cmd` shim'i sorun mu?** Python 3.12 subprocess `.cmd`
  uzantısını tam yol verildiğinde açar (CVE-2024-4030 sonrası
  escape güvenli). `shutil.which("claude")` Windows'ta `.cmd`'yi
  bulur; tam yol elimizde olduğu için ekstra `cmd /c` sarmalıyoruz.
