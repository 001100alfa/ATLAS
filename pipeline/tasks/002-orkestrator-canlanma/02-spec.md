# 002 — SPEC: Orkestratörün Canlanması

**Durum:** TASLAK — onay bekliyor (`spec-ok`).
**Sözleşme değişmezliği:** `src/atlas_core/orchestrator/core.py` içindeki
`run_loop`, `Action`, `Judge`, `CallBudget`, `LoopResult` **değişmez**.
Bu SPEC yalnızca o sözleşmeyi karşılayan **somut** planner/action/judge
üreticileri ile YAML tabanlı hedef yükleyici tanımlar.

---

## 1. Fonksiyonel Gereksinimler

- **FR1 — Hedef dosyası:** `atlas run --goal-file <path.yaml>` bir YAML
  hedef dosyası okur. Alanlar:
  ```yaml
  goal: "merhaba dünya dosyasına yaz"
  plan_kind: static            # static | llm
  plan_steps:                  # plan_kind=static için zorunlu
    - "write:hello.txt:merhaba"
  action_allowlist: [write, shell]   # {read, write, shell} alt kümesi
  shell_allow_regex: "^(echo|type|dir) "   # shell içindeyse zorunlu
  judge_kind: file_exists      # file_exists | regex_in_last_observe | exit_zero
  judge_arg: "hello.txt"
  budget: 50.0
  max_steps: 5
  ```
  Geriye uyumluluk: `atlas run "<hedef metni>"` eski konumsal argüman
  **korunur**; hedef dosyası verilmezse mevcut echo demo çalışır
  (regresyon yok). `--goal-file` verildiğinde konumsal argüman yok sayılır.

- **FR2 — Plan tipleri:**
  - `static`: `plan_steps` listesi sırayla döndürülür; liste bitince
    `PlannerExhausted` atar (judge yine de değerlendirilir).
  - `llm`: Bu görev kapsamında **stub**. `ATLAS_LLM=stub` (varsayılan)
    ise deterministik olarak `"noop"` planı döndürür ve audit'e
    `plan_source=stub` etiketi düşer. Gerçek LLM çağrısı Görev 003.
    (Q1 kararı: **stub ile başla.**)

- **FR3 — Action izin listesi:** İzinli fiiller `{read, write, shell}`
  alt kümesi. Plan formatı `fiil:arg1:arg2` (iki nokta ile ayrılır).
  - `read:<path>` → dosya içeriğini gözlem olarak döndürür.
  - `write:<path>:<content>` → sandbox dizinine dosya yazar.
  - `shell:<command>` → allowlist regex'ine uymak zorunda.
  - **İzin dışı fiil** veya **allowlist dışı komut** → action `ActionDenied`
    atar; `run_loop` bunu yakalayıp `observe="denied: <sebep>"` olarak
    kaydeder ve audit'e `action="denied"` yazılır (döngü kırılır, exit 5).

- **FR4 — Shell allowlist:** `shell_allow_regex` **goal dosyasında**
  tanımlanır (Q2 kararı: **goal dosyasında** — her hedefin izin sınırı
  kendi içinde). Regex `re.fullmatch` ile uygulanır. Regex yoksa ve
  action_allowlist içinde `shell` varsa → `SpecError` (yükleme zamanı).

- **FR5 — Judge tipleri:**
  - `file_exists`: `<sandbox>/<judge_arg>` var mı?
  - `regex_in_last_observe`: son `OBSERVE` kaydında `judge_arg` regex'i
    (`re.search`) eşleşiyor mu?
  - `exit_zero`: son shell action'ın exit kodu 0 mı?

- **FR6 — Audit:** Her plan/observe/denied/done kaydı mevcut
  `AuditLog.record()` üzerinden geçer. Yeni action tipi eklenmez;
  `detail` alanı prefix'lerle ayrıştırılır (`plan[stub]:`,
  `plan[static]:`, `denied:...`, `observe:...`). Koşu bitiminde
  `audit.verify()` **çağrılır** ve sonuç stdout'a yazılır.

- **FR7 — Sandbox:** Tüm dosya yazma/okuma/shell işleri
  `.atlas/sandbox/<goal-id>/` altına hapsedilir (Q3 kararı:
  **`.atlas/sandbox/`** — audit ile birlikte inspect edilebilsin).
  `<goal-id>` = goal dosyasının stem'i + kısa timestamp
  (`hello-20260728-1345`). `..` veya mutlak yol içeren path → `ActionDenied`.

- **FR8 — Bütçe:** Mevcut `CallBudget` sözleşmesi kullanılır. Her action
  varsayılan maliyet: `read`=1, `write`=2, `shell`=5. Değişiklik goal
  dosyasında `costs:` ile geçersiz kılınabilir.

- **FR9 — Çıkış kodları:** `0` başarı, `3` bütçe aşımı (mevcut),
  `4` max_steps aşımı (mevcut), **`5` action_denied (yeni)**,
  `2` spec/YAML hatası (yeni).

---

## 2. Arayüz (CLI)

```
atlas run [--goal-file PATH] [--budget FLOAT] [--max-steps INT] [GOAL]
```
- `--goal-file PATH`: YAML hedef dosyası. Verilirse `GOAL` ve diğer
  bayraklar YAML'dan gelenle **override edilir** (YAML kazanır).
- `--goal-file` yoksa: mevcut echo demo (regresyon).

Yeni alt komut YOK — mevcut `atlas run` sözleşmesi genişletildi.

---

## 3. Kabul Kriterleri (test edilebilir)

- **AC1 — Happy path:** `tests/goals/hello.yaml` (plan_kind=static,
  write action → file_exists judge) tek koşuda `done=True`, exit 0.
  Audit'te ≥5 kayıt. `audit.verify()` True. Dosya sandbox'ta mevcut.
- **AC2 — İzin ihlali (fiil):** goal dosyası `action_allowlist: [read]`
  iken plan `write:...` içerirse: exit 5, audit'te `action="denied"`,
  dosya oluşturulmamış.
- **AC3 — İzin ihlali (shell):** `shell_allow_regex: "^echo "` iken
  plan `shell:rm -rf .` ise: exit 5, audit'te `denied`, sandbox
  dokunulmamış (test fikstür kontrolü).
- **AC4 — Path kaçışı:** plan `write:../escape.txt:x` → exit 5,
  sandbox dışına yazılmamış (test fikstürü sandbox parent'ını mtime ile
  kontrol eder).
- **AC5 — Bütçe:** budget=3, plan iki `write` çağırır → 2. adımda
  BudgetExceededError, exit 3, audit'te 2 tam tur + `max_steps` yok.
- **AC6 — LLM stub:** plan_kind=llm, `ATLAS_LLM=stub` (varsayılan) →
  plan `"noop"` döner, judge `file_exists` "yok" der, `max_steps`
  sonunda exit 4. Audit'te `plan[stub]:` prefix'i.
- **AC7 — Regresyon:** `atlas run "eski hedef"` (goal-file YOK) →
  eski echo demo davranışı; `test_platform.py`'daki mevcut testler
  aynen geçer.
- **AC8 — audit-verify:** AC1 koşusu sonrası `atlas audit-verify`
  exit 0.

---

## 4. Fonksiyonel-Olmayan Gereksinimler

- **NF1 — Tip:** yeni dosyalar mypy `--strict` geçer.
- **NF2 — Lint:** ruff (mevcut kurallar) temiz.
- **NF3 — Coverage:** yeni dosyalar için ≥ %90; toplam kapsam düşmez.
- **NF4 — Windows:** Sandbox path'leri `pathlib.PurePosixPath` ile
  normalize edilir; `\` ve `/` karışımı kabul, çıktı UTF-8 (mevcut
  reconfigure kalıbı).
- **NF5 — Determinism:** `static` planner + stub LLM sabit
  seed'sizdir; testler zamana bağlı değildir (`<goal-id>` timestamp'i
  test için `--run-id` bayrağıyla override edilebilir).

---

## 5. Arayüz Sözleşmeleri (yeni modüller — sadece imza, kod DEĞİL)

```
src/atlas_core/orchestrator/goals.py
  @dataclass Goal:
      goal: str
      plan_kind: Literal["static","llm"]
      plan_steps: list[str]
      action_allowlist: frozenset[str]
      shell_allow_regex: re.Pattern | None
      judge_kind: Literal["file_exists","regex_in_last_observe","exit_zero"]
      judge_arg: str
      budget: float
      max_steps: int
      costs: dict[str, float]
  def load_goal(path: Path) -> Goal
  class SpecError(ValueError)

src/atlas_core/orchestrator/actions.py
  def make_action(goal: Goal, sandbox: Path) -> Action
  class ActionDenied(RuntimeError)

src/atlas_core/orchestrator/planner.py
  def make_planner(goal: Goal) -> Callable[[str,list],str]
  class PlannerExhausted(RuntimeError)

src/atlas_core/orchestrator/judges.py
  def make_judge(goal: Goal, sandbox: Path, last_exit: dict[str,int]) -> Judge
```

---

## 6. Açık Sorulara Verilen Kararlar (özet — onayına)

- **Q1 → stub.** LLM planner ilk sürümde deterministik stub; gerçek
  `claude` CLI entegrasyonu Görev 003. Gerekçe: LLM entegrasyonu
  Windows'ta stdin/UTF-8 tuzağı barındırıyor (DECISIONS.md 2026-07-24);
  tek görevde iki büyük risk tutulmaz.
- **Q2 → goal dosyasında allowlist.** Her hedefin izin sınırı kendi
  YAML'ında; global pyproject bağımlılığı yok. Gerekçe: farklı hedef
  farklı komut ister; global liste ya çok gevşek ya çok sıkı olur.
- **Q3 → `.atlas/sandbox/`.** Sandbox kökü `.atlas/` altında (audit ile
  aynı yer); tempdir DEĞİL. Gerekçe: koşu sonrası post-mortem için
  dosyalar duruyor olmalı; `.gitignore` zaten `.atlas/`'ı hariç
  tutuyor.

---

## 7. Riskler ve Azaltmalar

| Risk | Olasılık | Etki | Azaltma |
|---|---|---|---|
| Sandbox kaçışı (symlink, `..`, mutlak yol) | Orta | Yüksek | `Path.resolve().is_relative_to(sandbox.resolve())` kontrolü + testte fikstür |
| YAML parse hatası kullanıcıyı çarpar | Orta | Düşük | `SpecError` + net mesaj + exit 2 |
| Mevcut echo demo regresyonu | Düşük | Orta | `--goal-file` yoksa eski kod yolu; `test_platform.py` regresyon leg |
| Windows path ayırıcı karışıklığı | Orta | Orta | POSIX normalize + Windows CI leg zorunlu |
| Audit zinciri koşu ortasında bozulursa | Düşük | Yüksek | Aşama 0 yedeği; end-to-end test `verify()` çağırır |

---

## 8. Onay

- [ ] SPEC okundu.
- [ ] Q1/Q2/Q3 kararları kabul.
- [ ] AC1–AC8 kabul kriterleri onaylandı.
- [ ] Kapsam DIŞI listesi (LLM entegrasyonu, workflow handler, FTS)
      bu görev için tutulacak.

**Onay komutu:** `spec-ok` → Aşama 2 (PLAN) başlar.
**Revizyon:** `spec-değiştir: <ne>` → SPEC güncellenir, tekrar sunulur.
