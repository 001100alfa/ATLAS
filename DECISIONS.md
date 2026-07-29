# ATLAS Karar Günlüğü
Format: `## TARİH` altında madde; her madde [KARAR]/[VARSAYIM]/[HATA] etiketi taşır.

## 2026-07-29 (Görev 003.1 — anthropic + acp LLM backend'leri)
- [KARAR] `anthropic` backend'i **stdlib-only** kaldı: `urllib.request`
  ile doğrudan HTTPS POST. `requests`/`httpx` bağımlılığı eklenmedi;
  test tarafında `urlopen` monkeypatch aynı ergonomiyi verir. `x-api-key`
  ve `anthropic-version` header sözleşmesi Anthropic Messages API v1
  ile birebir; response `content[].type=="text"` toplanır ve ilk satır
  alınır (claude subprocess kalıbıyla simetrik).
- [KARAR] API key sızıntı savunması: `ANTHROPIC_API_KEY` hiçbir kod
  yolunda stderr / audit / log'a yazılmaz. Yalnız request header'ında
  yaşar. `test_key_asla_hata_mesajina_gecmez` bunu doğruluyor (URLError
  fırlatıldığında bile mesajda anahtar geçmez).
- [KARAR] `acp` backend'i **ACP-lite** — text-only + oturum-per-plan.
  Tam protokol (tool-use, streaming, permissions) Görev 010+; şu an
  yalnız `initialize` + `session/new` + `session/prompt` yeter.
  Kalıcı bağlantı yok — planner sözleşmesi durumsuz kalıyor
  (`Callable[[str, list], str]` değişmez).
- [KARAR] ACP subprocess yaşam döngüsü: her plan çağrısı için yeni
  `Popen`; `finally` bloğunda stdin.close → wait(2s) → hâlâ ayaktaysa
  kill → wait(2s). **Süreç sızıntısı yasak.** `test_teardown_wait_takilirsa_kill`
  wait TimeoutExpired atınca kill'in tetiklendiğini doğruluyor.
- [KARAR] Windows subprocess deadlock savunması: `bufsize=1` (hat-tamponlu)
  + `text=True` + `encoding="utf-8"` + `errors="replace"` + monotonic
  deadline'lı `readline`. Aynı DECISIONS 2026-07-24 kalıbı (subprocess
  UTF-8) burada da devrede.
- [KARAR] `_format_prompt` yardımcısı üç backend (claude, anthropic,
  acp) tarafından paylaşıldı → Görev 006 context injection tek noktada
  bakılır; iki backend'e otomatik geçti (AC11 + AC20).
- [KARAR] CLI dokunulmadı: her iki backend `LLMPlannerError` fırlatır
  ve `_cmd_run_goal` mevcut yakalama noktası (Görev 003) exit 7 döner.
  Sözleşme kırılmadan iki yeni backend geldi.
- [KARAR] `NotImplementedError` mesajı güncellendi: `"desteklenen: stub,
  claude, anthropic, acp"`. Bilinmeyen backend testi (`test_llm_bilinmeyen_backend`)
  mesajın her dört adı da içerdiğini doğrular — regresyon lehçesi.
- Kapsam: 1 modül düzenleme (planner.py 199→~430 sat), 3 yeni test
  dosyası (35 test), 1 CLI test genişleme (+2 test), 1 YAML fixture.
  Toplam 354 test yeşil + 1 bilinen flaky (test_doctor_gui — Görev 007
  son adımı düzeltiyor). Coverage %93.52 (eşik %90). mypy strict + ruff
  temiz. Artefaktlar `pipeline/tasks/003-1-llm-backends/`.

## 2026-07-29 (Görev 006 — Otomatik context injection)
- [KARAR] `cli.py::_cmd_run_goal` başında **tek kez** GBrain.context_for
  çağrılır ve `make_planner`'a `context=` kwarg ile bind edilir. Loop
  içinde tekrar edilmez — turlar arası vault değişimi nadir, FTS bile
  olsa gereksiz çağrı istenmez.
- [KARAR] `_context_enabled(goal)` üçlü kapıdan geçer: env `ATLAS_CONTEXT=off`
  → False; `goal.inject_context` False → False; `plan_kind=="static"` →
  False. Aksi hâlde True. Static görevler için GBrain **hiç instantiate
  edilmez** (disk/CPU maliyeti sıfır) — Görev 005 index'i açılmaz.
- [KARAR] `Planner` sözleşmesi (`(goal, history) -> str`) korundu.
  Context'i imzaya eklemek her çağrı yerini kırar; onun yerine
  `make_planner(goal, context=None)` — closure'a bind. Static ve stub
  backend'ler context'i yok sayar (M2, AC3-AC4).
- [KARAR] Yeni `Goal` alanları **opsiyonel default'lu**: `inject_context:
  bool=True`, `context_limit: int=5` (üst sınır 50). Doğrulama'da
  `bool int'in alt sınıfıdır` özel kontrolü — `context_limit: true`
  yakalanıyor. Eski YAML'lar hiç değişmeden yükleniyor.
- [KARAR] Prompt'a context bloğu görev satırından **hemen sonra** eklenir
  ("Önceden bilinen bağlam (GBrain):"). Boş / None → blok yok. Üst sınır
  `_MAX_CONTEXT_CHARS=4000` — prompt şişmesin (Görev 011 token budget
  gelene kadar emniyet).
- [KARAR] GBrain hata izolasyonu (FR6): try/except `Exception` +
  stderr uyarı, ctx=None, görev devam. Ajan diski dolsa bile çalışır.
  `# noqa: BLE001` bilerek — bu tek yer geniş yakalama gerektiriyor.
- [KARAR] Kullanıcı görünürlüğü: stdout başlığı üç durum ayırır:
  `Bağlam: N not enjekte edildi` (etkin+dolu) / `Bağlam: yok` (etkin+boş) /
  `Bağlam: (kapalı)` (env/YAML/static). Sessiz enjeksiyon yasak.
- Kapsam: 3 modül düzenleme, 3 test dosyası genişleme (17 yeni test),
  toplam 319 test yeşil, coverage %94.85, mypy strict + ruff temiz.
  Artefaktlar `pipeline/tasks/006-auto-context/`.

## 2026-07-29 (Görev 003 — LLM planner entegrasyonu)
- [KARAR] `orchestrator/planner.py` LLM backend'i **subprocess-based** ve
  **`claude --print`** ile başlar. `ATLAS_LLM=claude` verildiğinde her tur
  `_call_claude` çalışır; `shell=False`, `text=True`, `encoding="utf-8"`,
  `errors="replace"`, `input=prompt` (stdin), `capture_output=True`,
  `timeout=env(ATLAS_LLM_TIMEOUT, 60)`. Kalıp DECISIONS 2026-07-24'ün
  ("subprocess+UTF-8 tuzağı") ilk uygulaması.
- [KARAR] `make_planner` **fail-fast**: `plan_kind=llm` + `ATLAS_LLM=claude`
  altında bin çözümlenemezse `LLMPlannerError` **fabrika anında** patlar
  (run_loop'a girmez). Öncelik: `ATLAS_LLM_CLAUDE_BIN` env → `shutil.which("claude")`
  (Windows'ta `.cmd` uzantısını çözer). Çağrı-zamanı hataları (timeout,
  exit!=0, boş cevap) da `LLMPlannerError`; sözleşme: planner closure'ı
  yalnız bu istisnayı fırlatır.
- [KARAR] Yeni exit kodu **7** = LLM planner hatası. 6 workflow-handler'a
  ayrılmış (2026-07-28); karışmasın. `cli.py::_cmd_run_goal` fabrika ve
  runtime hatalarını ayrı `except` bloklarında yakalar, audit'e
  `("atlas-run","llm_error", str(exc)[:200])` yazar.
- [KARAR] `acp` ve `anthropic` backend'leri açık `NotImplementedError`
  ("Görev 003.1'de eklenecek") ile bırakıldı. Prompt YAML'da (Goal.llm_prompt)
  Görev 003.2. Retry Görev 013. Token cost Görev 011. Küçük tutuldu.
- [KARAR] Prompt **sabit ve kısa** (~450 karakter): görev + izinli fiiller
  + son 3 OBSERVE + "TEK satır yaz" direktifi. LLM çok satır yazarsa ilk
  satır alınır; boşsa `LLMPlannerError("boş plan")`.
- [HATA] Test suite'in `_run` helper'ları (`test_cli_goal.py`,
  `test_cli_workflow.py`) subprocess.run çağırırken `encoding` **vermiyordu**;
  Windows Türkçe locale'da (cp1254) reader thread UTF-8 çıktıyı decode
  edemeyip `UnicodeDecodeError` fırlatıyor, `?` karakteri koyup Türkçe
  arayan assertion'lar sessizce düşüyordu. 5 test flaky idi. Kalıp aslında
  DECISIONS 2026-07-24'te vardı ama CLI çıktısını **okuyan** taraf için
  taşınmamıştı. Düzeltme: `encoding="utf-8", errors="replace"` sabit.
- [HATA] `test_doctor_gui.py::test_restore_defaults_to_newest_and_can_pick_by_name`
  Windows mtime granülerliğinde flaky: iki yedek aynı saniye içinde
  oluşturulunca "en yeni" sıralaması karışıyor. 003 kapsamı dışı; Görev
  007+ notu.
- Kapsam: 1 modül düzenleme, 1 CLI düzenleme, 3 yeni test dosyası (16 test),
  toplam 302 test yeşil, coverage %94.84, mypy strict + ruff temiz.
  Artefaktlar `pipeline/tasks/003-llm-planner/`.

## 2026-07-28 (Görev 005 — GBrain FTS indeksi)
- [KARAR] Önbellek katmanı = `.atlas/gbrain.sqlite`; vault gerçek kaynak
  olarak kalır. İndeks silinirse bilgi kaybı yok — `atlas reindex` yeniden kurar.
- [KARAR] Stale tespit stratejisi: mtime hızlı yol, sha256 emniyet. mtime
  uyuşuyorsa hash atlanır (hız); mtime farklıysa hash ile teyit edilir
  (mtime hilesine karşı). Full rebuild'de her zaman hash.
- [KARAR] Skor sözleşmesi genişletildi ama uyumlu: FTS bm25 `1/(1+rank)`
  ile 0..1'e normalize edilir; W_TITLE=3, W_NEIGHBOR=0.5 sabitleri korundu.
  Ranked skorlar farklı sayısal aralıkta olsa da sıralama semantiği aynı.
- [KARAR] Otomatik reindex `recall()` başında lazy; `remember()` yazma
  yolunda `upsert` (deterministik, stale bırakmaz). Böylece kullanıcı
  `atlas reindex` çağırmayı unutabilir.
- [KARAR] FTS5 yoksa (nadir eski sqlite) `is_fts_available()==False`
  → GBrain eski O(N·M) yola düşer, stderr uyarı. Böylece yeni bağımlılık
  girmedi ama regresyon garantisi var.
- [KARAR] `GBrain.__init__` opsiyonel `index_path` alır; eski çağrılar
  aynen çalışır (default: `<vault>/../.atlas/gbrain.sqlite`).
- [KARAR] FTS sorgu güvenliği: `_sanitize_query()` alfanumerik+Türkçe
  karakterleri korur, geri kalanı boşluğa çevirir, ≥2 karakterli her
  token'ı `"..."` içine alır. FTS operatör enjeksiyonu (AND, ", (, ) )
  etkisiz.
- [HATA] İlk test `remember()` sonrası notu `vault/silinecek.md` yerine
  `vault/entities/silinecek.md`'de arıyordu — `remember` varsayılan
  folder="entities". Kalıp: vault yerleşimi remember default'una uyar.

## 2026-07-28 (Görev 004 — WorkflowEngine handler kaydı)
- [KARAR] Handler kaydı **paket** yapısı: `atlas_core/workflows/handlers/`
  altında her handler kendi dosyasında; `register_builtins()` fabrikası
  hepsini engine'e bağlar. Yeni handler eklemek = 1 dosya + 1 satır.
- [KARAR] Yıkıcı `memory.archive` handler'ı için varsayılan `dry_run=True`.
  Gerçek arşivleme YAML'da `with:{dry_run:false}` ister — kullanıcı niyeti
  önce, kaza güç. YAML-düzeyi `dry_run` handler-düzeyi varsayılanı ezer.
- [KARAR] `pipeline.test` handler'ı `sys.executable -m pytest` çağırır
  (`uv run pytest` DEĞİL) — taşınabilir bundle'da uv gerekmesin.
  Timeout 300s. Test suite'in kendini rekürsif çağırmaması için testler
  `paths=[tests/test_goals.py]` gibi minik alt-küme kullanır.
- [KARAR] CLI'da HandlerError ve WorkflowError ayrı yakalanır ama ikisi de
  exit 6 döner + audit'e "error" kaydı düşer. Ayrım hata mesajından okunur.
- [KARAR] Yeni exit kodu: `6` = handler başarısız / bilinmeyen handler.
- [HATA] pytest-cov subprocess CLI çağrılarını izlemiyor → cli.py kapsamı
  ilk turda %66'ya düştü. Çözüm: `test_cli_direct.py` in-process `main()`
  çağrılarıyla aynı branch'leri geziyor; kapsam %95'e çıktı. Kalıp: yeni
  CLI kodu için subprocess e2e testine ek olarak in-process test şart.

## 2026-07-28 (Görev 002 — Orkestratörün Canlanması)
- [KARAR] `atlas run --goal-file <yaml>` gerçek görev sürücüsü eklendi;
  eski konumsal `atlas run "hedef"` echo demo davranışı **korundu** (regresyon).
  Dallanma `_cmd_run` en üstünde; goal-file yoksa eski kod yolu.
- [KARAR] Orkestratör sözleşme dokunulmazlığı: `run_loop`, `Action`, `Judge`,
  `CallBudget`, `LoopResult` değişmez. Yeni yetenekler (goals/actions/planner/
  judges) bu sözleşmeyi karşılayan fabrikalar olarak eklendi. Bu, mevcut
  `test_platform.py`'yi kırmadan büyümeyi mümkün kıldı.
- [KARAR] Sandbox jail: `_jail()` platform-bagimsiz mutlak-yol reddi
  (`/`, `\`, `X:` prefix'i, `Path.is_absolute()`) + `is_relative_to()` +
  symlink reddi. Windows'ta `Path("/etc/x").is_absolute()` False döndüğü
  için manuel prefix kontrolü şart.
- [HATA] Plan formatı `fiil:arg1:arg2` — Windows drive letter (`C:`) parser'ı
  yanıltıyor (`write:C:/pwn.txt:x` → arg1="C"). Zararsız oluyor (sandbox
  içine `C/` klasörü yazılır) ama mutlak-yol reddi yine de platform-bagimsiz
  prefix kontrolüyle sağlanır.
- [KARAR] LLM planner ilk sürümde **stub** (`ATLAS_LLM=stub` varsayılan);
  gerçek `claude` subprocess entegrasyonu Görev 003. Gerekçe: DECISIONS
  2026-07-24'te subprocess+UTF-8 tuzağı belgelendi — tek görevde iki büyük
  risk tutulmaz.
- [KARAR] Shell komutu için `shell=False` **sabit** + `shlex.split` +
  goal dosyasındaki `shell_allow_regex` ile `re.fullmatch`. Global
  allowlist yerine hedef-başına allowlist (her hedefin izin sınırı kendi
  YAML'ında).
- [KARAR] Yeni exit kodları: `2` spec/YAML hatası, `5` action_denied.
  Mevcut `3` (bütçe) ve `4` (max_steps) korundu.
- [KARAR] Ruff N818: tüm istisna sınıfları `*Error` sonekli
  (`ActionDeniedError`, `PlannerExhaustedError`, `SpecError`, `SectionError`,
  `WorkflowError`, `BudgetExceededError`). Proje standardı.
- Kapsam: 5 yeni modül, 43 yeni test (250 toplam), coverage %90 korundu,
  mypy strict + ruff temiz. Görev 002 pipeline artefaktları
  `pipeline/tasks/002-orkestrator-canlanma/` altında.

## 2026-04-16
- [KARAR] Çekirdek: Claude Code CLI + GitHub issue akışı.
- [KARAR] Paket yöneticisi: uv; yoksa pip'e düş.
- [KARAR] Ruff N806 sections/ için kapalı: EN 1993 gösterimi (Iy, Wel_y) proje standardı.
- [KARAR] Sayısal test politikası: analitik formüller rel_tol=1e-9; katalog karşılaştırması ayrı testte, tolerans gerekçeli.

## 2026-07-24
- [KARAR] Depo git ile başlatıldı (varsayılan branch: main). İlk commit tüm mevcut ağacı kapsar.
- [KARAR] Platform giriş noktası: `atlas` CLI (`atlas_core.cli:main`). Katmanları (GBrain/orchestrator/AuditLog/scan_secrets) uçtan uca bağlar; alt komutlar: context/remember/recall/run/audit-verify/scan.
- [KARAR] Vault ve audit yolları ATLAS_VAULT / ATLAS_AUDIT ortam değişkenleriyle geçersiz kılınır; audit çıktısı `.atlas/` gitignore'da.
- [KARAR] Geliştirme ortamı uv ile 3.12'ye bağlanır: `uv sync --extra dev` (`.venv` = 3.12.6). Sistem Python 3.11 kullanılmaz; makinede Python 3.12 mevcut ve uv onu bulur.
- [HATA] CLI çıktısı üstsimge birimleri (mm², mm⁴) içeriyordu; Windows konsolu (cp1254) bunları kodlayamayıp UnicodeEncodeError veriyordu. Düzeltme: her iki CLI `main()` başında `sys.stdout/stderr.reconfigure(encoding="utf-8")`. Kalıp: kullanıcıya yazan her çıktı akışı UTF-8'e sabitlenmeli.
- [KARAR] Taşınabilirlik: Python 3.12 + uv + çalışma bağımlılıkları projeye gömülü (`runtime/`, `vendor/wheels/`). Başlatıcılar `%~dp0` göreli, venv `--relocatable`. Offline kurulum `--no-index` ile ispatlandı (venv silinip yeniden kuruldu). İkili yük git'te tutulmaz (gitignore); `make-portable.cmd` üretir (online), `setup-portable.cmd` kurar (offline).
- [KARAR] AI çekirdek (Claude Code CLI) taşınabilirlik istisnasıdır: gömülmez, ayrı kurulur, çalışırken ağ ister. Hesap + platform CLI'ları tamamen offline çalışır. Bkz `docs/OFFLINE.md`.
- [HATA] `pip download numpy>=1.26` bash'te çalıştırıldığında `>` yönlendirme sanılıp `=1.26` boş dosyaları üretti. Kalıp: sürüm kısıtlı paket adlarını bash'te tırnak içine al veya `.cmd` içinde çalıştır (make-portable.cmd böyle).
- [KARAR] Çok-platform bundle: `tools/make_portable.py` (stdlib-only) windows/linux/macos-arm/x64 için `dist/atlas-<hedef>/` üretir. Yorumlayıcı arşivi host'ta AÇILMAZ (Windows'ta yabancı arşiv extract çok yavaş — Defender); `runtime/python.tar.gz` kopyalanır, hedefte native tar açar. Böylece tüm platformlar tek Windows host'tan üretilir. Sürüm sabitleri script başında (PY_VERSION, PBS_TAG).
- [HATA] `setup-portable.cmd` içinde düz `tar`, PATH'te Git'in GNU tar'ı varsa `C:\...` yolundaki `:`'i "uzak host" sanıp patlıyor. Düzeltme: Windows built-in bsdtar'ı açıkça çağır (`%SystemRoot%\System32\tar.exe`). Linux/macOS'ta sorun yok (drive-colon yok). Windows bundle sıfır-kurulumdan uçtan uca doğrulandı (izole kopya → setup → launcher, gömülü yorumlayıcıyla).

## 2026-07-24 (Juggler entegrasyonu)
- [KARAR] Web UI + masaüstü GUI = Juggler (juggler-ai/juggler). Entegrasyon = Juggler eklentisi (`integrations/juggler/`, Apache-2.0 — SDK ile aynı, ATLAS'a copyleft bulaşmaz). Juggler çekirdeği AGPL-3.0 ama ayrı derlenir/çalışır (bundle'a gömülmez). Yetenekler: `atlas_section`/`atlas_recall` context-item araçları, `/atlas-section` komutu, sistem-prompt katkısı; ATLAS launcher'larına `juggler/ops` shell köprüsü (PATH'ten).
- [KARAR] Eklentinin stabil sözleşmesi için `atlas-sections --json` eklendi (properties+units, hata JSON'u stderr/exit 2). Metin parse'a bağımlılık = kırılganlık.
- [KARAR] Yedek AI CLI'ları: OpenCode (`opencode-ai`) + Kilo (`@kilocode/cli`) proje-yerel npm kurulumu (`tools/ai-cli/`, `setup-ai-cli.cmd`), Claude Code limitinde/tercihe göre. Config/data proje içine hapsedilir; kullanıcı home'una dokunulmaz. Başlatıcılar `opencode_Run.cmd`/`kilo_Run.cmd`. node_modules+home gitignore, package(-lock).json tutulur.
- [KARAR] **Juggler ACP Agents (5 yedek ajan)** — v0.4.1. opencode/kilo/cline (npm), kimi (pip `tools/ai-cli/py-venv`), goose (Windows binary `tools/goose/` v1.44.0). Hepsi stdio ACP handshake ile doğrulandı (opencode 1.18.4, kilo 7.4.15, cline 3.0.46, kimi 1.49.0, goose 1.44.0).
  - **Spawn sözleşmesi:** Juggler ajanı `exec.LookPath(command)` + doğrudan `exec.Command` ile başlatır (KABUK YOK) ve env'i parent+config merge eder. Bu yüzden: Node CLI'lar `command:"node" args:[<bin>,...]` (`.cmd` shim'i PE değil, bare ad PATH'te yok); derlenmiş/Python ikilileri mutlak `.exe` yolu; her ajan için env ile config/data proje-yerele yönlendirilir (kullanıcı home'una dokunulmaz).
  - **Üretim:** `tools/gen-acp-config.js` `<project>/.juggler/acp.json`'u varlık-kontrollü yazar (yalnız kurulu ajan); `setup-ai-cli.cmd` üç ekosistemi kurar; `setup-acp-agents.cmd` config'i üretir. acp.json makineye özel → gitignore (goose/py-venv de); generator tutulur.
  - **Tuzaklar:** (a) goose zip'i bsdtar/PowerShell açamaz (`-5` / corrupt 244M → segfault) → **Python `zipfile`** ile aç, indirme TAM bitince. (b) Kimi `printf | kimi acp` EOF ile ölür → doğrulama stdin'i açık tutmalı (Juggler zaten tutar). (c) Node CLI'ları shim yerine node ile çağır.
- [HATA] Kilo Windows'ta `XDG_*` değişkenlerini onurlandırmıyor — `$HOME` köklü (`~/.config/kilo`) yollar kullanıyor; ayrıca npm `.cmd` shim'i (`endLocal &`) parent'ta set edilen `USERPROFILE`'ı yutuyor. Çözüm: `kilo_Run.cmd` node'u DOĞRUDAN çağırır (shim'i atlar) + `HOME`/`USERPROFILE`/`HOMEDRIVE`/`HOMEPATH`'i proje-yerele set eder. OpenCode ise Windows'ta da `XDG_*` (4'lü) onurlandırır — sorunsuz. İkisi de proje-içine yazacak şekilde doğrulandı (gerçek home Jul-20 opencode dizini dokunulmadı).
- [HATA] Juggler kaynaktan derleme Windows engelleri: (1) shallow clone submodule almaz — `3rdparty/wails` SSH URL'li, HTTPS rewrite gerekti (`-c url.https://github.com/.insteadOf=git@github.com:`); (2) submodule checkout MAX_PATH(260) aşımı — `core.longpaths=true`; (3) `//go:embed icon.png` — `assets/icons/juggler-icon.png`'yi `cmd/juggler/app/icon.png`'ye kopyala; (4) `ext link` symlink Windows'ta Developer Mode/admin ister — alternatif kopyalama. Headless `cmd/juggler` CGO'suz derlenir (CGO'lu dosyalar yalnız darwin). Go 1.26.5 ile derlendi, `ext validate` geçti, sunucu localhost:3939'da açıldı.

## 2026-07-24 (kalite sertleştirme — v0.4.2)
- [HATA] CI kalite kapısı delikleri (öz-inceleme): mypy yalnız `src/sections`'ı, coverage yalnız `--cov=sections`'ı görüyordu → `atlas_core` (platform katmanı) tip-kontrol/kapsam DIŞINDA. Düzeltme: CI `mypy src` + `--cov=sections --cov=atlas_core --cov-fail-under=90` (toplam %96).
- [KARAR] CI çift-OS: `quality` (ubuntu; ruff, mypy, JS `node --check`+`node --test`, `atlas scan` sır taraması, pytest+coverage) + `test-windows` (windows-latest; pytest regresyon). Windows-öncelikli özellikler için Windows leg zorunlu.
- [KARAR] `.gitattributes` çapraz-platform satır-sonu sözleşmesi: `.cmd/.bat/.ps1`=CRLF, `.sh`=LF (CRLF olursa bash "bad interpreter"), kaynak/doküman=LF, `.webp/.png/.exe/.zip`=binary. Bunsuz `.sh` bozulma riski.
- [KARAR] Manuel-doğrulanan araçlara regresyon testi: `make_portable.py` (pytest, saf mantık — ağ/subprocess yok) ve `gen-acp-config.js` (`node --test`, sahte projectRoot + stub bin). CI'da zorlanır. Test tuzağı: ESM'de yol için `fileURLToPath` (Windows `.pathname` `/C:/` verir); `node --test` dizin yerine glob (`*.test.mjs`) ile çağrılır.
- [KARAR] Atıl `api` extra (fastapi/uvicorn) kaldırıldı — hiçbir kod/CI kullanmıyordu; API desk (skills/trading) gelince geri tanımlanacak. `docs/CONTRIBUTING.md` GitHub'ca otomatik algılandığı için (root/.github/docs) taşınmadı.

## 2026-07-27 (Juggler güncelleme riski + sağlık ajanı)
- [HATA] **Juggler kendi kendini güncelleyebiliyor ve ATLAS'ın ikilisini değiştirebilir.** Panelde yerleşik güncelleyici var: `internal/updatecheck` (juggler.studio manifest'i yoklar) + `internal/updateapply` (indirdiği zip'i açıp ÇALIŞAN `.exe`'yi rename edip yerine koyar — hedef dizin çalışan ikilinin dizinidir). ATLAS paneli `tools/juggler/juggler.exe` üzerinden çalıştırdığı için güncelleme ATLAS'ın kullandığı ikiliyi habersiz değiştirir; indirilen üstakım sürümünde yerel ACP `authenticate` düzeltmesi BULUNMAZ → cline/kimi gibi auth-gate'li ajanlar `session/new`'de kopar. Kalıp: proje-yerel tutulan üçüncü-parti ikililerin parmak izi (SHA-256) kaydedilmeli.
- [KARAR] Panel ikilisi ASLA otomatik indirilmez/güncellenmez. Güvenli sıra sabit: yedek → AYRI klasörde kaynaktan derle → `juggler ext validate` ile eklenti uyumluluğunu doğrula → ancak geçerse `tools/juggler/` içine kopyala. Gerekçe: ATLAS deposu güncellemeden etkilenmez (`tools/juggler/` gitignore'da) ama eklenti `engineApi ^1.0.0` bildirir; panel motor API'sini büyütürse eklenti SESSİZCE yüklenmez (hata yok, araçlar kaybolur).
- [KARAR] `DOCTOR.cmd` + `tools/doctor_gui/` — sağlık ve güncelleme ajanı (stdlib-only, `tools/setup_gui` modüllerini yeniden kullanır). Yedi adım: çalışma zamanları / Juggler / ACP ajanları / yerel AI / yapılandırma / sürüm izi / canlı sağlık. Her bulgu üç şeyi birden taşır — kanıt (`detail`), kök neden (`cause`), çözüm (`remedy`) — ve düzeltilebiliyorsa idempotent bir eylem (`fix`). Sürüm kaynakları: npm registry, PyPI, GitHub releases; ağ yoksa tarama durmaz, yalnız "son sürüm" boş kalır.
- [KARAR] `.atlas/doctor/baseline.json` = son sağlıklı andaki sürümler + panel ikilisinin SHA-256'sı. "Ne değişti?" sorusunu tahminden çıkarır: sürüm izi adımı sapmayı listeler, parmak izi denetimi sessiz self-update'i yakalar; her ikisi de "Yedekten geri al" eylemine bağlanır.
- [HATA] Semver ayrıştırmada `\b(\d+)\.(\d+)\.(\d+)\b` "v0.4.2" biçimini HİÇ yakalamıyordu: 'v' ile '0' arasında kelime sınırı yok. Sonuç sessiz yanlıştı — güncelleme mevcutken "güncel" deniyordu. Düzeltme: `(?<![\d.])(\d+)\.(\d+)\.(\d+)...(?![\d])`. Kalıp: sürüm dizgelerinde `\b` yerine "önünde rakam/nokta olmasın" koşulu.
- [KARAR] Yerel `Documents\juggler` ağacı üstakım v0.4.2 DEĞİL: git'siz bir çalışma ağacı ve upstream'de olmayan yerel iş içeriyor (`internal/updateapply`, `internal/registryfetch`, `internal/winlink`, `childcontain/{env,fs,policy,wsb}.go`, ACP authenticate + fs/terminal capability). v0.5.0 ayrı klasöre (`Documents\juggler-v0.5.0`) klonlandı; üstüne yazmak bu işi yok ederdi. v0.5.0'da ACP authenticate düzeltmesi HÂLÂ yok — yükseltmede yeniden uygulanmalı.

## 2026-07-27 (ATLAS Juggler profili — Juggler klasöründen bağımsızlık)
- [HATA] Global `~/.juggler/acp.json` beş ACP ajanının HEPSİNİ `Documents\juggler\scripts\*.cmd` ile kaydetmişti — yani ATLAS'ın panel ajanları Juggler ÇALIŞMA AĞACININ içindeki sarmalayıcılara bağlıydı. O ağaç silinir veya Juggler yeniden kurulursa ajanlar global kapsamda ölür. Fark edilmiyordu çünkü ATLAS projesi açıkken proje kaydı (`ATLAS/.juggler/acp.json`, ATLAS sarmalayıcıları) global'i eziyor; başka bir klasör açıldığında kopuyor. Kalıp: üçüncü-parti bir uygulamanın durum dizinine yazılan her kayıt, hedefin bizim depomuzun içinde olduğunu doğrulamalı.
- [KARAR] **`JUGGLER_CONFIG_DIR` kullanılır.** Juggler'ın kullanıcı durumu normalde `os.UserHomeDir()/.juggler`dır ama bu env değişkeni konumu tamamen taşır (`internal/userpaths`; kurulu v0.4.2 ikilisinde ampirik doğrulandı — geçici dizin verildiğinde `extensions/`, `commands/`, `credentials.json` oraya yazıldı). Başlatıcılar bunu `juggler-profile/home`a çevirir; eklenti, ACP kaydı, MCP, komutlar, skills, kimlik bilgileri artık ATLAS deposunun içinde. `~/.juggler`a dokunulmaz, ATLAS dışı kullanımda Juggler'ın varsayılanı olarak kalır.
- [KARAR] Tek klasör: `juggler-profile/`. `integrations/juggler` → `juggler-profile/extensions/atlas-engineering` taşındı (kullanıcı isteği: ATLAS'ın Juggler'a kattığı her şey tek yerde). Kaynak git'te; `juggler-profile/home/` üretilen çalışma dizinidir ve **gitignore'dadır** (credentials.json içerir).
- [KARAR] ACP ajanları profil içinde ŞABLON olarak tutulmaz, kurulumun gerçek durumundan üretilir (`detect.agent_specs` → `tools/agents/*.cmd`). Gerekçe: yollar makineye özeldir (node konumu, sarmalayıcı yolu); şablonla gerçek arasındaki sapma tam da paneli bozan şeydir.
- [KARAR] Senkron (`tools/juggler_profile/sync.py`, `juggler-profile_Sync.cmd`) idempotent ve yıkıcı değil: birleştirilen JSON'larda yabancı kayıtlar (başka ACP ajanı, başka MCP sunucusu) korunur, yalnız ATLAS'ınkiler tazelenir. Eski global `~/.juggler/acp.json` de onarılır — ama YALNIZ zaten varsa; kullanıcının hiç dokunmadığı bir yere durum yazılmaz. İlk kurulumda `~/.juggler`daki taşınabilir durum (kimlik, varsayılan model, skill kayıtları) kopyalanır ki panelde yeniden giriş gerekmesin.
- [KARAR] Doktora "ATLAS profili" adımı eklendi. Kritik denetim `profile.self-contained`: herhangi bir ATLAS ACP kaydı depo dışını gösteriyorsa FAIL — "Juggler klasörünü silsem ne kırılır?" sorusunun makine tarafından yanıtı. Düzeltmesi tek tık (`profile-sync`).
- [KANIT] Panel `JUGGLER_CONFIG_DIR` ile başlatıldığında logda `[PluginWatcher] Watching 5 dir(s) under: ...ATLAS\juggler-profile\home\extensions` çıkıyor; `ext validate` yeni kaynak yolunda geçiyor; senkron sonrası canlı ACP el sıkışması 5/5 eskisi gibi (opencode/kilo/goose OK, cline/kimi kimlik bekliyor).

## 2026-07-27 (Juggler v0.5.0 yükseltmesi + self-update olayı)
- [HATA] **Juggler kendi kendini güncelledi ve yerel işi sildi — ölçüldü, varsayım değil.** 13:29'da `tools/juggler/` içinde `juggler.exe.old-update` + `juggler-app.exe.old-update` belirdi; `updateapply` çalışan ikilileri yeniden adlandırıp yerlerine upstream v0.5.0'ı koydu. Gelen ikilide yerel bileşenlerin HİÇBİRİ yok (ikili içi dizge sayımı — `updateapply` 0, `registryfetch` 0, `winlink` 0, `SandboxSettings` 0, `authenticateParams` 0; dokunulmamış upstream v0.5.0 derlemesiyle birebir aynı profil). Doktorun SHA-256 parmak-izi denetimi olayı FAIL ile yakaladı. Kalıp: proje-yerel tutulan üçüncü-parti ikililerin kendi güncelleyicisi olabilir; parmak izi + yedek olmadan sessizce kaybedersin.
- [KARAR] Yükseltme fork-merge olarak yapıldı, yamayı elle taşıyarak değil: yerel ağacın tabanı ölçüldü (v0.4.2'ye 146 fark, v0.5.0'a 235 → taban v0.4.2), yerel iş v0.4.2 üstüne tek commit olarak aktarıldı, sonra v0.5.0 ile `git merge` edildi. 162 dosya / +12.990 satırlık yerel işte yalnız **5 çakışma** çıktı. Elle yama taşımak bu ölçekte güvenilir değildi.
- [KARAR] Çakışma çözümlerinde kural: iki taraf da özellik ekliyorsa İKİSİ de kalır (settings.go'da ConnectivitySettings+SandboxSettings; project-picker'da current+locked rozeti; iki import). Upstream bir yerel bloğu yardımcı fonksiyona çıkardıysa upstream'in yardımcısı kullanılır ama **yerel davranış farkı korunur** — `modelAlias` boş modeli "opus"a düşürmeye devam ediyor (operator tercihi 2026-07-23); upstream "sonnet" döndürüyordu ve bu sessiz bir davranış değişikliği olurdu.
- [KANIT] Satır sonu tuzağı: ilk karşılaştırmada web/ 452 dosya "farklı" göründü; gerçek fark 50'ydi. Sebep: klonda `core.autocrlf` açık (CRLF), yerel ağaç LF. Kalıp: git'siz bir ağaçla karşılaştırma yapmadan önce `core.autocrlf=false` + yeniden checkout.
- [KANIT] Doğrulama: `go build ./...` + `go vet ./...` temiz; 40 paket testi geçti; yerel paketler (updateapply/registryfetch/childcontain/acp) yeşil. Tarayıcı entegrasyon paketi bu makinede kararsız — **aynı makinede dokunulmamış v0.5.0 daha fazla düşüyor (7 vs 2)**, yani birleştirmeden gelmiyor. Kurulum sonrası: `ext validate` geçti, panel profille açıldı (`PluginWatcher ... juggler-profile\home\extensions`), canlı ACP el sıkışması 5/5 eskisi gibi.
- [KARAR] Geri dönüş noktaları: `.atlas/doctor/juggler-backup/` (yerel v0.4.2 derlemesi) ve `.atlas/doctor/juggler-upstream-v0.5.0/` (self-update ile gelen saf upstream). `.old-update` kalıntıları silindi (hash'i yedekle birebir aynı, doğrulandı).
- [KARAR] **Panelin otomatik güncelleyicisi kapatıldı** (`settings.json` → `updates.mode="off"`), hem profil çalışma dizininde hem eski konumda (`~/.juggler`; panel başlatıcısız açılırsa oradan okur). Ayar profilin kaynağında tutulur ve senkron her açılışta dayatır; doktorun `profile.autoupdate` denetimi açık bulursa FAIL verir. Kapatılan yalnız kendiliğinden indirme — manuel "güncelleme denetle" çalışır. Gerekçe ölçülmüş olaydır (yukarıdaki self-update kaydı), tercih değil.
- [HATA] **ACP sağlık testi ajanların alt süreçlerini öldüremiyor.** Ajan süreci kapatılıyor ama asıl işi yapan alt süreç öksüz kalıyor (ölçüldü: cline, goose). Bugün iki somut zarar verdi: OpenCode güncellemesinde `npm install` **EBUSY** (çalışan `cline.exe` kilitli) ve eski ağacı arşivlerken **Permission denied** (üç goose.exe). Tek taramada **42 öksüz süreç** sayıldı. Çözüm: doktora "Artık süreçler" adımı — yalnız DEPO İÇİNDEKİ ajan ikilileri sayılır (başka kurulumlara/kullanıcının kendi CLI'sına dokunulmaz), panel açıkken hiç sayım yapılmaz, tek tıkla kapatılır. `taskkill` "not found" dönüşü BAŞARISIZLIK değil "zaten sonlanmış" sayılır — üst süreç kapatılınca altları da ölür, yoksa temizlik hep kısmen başarısız görünür.
- [HATA] Artık-süreç denetiminin ilk sürümü asıl vakayı KAÇIRIYORDU: npm ajanları işi ayrı bir platform paketinde yapar — cline'ın kaydı `node_modules/cline/bin/cline` iken çalışan süreç `node_modules/@cline/cli-windows-x64/bin/cline.exe`. İkincisi birincinin kardeşi olmadığı için yalnız yola bakan ölçüt görmüyordu; `npm install` EBUSY'sine yol açan süreç tam olarak buydu. Düzeltme: depo sınırı içinde kalmak kaydıyla **ada göre** de eşleştir (`Path(exe).stem in {opencode,kilo,cline,kimi,goose}`). Kalıp: bir özelliği doğrularken onu doğuran GERÇEK vakayı yeniden üret — "temiz" çıktı, ölçütün dar olduğunu gizleyebilir.
- [HATA] Sihirbazın "Giriş yap" düğmesi üç ajanda YANLIŞ komut üretiyordu. Ajan tanımlarında `auth_cmd` yoksa varsayılan `["auth"]` kullanılıyordu; oysa `--help` çıktılarıyla ölçüldü: `kimi`de `auth` diye bir alt komut YOK (doğrusu `kimi login`), `opencode`/`kilo`da `auth` bir komut GRUBU (list/login/logout) — tek başına yalnız yardım basar, giriş `auth login` altındadır. Yalnız `cline` doğruydu (`auth cline`). Sonuç sessiz başarısızlıktı: düğmeye basılınca pencere açılıp hata veriyor, kimse giriş yapamıyordu. Üçü de açık `auth_cmd` ile sabitlendi ve testle korundu. Kalıp: bir dış CLI'nın alt komutunu VARSAYMA — `--help` ile ölç, tanımda açıkça yaz.
- [HATA] Sağlık sınaması panelin el sıkışmasını EKSİK taklit ediyordu: yalnız `initialize` + `session/new` yapıyor, panelin (yerel yamayla gelen) `authenticate` turunu atlıyordu. Sonuç yanıltıcıydı — cline CLI'dan giriş yapılmış ve panelde çalışacak durumdayken sınama "Authentication required" diyordu. Düzeltme: `session/new` kimlik hatası verirse `initialize`in ilan ettiği `authMethods` ile sırayla `authenticate` çağrılıp session/new bir kez yineleniyor (panelin `cmd/juggler/providers/acp/session.go` akışının birebir aynısı). Doğrulandı: cline artık "bağlantı doğrulandı" veriyor. Ek: kimlik yokken `authenticate` ajanı asabildiği için, o durumda "timeout" yerine ilk hatanın kendisi ("Authentication required") bildiriliyor — kullanıcı asıl nedeni görüyor. Kalıp: bir davranışı taklit eden sınama, taklit ettiği kodun DEĞİŞTİĞİNİ takip etmezse sessizce yanlış cevap verir.
- [KARAR] **kimi devre dışı bırakıldı** (`juggler-profile/profile.json` → `disabledAgents`). Gerekçe ölçülmüş: cihaz girişi TAMAMLANDI (token `.kimi/credentials/kimi-code.json`'a yazıldı) ama kullanılabilir modeli yok — config'i sildiğimiz yerel `ollama/llama3.1:8b`'yi gösteriyor ve Kimi Coding bulut uçları `402 Payment Required` dönüyor. Belirti kararsız "Internal error"du: ACP el sıkışması modele dokunmayan turlarda geçiyor, model doğrulamasına giren turlarda düşüyordu (3 turda 2/1). Mekanizma: devre dışı ajan panele yazılmaz VE varsa eski kaydı kaldırılır — kaydı elle silmek yetmez, senkron her açılışta kurulu ajanları yeniden yazar. Doktor bunu arıza değil bilgi olarak gösterir. Geri açmak: listeden çıkar + senkron.

## 2026-07-28 (Ollama cloud + goose bağlantısı)
- [KARAR] goose **`gpt-oss:120b-cloud`** modeline bağlandı (`tools/agents/local-model.cmd`). Uçtan uca kanıt: `goose run --no-session -t "Reply with exactly: ATLAS-OK"` → `ATLAS-OK`. ACP el sıkışması modeli kullanmadığı için tek başına yeterli DEĞİLDİ; gerçek tur koşuldu.
- [HATA] **Kayıtlı olmak, modelin istek alabildiği anlamına gelmiyor.** Ollama cloud modelleri `ollama list`te görünür ama çoğu ücretli abonelik ister: ölçüldü (hesap `amon001100`, ücretsiz katman) — `kimi-k2.7-code:cloud` ve `qwen3.5:cloud` ilk istekte `this model requires a subscription`, `gpt-oss:120b-cloud` ve `20b-cloud` çalışıyor. Eski `pick_model` yalnız ada bakıyordu ve bu listede `qwen3.5:cloud`/`kimi-k2.7-code:cloud` seçiyordu — yani sihirbaz ajanı kullanılamayan modele bağlardı ve arıza ancak kullanıcı ilk soruyu sorunca çıkardı. Düzeltme: `model_works()` (tek, `num_predict:1` üretim denemesi) + `pick_model(models, base_url)` adayı DENEYEREK seçiyor; hiçbiri çalışmıyorsa sessizce ilkini seçmek yerine None dönüp açık hata veriyor. `MODEL_PREFERENCE` cloud adlarını da kapsayacak şekilde genişletildi. Kalıp: "kurulu ≠ çalışıyor" kuralı modeller için de geçerli.
- [KARAR] `qwen3-coder`'ın cloud etiketi YOK (yalnız yerel `30b`/`480b`…); cloud katalogda 19 model var. İstenen model bulunamadığında tahminle muadil kurulmaz — katalog sorgulanır, doğrulanmış etiketler kullanıcıya sunulur.

## 2026-07-28 (kimi geri açıldı — iki ayrı arıza)
- [KARAR] **kimi yeniden etkinleştirildi** (`juggler-profile/profile.json` → `disabledAgents` boşaltıldı). Dünkü kapatma gerekçesi (modelsizlik) ortadan kalktı: `enable_keyless('kimi')` kimi'nin config'ini çalışan tek modele (`ollama/gpt-oss:120b-cloud`) bağladı. Kanıt sırayla: gerçek CLI turu (`kimi --quiet -p "Reply with exactly: ATLAS-OK"` → `ATLAS-OK`), ardından panelin akışıyla birebir aynı ACP el sıkışması 6/6 `ready`, senkron sonrası kayıtlı sarmalayıcı üzerinden 5/5 `ready`, doktorun profil/ajan/canlı sağlık adımlarında sıfır bulgu.
- [HATA] **Dünkü kararsız "Internal error" modelden DEĞİL, git-bash aramasından geliyormuş.** Ham JSON-RPC ile hata gövdesi açılınca asıl neden çıktı: `kimi-cli on Windows requires Git for Windows ... set KIMI_CLI_GIT_BASH_PATH`. kimi Shell aracı için bash'i HER `session/new`'de yeniden arıyor: `where.exe git` → `git --exec-path` (5 sn zaman aşımı) → yalnız `C:\Program Files\Git\...`. Bu makinede git kullanıcı dizinine kurulu (`%LOCALAPPDATA%\Programs\Git`), yani ilk iki adım tutmazsa çare kalmıyor ve arama yük altında arada bir düşüyor — ölçüldü: pinsiz 3 turda 1, sonra 5 turda 2 hata; pinli 6/6 ve 5/5 temiz. Düzeltme: sarmalayıcı üreticisi (`wrappers.git_bash_path`) yolu BİR KEZ çözüp `KIMI_CLI_GIT_BASH_PATH` ile sabitliyor. Kalıp: kararsız arıza modelin/ağın değil, ajanın her açılışta yeniden yaptığı bir KEŞFİN olabilir — hata gövdesini (`error.data`) yutma, aç ve oku.
- [KANIT] "Güncelleme var" rozeti YANILTICIYDI — yeni sürüm yok. Ölçüldü: manifest (`juggler.studio/juggler-version.json`) `latest: v0.5.0`, GitHub `releases/latest` `v0.5.0`, kurulu ikili `v0.5.0 (73e41a6)`, panelin kendi ucu `/api/update-status` → `updateAvailable: false`, doktorun parmak izi denetimi temiz. Panel yeniden açıldığında rozet çıkmadı. Kalıp: rozet/uyarı bir iddiadır — uygulamanın kendi durum ucunu oku, ölçmeden "güncelleme yap" deme.
- [HATA] **Doktorun "Şimdi yedek al" düğmesi tek geri dönüş noktasını eziyordu.** Hedef sabitti (`.atlas/doctor/juggler-backup/`); orada yerel v0.4.2 derlemesi duruyordu ve ikinci bir yedek onu sessizce silerdi — üstelik düğmenin adı "yedek al"dı, "yedeği değiştir" değil. Düzeltme: hedef sürümden türer (`juggler-backup-v0.5.0-73e41a6`; sürüm okunamazsa ikilinin SHA-256'sından `bilinmeyen-<12>`), yani aynı yapı aynı klasörü tazeler (idempotent) ama farklı yapı ASLA başkasının üstüne yazmaz. `VERSION.txt` artık sürümün yanında iki ikilinin parmak izini de taşır. "Yedekten geri al" adsız çağrıda EN YENİ yedeği kullanır, `{"name": ...}` ile belirli yedek seçilebilir (uç zaten gövdeyi params olarak geçiriyordu; arayüz değişikliği gerekmedi). Eski sürümsüz klasör listelenmeye ve geri alınmaya devam eder.
- [KARAR] **Taşınabilirlik: klasörü sıkıştır → başka Windows'ta aç → `BASLAT.cmd`.** Üç yeni giriş noktası (`BASLAT.cmd`, `GUNCELLE.cmd`, `PAKETLE.cmd`) ve `tools/portable/` katmanı. `BASLAT.cmd` gömülü yorumlayıcıyı (`runtime/python/cpython-*`) kendisi bulur — sistem Python'u gerekmez; taşınabilir araçların tamamı stdlib-only olduğu için venv de gerekmez.
- [HATA] **Üretilen sarmalayıcılar makineye özgü MUTLAK yol gömüyordu** — node `%LOCALAPPDATA%\hermes\node.EXE`, git-bash `%LOCALAPPDATA%\Programs\Git\bin\bash.exe`. Klasör başka bir bilgisayarda açılınca kilo/cline/kimi ölürdü ve kullanıcı bunu ancak ajan konuşmayınca anlardı. Düzeltme: ikisi de depo içine alındı (`tools/node`, `tools/git`; `python -m tools.portable.vendor` indirir) ve sarmalayıcılar `%ROOT%` göreli yazıyor. Çözüm sırası `tools/portable/runtimes.py`de: **önce depo içi kopya**, sonra makine — taşındığında ayakta kalan tek şey depo içidir. Test: hiçbir sarmalayıcı depo kökünün mutlak yolunu içermemeli.
- [KARAR] MinGit `bash.exe` GÖNDERMEZ, yalnız `sh.exe`. ÖLÇÜLDÜ: kurulu Git for Windows'ta `usr/bin/sh.exe` ile `usr/bin/bash.exe` sha256 olarak BİREBİR aynıdır (bash kipini argv[0]'dan seçer). Vendor, `sh.exe`yi `bash.exe` adıyla KOPYALAR (yeniden adlandırmaz — `sh.exe` bekleyen kırılmasın). Kimi bu bash ile 5/5 `ready` verdi.
- [KARAR] `.atlas/portable/machine.json` = makine parmak izi (host, kullanıcı, depo yolu, node/bash konumu). `BASLAT.cmd` her açılışta karşılaştırır; değiştiyse sarmalayıcılar + ACP kayıtları + Juggler profili yeniden ÜRETİLİR (şablondan değil, kurulumun gerçek durumundan). Değişmemişse hiçbir şey yapılmaz. Gerçek prova: parmak izi başka bir makineden gelmiş gibi yazıldı → `BASLAT.cmd` "Yeni yerlesim algilandi (host, root, node)" deyip üçünü de tazeledi, ardından beş ajan yine `ready`.
- [KARAR] Otomatik güncelleme `atlas-portable.json` ile: `agents` (varsayılan; npm/pip ajanları günde bir kez sessizce) / `notify` / `off`. **Panel ikilisi hiçbir ayarda otomatik güncellenmez** — 2026-07-27 self-update olayı. Kanıt: ilk çalıştırmada opencode 1.18.7 → 1.18.8 kendiliğinden güncellendi ve beş ajan yine `ready` verdi. Güncelleme npm'i de depo içinden alır (`tools/node/npm.cmd`), yoksa npm kurulu olmayan bir makinede güncelleme hiç çalışmazdı.
- [HATA] **Ollama bulut kimliği depo DIŞINDA kalıyordu — taşımanın sessiz katili.** `ollama signin` kimliği bir anahtar çiftidir (`%USERPROFILE%\.ollama\id_ed25519`); sarmalayıcı yalnız `OLLAMA_MODELS`i depoya çeviriyordu. ÖLÇÜLDÜ: ev dizini boş bir klasöre çevrilince ollama YENİ anahtar üretti ve bulut modeli `{"error":"Unauthorized"}` döndü; gerçek anahtar kopyalanınca aynı uç yanıt üretti ve goose gerçek turu tamamladı. Yani taşınan klasörde goose+kimi çalışmaz, kullanıcı yine "kurulum" yapardı. Düzeltme: `ensure-ollama.cmd` sunucunun `USERPROFILE`/`HOME`unu `tools/ollama/home`a çevirir, `tools/portable/ollama_identity.py` anahtarı ilk açılışta bir kez depoya alır ve **taşınan anahtarı asla ezmez** (hedef makinede hesap olmayabilir). Kalıp: "durumu proje içine hapsettik" demeden önce KİMLİĞİN nerede durduğunu ayrıca sor — model/ayar yolu taşınıyor diye kimlik de taşınıyor sanma.
- [HATA] Arşivleyici araması sürücü harfini VARSAYIYORDU (`C:\Program Files\WinRAR\Rar.exe`). Bu makinede WinRAR `D:\Program Files` altında kuruluydu; arama onu göremeyip 7-Zip'e düşüyor, 7-Zip de RAR yazamadığı için (`System ERROR: Not implemented`, RAR tescilli biçim) iş patlıyordu. Düzeltme: PATH + tüm sabit sürücülerin `Program Files`/`Program Files (x86)` dizinleri taranır ve hedefin uzantısı hangi aracı gerektiriyorsa o öne alınır; ayrıca 7-Zip'e `.rar` hedefi verilirse iş BAŞLAMADAN açık hata döner (3-4 GB'lik uğraşın sonunda değil). Kalıp: "kurulu değil" demeden önce aramanın kendisinden şüphelen — kurulum yolu sabit değildir.
- [KARAR] Preflight'a iki taşıma riski eklendi: `path.length` (kök yolu 60 karakterden uzunsa uyarır — derin `node_modules` ağacı Windows'un 260 karakter sınırına arşiv AÇILIRKEN takılır ve dosyalar sessizce eksik kalır) ve `auth.ollama`. Mark-of-the-Web, antivirüs ve x64-mimari riskleri `docs/TASINABILIR.md`de yazılı.
- [KARAR] `PAKETLE.cmd --bulut` yerel model çalıştırıcılarını (`tools/ollama/lib`, 1,8 GB) arşive koymaz. ÖLÇÜLDÜ: klasör tamamen kaldırılmışken ollama sunucusu açıldı, `/api/tags` bulut modelini listeledi, `/api/generate` yanıt üretti ve goose gerçek bir turu tamamladı (`LIBSIZ-AJAN-OK`) — bulut modelleriyle çalışırken bu klasör gerekmiyor. Varsayılan davranış **silmek değil dışlamak**: arşivleyiciye dışlama argümanı geçilir (WinRAR `-x<yol>\*`, 7-Zip `-x!<yol>` — biçimi karıştırmak sessizce etkisiz kalır, test bunu koruyor), elle sıkıştıracaklar için liste basılır; `--sil` istenirse klasörden de kaldırır. Geri alma yolu raporun içinde: `SETUP.cmd > Yerel AI`. Kalıp: yer kazandıran her seçenek NE KAYBETTİRDİĞİNİ ve nasıl geri alınacağını aynı ekranda söylemeli.
- [HATA] `ensure-ollama.cmd`in hazırlık sınaması `ollama list`ti ve ÖLÇÜLDÜ (2026-07-28): sunucu bulut ucuna takıldığında `list` süresiz asılıyor — sarmalayıcı hiç dönmüyor, ajan hiç başlamıyordu (kimi/goose "timeout"). Düzeltme: `curl.exe -m 3` ile HTTP `/api/tags` yoklaması (Windows 10+ curl'ü getirir; yoksa eski yönteme düşülür). Kalıp: hazırlık sınaması zaman aşımı olmayan bir komuta dayanamaz.
- [HATA] kimi'nin sarmalayıcısı `ensure-ollama.cmd` çağırmıyordu; oysa modeli artık yerel Ollama'dan geliyor (makine yeniden başladıysa sunucu kapalı olur). Üretici koşulu `keyless` (yalnız goose) yerine `keyless or local_model_ok` (goose + kimi) oldu; `GOOSE_*` varsayılanları yine yalnız goose'a yazılıyor.
