# 002 — PLAN: Orkestratörün Canlanması

**Girdi:** `02-spec.md` (onaylı — 3 karar Q1/Q2/Q3 kabul, AC1–AC8 kilitli).
**Çıktı:** Aşama 3+ için WBS, her adımın gate'i, rollback, test matrisi.

---

## 1. WBS (İş Kırılımı) — 6 Alt-Adım

Her adım kendi commit'ini alır (küçük, atomik, geri alınabilir).
Gate düşerse **aynı adımda** kalırız; 3 ardışık başarısızlıkta durup rapor.

| # | Adım | Üretilen Dosyalar | Gate (geçmeden ilerleme yok) | Risk |
|---|---|---|---|---|
| 3.1 | `goals.py` + YAML yükleyici | `src/atlas_core/orchestrator/goals.py`, `tests/test_goals.py`, `tests/goals/hello.yaml`, `tests/goals/denied_verb.yaml`, `tests/goals/denied_shell.yaml`, `tests/goals/escape.yaml`, `tests/goals/budget.yaml`, `tests/goals/llm_stub.yaml` | `pytest tests/test_goals.py -q` yeşil + `mypy src/atlas_core/orchestrator/goals.py` temiz | Düşük |
| 3.2 | `actions.py` + sandbox jail | `src/atlas_core/orchestrator/actions.py`, `tests/test_actions.py` | pytest yeşil; path-escape / shell-deny / verb-deny testleri geçer | **Yüksek** (sandbox kaçış) |
| 3.3 | `planner.py` (static + stub) | `src/atlas_core/orchestrator/planner.py`, `tests/test_planner.py` | pytest yeşil; `PlannerExhausted` doğru yerde atar | Düşük |
| 3.4 | `judges.py` (3 tip) | `src/atlas_core/orchestrator/judges.py`, `tests/test_judges.py` | pytest yeşil; her judge tipi için pozitif+negatif senaryo | Düşük |
| 3.5 | `cli.py` entegrasyonu (`_cmd_run` genişletme) + regresyon | `src/atlas_core/cli.py` (edit), `tests/test_cli.py` (genişlet) | `test_platform.py` ve `test_cli.py` regresyonsuz geçer; `--goal-file` yolu çalışır | Orta (regresyon) |
| 3.6 | End-to-end + audit doğrulama | `tests/test_run_end_to_end.py` | AC1–AC8 tümü yeşil; `atlas audit-verify` exit 0; ruff + mypy strict + coverage ≥ %90 | Orta |

**Aşama 6 (öz-denetim)** = ruff + mypy `src` + `uv run pytest --cov=atlas_core --cov=sections --cov-fail-under=90`.
**Aşama 7 (ship)** = `06-test-report.md` + `09-ship.md` + DECISIONS.md'ye [KARAR] satırı + commit.

---

## 2. Adım-Adım Detay

### 3.1 — `goals.py` + YAML yükleyici
- `Goal` dataclass (frozen, slots) — SPEC §5 imzası.
- `load_goal(path: Path) -> Goal`: PyYAML `safe_load`, alan doğrulaması,
  eksik/yanlış → `SpecError` (mesaj + alan adı).
- Path/regex normalize: `shell_allow_regex` derlenmiş `re.Pattern` olarak
  saklanır (yükleme zamanı hata verir, koşuda değil).
- Fikstür YAML'ları `tests/goals/` altında; test bunları okuyup `Goal`
  üretir, alan-bazlı assert eder.
- **Gate:** 6 fikstür yükleniyor + 4 negatif senaryo (eksik alan, yanlış
  enum, shell allowlist eksik, geçersiz regex) `SpecError` atıyor.

### 3.2 — `actions.py` + sandbox jail
- `make_action(goal, sandbox) -> Action` closure döndürür (mevcut
  `Action = Callable[[str], tuple[str,float]]` sözleşmesi).
- Plan parse: `fiil:arg1[:arg2]` → tuple; tanınmayan fiil → `ActionDenied`.
- Path jail helper: `_jail(sandbox, user_path) -> Path`
  - `Path(user_path)` mutlak ise → deny.
  - `(sandbox / user_path).resolve().is_relative_to(sandbox.resolve())`
    False ise → deny.
  - Symlink var mı kontrol; varsa deny (Windows'ta symlink genelde yok
    ama Linux CI için).
- Shell: `subprocess.run(shlex.split(cmd), cwd=sandbox, capture_output=True,
  timeout=10, shell=False)`. `shell=False` **sabit** (kabuk açma yok).
  Exit kodu `last_exit["shell"]` sözlüğüne yazılır (judge okuyacak).
- Windows shell: allowlist içinde `echo|type|dir` gibi builtin varsa
  `cmd.exe /c` üzerinden çağır? **HAYIR** — `shell=False` sabit.
  Onun yerine fikstürler platform-nötr komut kullanır (`python -c "..."`).
- Cost tablosu goal'dan gelir; yoksa varsayılan `{read:1, write:2, shell:5}`.
- **Gate:** 8 test — happy path (read/write/shell), 4 deny senaryosu
  (verb, shell-regex, path-escape, absolute-path), timeout, kod yolu
  Windows'ta da geçer (CI Windows leg).

### 3.3 — `planner.py`
- `make_planner(goal) -> plan_fn` closure.
- `static`: dahili sayaç; her çağrıda `plan_steps[i]` döner; taşınca
  `PlannerExhausted`.
- `llm` + `ATLAS_LLM=stub` (varsayılan): sabit `"noop"` döner + audit
  detail prefix'i `plan[stub]:`.
- `llm` + `ATLAS_LLM=claude` gibi bilinmeyen → `NotImplementedError`
  (Görev 003'e park).
- **Gate:** 4 test — static ilerleme, static exhaust, stub deterministik,
  bilinmeyen backend hata.

### 3.4 — `judges.py`
- `make_judge(goal, sandbox, last_exit) -> judge_fn`.
- `file_exists`: `(sandbox / goal.judge_arg).exists()`.
- `regex_in_last_observe`: history'de son `OBSERVE` kaydını bul,
  `re.search(goal.judge_arg, text)`.
- `exit_zero`: `last_exit.get("shell") == 0`.
- **Gate:** 6 test — her tip × (pozitif, negatif).

### 3.5 — `cli.py` entegrasyonu
- `_cmd_run` başında: `if args.goal_file: <yeni yol> else: <mevcut echo>`.
- Yeni yol:
  1. `goal = load_goal(Path(args.goal_file))` — hata → exit 2.
  2. `sandbox = _sandbox_root() / f"{goal_id}"` (goal_id = stem + `-{run_id or timestamp}`).
  3. `plan = make_planner(goal); act = make_action(goal, sandbox); judge = make_judge(...)`.
  4. `run_loop(...)` çağır; `ActionDenied` yakala → exit 5, audit'e
     "denied" yaz.
  5. Çıktı: mevcut format + `sandbox=<path>` satırı.
- Yeni argparse: `--goal-file PATH`, `--run-id STR` (test için).
- **Gate:** `test_cli.py` mevcut testleri geçer + yeni `--goal-file`
  testi eklenir; `test_platform.py` dokunulmadan geçer.

### 3.6 — End-to-end + kapsam
- `tests/test_run_end_to_end.py`: AC1–AC8'i doğrudan koşar
  (`subprocess.run([sys.executable, "-m", "atlas_core.cli", "run",
  "--goal-file", ...])`) → exit kodu + audit dosyası + sandbox içeriği
  assert.
- Fikstürler tmp_path'e kopyalanır; `ATLAS_AUDIT` ve sandbox root
  monkeypatch'lenir (gerçek `.atlas/audit.jsonl` bozulmaz).
- **Gate:** 8 AC yeşil; `ruff check`, `mypy src`, `pytest --cov` ≥ %90.

---

## 3. Risk Tablosu (SPEC §7'nin genişletilmiş hali)

| # | Risk | O | E | Erken Uyarı | Azaltma | Fallback |
|---|---|---|---|---|---|---|
| R1 | Sandbox kaçışı (symlink/`..`/absolute) | O | Y | test-3.2 kırmızı | `Path.resolve() + is_relative_to`; symlink reddi; 4 negatif test | Adım 3.2'de kal, kod-inceleme + ek test |
| R2 | Windows'ta subprocess/UTF-8 tuzağı | O | O | Windows CI leg kırmızı | `shell=False` + platform-nötr fikstür (`python -c`); mevcut `stdout.reconfigure` kalıbı | Fikstür komutunu değiştir, testi izole et |
| R3 | Mevcut echo demo regresyonu | D | O | `test_platform.py` kırmızı | `--goal-file` yoksa eski yol; entegrasyondan önce regresyon koş | 3.5'i geri al, dallanmayı en üstte yap |
| R4 | YAML alan hataları kullanıcıya sızar | O | D | AC olmayan crash | `SpecError` + alan adı; exit 2; 4 negatif test | Mesaj iyileştir |
| R5 | Coverage %90 altına düşer | O | D | 3.6 gate kırmızı | Küçük dosyalar + kenar durum testleri; ölü kod yok | Test ekle, ölü branch kaldır |
| R6 | `subprocess.timeout` Windows'ta farklı davranır | D | O | test flaky | Timeout=10s cömert; `TimeoutExpired` → `ActionDenied("timeout")` | Timeout artır, testi mark.slow |
| R7 | Audit zinciri koşu sırasında yarım kalır | D | Y | `audit-verify` False | AuditLog append-only zaten atomik; koşu öncesi yedek (aşama 0) | Yedekten geri al, testi izole ATLAS_AUDIT ile koş |

---

## 4. Rollback Planı

Her adım sonunda atomik commit:
```
git add -A && git commit -m "feat(002/3.<N>): <özet>"
```
Bir gate düşerse **önce** düzelt; düzelmiyorsa:
```
git reset --hard HEAD~1          # son adımı geri al
```
Aşama 3.5 (CLI entegrasyonu) özel: regresyon olursa `_cmd_run`'ı adım
adım geri sar, `--goal-file` yolunu ayrı fonksiyona (`_cmd_run_goal`)
taşıyıp mevcut `_cmd_run`'ı dokunulmadan bırak.

Audit dosyası:
- Aşama 0'da yedek YOK (henüz audit.jsonl mevcut değildi — teyit
  edildi: `.atlas/` altında sadece `doctor/` ve `portable/` var).
- Yeni koşularda `.atlas/audit.jsonl` **testler için** monkeypatch'lenir;
  gerçek dosya sadece manuel `atlas run` ile yazılır.

**Yıkıcı işlem = onay iste** kuralı geçerli. `git reset --hard` sana
sorulmadan çalıştırılmaz.

---

## 5. Test Matrisi (özet)

| Test dosyası | Test sayısı (hedef) | Kapsadığı FR/AC |
|---|---|---|
| `test_goals.py` | 10 | FR1, FR4, NF1 |
| `test_actions.py` | 8 | FR3, FR4, FR7, AC2, AC3, AC4 |
| `test_planner.py` | 4 | FR2, AC6 |
| `test_judges.py` | 6 | FR5 |
| `test_cli.py` (genişletme) | +3 | FR1, FR9, AC7 |
| `test_run_end_to_end.py` | 8 | AC1–AC8 |
| **TOPLAM YENİ** | **~39** | tümü |

Regresyon (dokunulmayacak): `test_platform.py`, `test_core.py`,
`test_portable.py`, `test_doctor_*`, `test_juggler_*`, `test_make_portable`,
`test_setup_gui`.

---

## 6. Tahmini Efor & Sıra

Sıralı, tek oturumda biter (Adım-3.2 en uzun):

- 3.1: ~45 dk (dataclass + YAML + 10 test)
- 3.2: ~90 dk (sandbox jail dikkatli, Windows farkı)
- 3.3: ~30 dk
- 3.4: ~30 dk
- 3.5: ~45 dk (CLI + regresyon)
- 3.6: ~60 dk (E2E + coverage + ruff/mypy)
- Aşama 7 (ship): ~15 dk

**Toplam:** ~5 saat aktif iş. Bekleme yok, harici bağımlılık yok
(LLM entegrasyonu Görev 003).

---

## 7. Onay

- [ ] WBS 6 alt-adım kabul.
- [ ] Gate'ler ve rollback kabul.
- [ ] Test matrisi (~39 yeni test) kabul.
- [ ] Yıkıcı işlem onay kuralı korunacak.

**Onay komutu:** `plan-ok` → Aşama 3.1 (kod yazımı) başlar.
**Revizyon:** `plan-değiştir: <ne>`.
