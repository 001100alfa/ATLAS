# ATLAS Karar Günlüğü
Format: `## TARİH` altında madde; her madde [KARAR]/[VARSAYIM]/[HATA] etiketi taşır.

## 2026-07-29 (Görev 020 — `atlas run --dry-run` rehearsal)
- [KARAR] **Tek adım rehearsal** — action stub'landı + judge sabit
  True. Alternatif "N adım simüle et" bilinmiyor bir gelecek (planner
  ne üretir?); kullanıcı için tek adım yeter: prompt/YAML doğru mu?
  Cost gerçek mi? Tam koşuyu istiyorsa `--dry-run` çıkarır. YAGNI
  minimum.
- [KARAR] Planner **gerçek** — LLM gerçek fiyata çağrılır, cost
  audit'e yazılır, retry çalışır. Amaç "yıkıcı iş yok" değil
  "sistem yıkımı yok"; kullanıcı **fiyatı görsün** ki YAML/prompt
  optimizasyonu yapabilsin. Cost simülasyonu (fake usage) kandırıcı
  olur.
- [KARAR] Action stub'ı **lambda** olarak yazıldı (`# noqa: E731`)
  — inline, minimum kod. `def _act(...)` fonksiyon adı yerine
  intent daha net. `run_loop` sözleşmesi (`Action = Callable[[str],
  tuple[str, float]]`) sağlanıyor.
- [KARAR] Judge sabit True → run_loop ilk adımdan sonra `done=True`
  bulur; `max_steps` beklenmez. Tek plan → tek observe → dur.
  Kullanıcı planı görür, işim biter.
- [KARAR] Audit'e ayrıca `("atlas-run", "dry_run", <goal>)` marker —
  kullanıcı sonradan denetim zincirinde "bu run gerçek miydi
  dry-run mıydı?" ayırabilsin. Aksi hâlde dry-run kayıtları normal
  koşularla karışır.
- [KARAR] LLM hata yolları (LLMPlannerError exit 7) `--dry-run`
  ile bypass edilmez — planner fabrikası ilk çağrıda LLM'e ulaşmaya
  çalışır; bin yoksa/key yoksa yine hata alınır. Bu **doğru davranış**:
  dry-run "gerçek plan üretiminin" simülasyonu; LLM kurulumu yoksa
  test etmenin anlamı yok.
- [KARAR] mypy Callable variable annotation — inline lambda + reassign
  tip daralması için gerekli (`act: Callable[...]; act = lambda ...`).
  `collections.abc.Callable` import edildi (stdlib idiomatic).
- Kapsam: 1 modül düzenleme (cli.py: +Callable import + _cmd_run_goal
  dry-run dallanma ~15 sat + parser --dry-run flag), 1 test dosyası
  genişleme (+4 test). Toplam 481 test yeşil (477 → +4). mypy strict
  + ruff temiz. Artefaktlar `pipeline/tasks/020-run-dry-run/`.

## 2026-07-29 (Görev 019 — Anthropic streaming, opt-in)
- [KARAR] Opt-in `Goal.stream: bool = False` — non-streaming yol
  varsayılan; 011/013/015.1 test suite'i bit-uyumlu. Streaming'i
  aktif eden görev bazında karar verir (uzun response beklenen
  görevlerde).
- [KARAR] **İlk newline'da kes** — ATLAS planner sözleşmesi "tek
  satır" olduğundan tam response'u beklemek anlamsız. `text_delta`
  chunk'ları biriktir, `"\n" in joined` görünce `first_line`'ı
  al ve `resp.close()`. Sunucu tarafında kalan chunk'lar üretilmeye
  devam edebilir ama bize hız kazancı.
- [KARAR] Inline SSE parser (stdlib-only) — ~50 sat kod; `sseclient`
  kütüphanesi eklemek istenmez. Format basit: `event: X\ndata: {...}\n\n`.
  Satır satır oku, `event: ` başlı satırlar current event'i set eder,
  `data: ` satırları JSON parse edilir, boş satır event'i sonlandırır.
- [KARAR] Usage yakalama tam — `message_start.message.usage`
  (input_tokens öncesi) + `message_delta.usage` (output_tokens güncel).
  `_extract_usage` mevcut sözleşmesi kullanılır (011/013/015.1 uyum).
  Erken kes'ten sonra usage 0 kalabilir (message_delta gelmedi) —
  kabul: hız > tam usage.
- [KARAR] Hata dallanması: geçersiz SSE JSON → net mesaj
  `"streaming: geçersiz SSE data: <ilk 200>"`. HTTPError yolu **aynı**
  (streaming'de urlopen `Content-Type` etkilemez). RetryAfterError
  streaming'de de tetiklenir (aynı except kolu — kodu tekrar etmiyoruz).
- [KARAR] `resp.close()` **`finally`** bloğunda — early return'de bile
  bağlantı sızıntısı yok. `Exception` yakalamada `noqa: BLE001` (teardown
  ana hatayı gölgelemez).
- Kapsam: 1 modül düzenleme (goals.py: +stream alanı + load kolu),
  1 modül düzenleme (planner.py: _call_anthropic stream keyword +
  _read_anthropic_stream ~65 sat + _anthropic_planner bind),
  2 test dosyası genişleme (+8 test). Toplam 477 test yeşil (469 → +8).
  mypy strict + ruff temiz. Artefaktlar
  `pipeline/tasks/019-anthropic-streaming/`.

## 2026-07-29 (Görev 018 — gözlem uzunluk kırpma env)
- [KARAR] Env **runtime** okunur — `_format_prompt` her çağrıda
  `_read_obs_chars_env()`. Cache'lemek performans için mikro-iyileştirme
  ama env değişikliği anında etkili olmalı (kullanıcı `export ATLAS_LLM_OBS_CHARS=500`
  yapıp yeniden çalıştırınca fark hemen görülebilmeli).
- [KARAR] Aralık üst sınırı **2000** — sistem prompt + context (4000) +
  gözlem × 3 = ~10k char güvenli. Üst sınır yoksa kullanıcı `100000`
  yazıp prompt token limit'ini aşabilir. 2000 hem büyük stderr'a
  hem token bütçesine dost.
- [KARAR] Fail-safe fallback varsayılana — kullanıcı yanlış env yazarsa
  bug yerine 200 (`_DEFAULT_OBS_CHARS`) kullanılır; hata mesajı yok
  (env okuma tolere).
- Kapsam: 1 modül düzenleme (planner.py: +2 sabit, +_read_obs_chars_env
  yardımcı, _format_prompt runtime kullanım — ~15 sat), 1 yeni test
  dosyası (9 test). Toplam 469 test yeşil (460 → +9). mypy strict +
  ruff temiz. Artefaktlar `pipeline/tasks/018-obs-chars-env/`.

## 2026-07-29 (Görev 016.1 — ACP `fs/read_text_file` minimum destek)
- [KARAR] Request/notification ayrımı **`id` alanı**: request `id`+`method`
  var; notification sadece `method`. `_call_acp` dispatcher ilk kolda
  request'e cevap yazar, sonra 016 notification kollarına düşer.
  Böylece 016 tool_call sert red davranışı 016.1'in request yolundan
  etkilenmez — regresyon güvencesi ayrı test.
- [KARAR] **Yalnız read-only** `fs/read_text_file`. Yazma/shell
  metotları `-32000 not supported`. Neden: agent'ın plan üretimi için
  kod okuma yeter (klasör keşfi, mevcut dosyaları anlama); yazma
  planlayıcı sözleşmesi dışında (ATLAS'ın Action katmanı yapar).
  Terminal desteği güvenlik burden'ı büyük (sandbox, timeout, kill);
  YAGNI.
- [KARAR] Proje kökü = `os.getcwd()` — override YOK. ACP sözleşmesinde
  agent zaten `cwd` alır (`session/new.params.cwd`); ATLAS bunu
  set ederken kendi cwd'sini bildirdi. Traversal denetimi
  `Path.resolve().relative_to(root.resolve())`. `..` bileşenleri ve
  symlink'ler çözülür, kök dışı kaçış engellenir.
- [KARAR] `params.line` **1-tabanlı** (ACP sözleşmesi); ATLAS Python
  `splitlines()` 0-tabanlı — `line - 1` dönüşümü açık. `limit`
  verilmezse `line`'dan itibaren tümü.
- [KARAR] Bilinmeyen method **JSON-RPC standart** `-32601 Method not
  found`. Custom kod (`-32000`) yalnız yazma reddi için — hata
  ayrımı temiz: "method yok" vs "method var ama izin yok".
- [KARAR] Client-provided handler'lar planner sözleşmesini kirletmiyor
  — `_call_acp` içinde yerel yardımcılar. Alt-modüle çıkarma
  (`_acp_client_handlers.py`) YAGNI; yaklaşık 100 sat.
- Kapsam: 1 modül düzenleme (planner.py: +Path import, +_ACP_*_METHODS
  sabitleri, +_acp_handle_client_request + _acp_fs_read_response +
  _resolve_project_path ~100 sat, _call_acp dispatcher küçük değişim),
  1 test dosyası genişleme (+6 test). Toplam 460 test yeşil (454 → +6).
  mypy strict + ruff temiz. Artefaktlar `pipeline/tasks/016-1-acp-fs-read/`.

## 2026-07-29 (Görev 015.1 — cache-hit token indirimi)
- [KARAR] Anthropic tarife çarpanları **modül sabitleri**:
  `_CACHE_READ_MULT = 0.1`, `_CACHE_WRITE_MULT = 1.25`. Kamu tarife.
  Model-özel farklılaştırmadık (Sonnet/Opus aynı oran); Anthropic
  tarifesi değişirse tek yerden güncellenir.
- [KARAR] `_extract_usage` **4-tuple**'a genişledi — `(input, output,
  cache_creation, cache_read)`. İç fonksiyon; kırma maliyeti düşük;
  tüm çağıranları (trace + on_usage) tek yerden güncelledik.
- [KARAR] `on_usage` callback imzası **2-arg → 4-arg** (`(int, int)`
  → `(int, int, int, int)`) — 013 sözleşmesi kırıldı ama:
  1. İç API (public planner Callable etkilenmedi)
  2. 013'ten kısa süre geçti, tek çağıran var (CLI)
  3. Alternatif: cache alanlarını bir 4. arg yerine `**kwargs` ile
     iletmek okunması zor kod. Basit tuple daha net.
  Test tarafında 2 test güncellendi (4-arg lambda) — kırma acısız.
- [KARAR] `CallBudget.charge_tokens` yeni kwargs `cache_creation: int
  = 0`, `cache_read: int = 0` **keyword-only + default=0** — 013
  mevcut çağrıları bit-uyumlu. `charge_tokens(a, b, c, d)` hâlâ
  çalışır. Genişleme kırmadan geldi.
- [KARAR] Trace format `in=N (cache=W r=R) out=M` — cache varsa
  parantez. Yoksa 011 formatı bit-uyumlu (`in=N out=M`). Grep/awk
  hala kolay; kullanıcı `cache=` gördüğünde hemen "cache-hit
  bilgisi" olduğunu anlar.
- [KARAR] Trace ve charge_tokens tek gerçek kaynak: `_extract_usage`.
  Cache hesabı iki yerde de aynı (indirim = %10 read, %125 create).
  Bir yerde bug varsa diğerinde de var; test yalıtımı temiz.
- Kapsam: 1 modül düzenleme (planner.py sabitler + _extract_usage
  4-tuple + _fmt_cost cache paramları + trace format + on_usage tip),
  1 modül düzenleme (core.py charge_tokens kwargs), 1 CLI düzenleme
  (_on_usage 4-arg), 2 test dosyası genişleme (+10 test). Toplam
  454 test yeşil (444 → +10). mypy strict + ruff temiz. Artefaktlar
  `pipeline/tasks/015-1-cache-hit-discount/`.

## 2026-07-29 (Görev 017 — `atlas archive --auto` yaş filtresi)
- [KARAR] Yaş ölçüsü **`09-ship.md` dosyasının st_mtime**'ı — task
  klasörünün oluşum tarihi değil. SHIP zamanı "görev bitti" işareti;
  klasör oluşum tarihi görevin başlangıcı olabilir. Kullanıcı SHIP
  yazdıysa arşive uygunluğu ilan etmiş demektir; N gün sonra otomatik
  taşıma mantıklı.
- [KARAR] Varsayılan **7 gün** — bir hafta yeterli "soğuma" süresi.
  Kullanıcı SHIP sonrası son bir hafta içinde geri dönüp düzeltmek
  isteyebilir; 7 gün sonra istikrar sağlanmış sayılır. `ATLAS_ARCHIVE_AGE_DAYS`
  env override — kullanıcı 30/90 gün istese ayarlayabilir.
- [KARAR] `--auto` `--all` ile birlikte anlamlı — tek görev yolunda
  yaş kavramı zaten kullanıcı seçimiyle atlanır. `argparse` `--auto`'yu
  bağımsız kabul eder ama `_cmd_archive_all` sadece `--all` dallanmasında
  `age_days` bakar; tek görev yolu `--auto`'yu **yok sayar** (uyarı yok,
  gereksiz gürültü).
- [KARAR] Dry-run başlığında yaş bilgisi görünür (`adayları (auto, >7
  gün): N görev`) — kullanıcı hangi eşiğin uygulandığını hemen görür.
  `--auto` yokken başlık eskisi gibi (`adayları: N görev`) — 012
  regresyonu yok.
- [KARAR] `_iter_archive_candidates` yeni parametre **default=None**
  → 012 davranışı korundu; test suite dokunulmadan yeşil. Küçük
  refactor, geniş uyum.
- [KARAR] Cron/hook script'i **belge olarak** verildi (ship.md
  kullanım örneği), ATLAS-içi zamanlayıcı yazılmadı — sistem
  zamanlayıcıları yeterli, ayrı process yönetimi YAGNI.
- Kapsam: 1 modül düzenleme (cli.py: +_read_archive_age_env,
  _iter_archive_candidates age_days paramı, _cmd_archive_all --auto
  dallanma, parser --auto flag — ~25 sat), 1 test dosyası genişleme
  (+4 test). Toplam 444 test yeşil (440 → +4). mypy strict + ruff
  temiz. Artefaktlar `pipeline/tasks/017-archive-auto/`.

## 2026-07-29 (Görev 016 — ACP `tool_call` açık red)
- [KARAR] Agent tool_call'ı **sessizce yok saymak** yerine
  **açık red** — kullanıcı fake plan sonucu görmesin, yanlış
  ilerlemesin. Sessiz yok sayma sonsuz beklemeye veya boş cevaba
  yol açardı; her ikisi de zor debug'lanır.
- [KARAR] Tool_name'i mesaja koy — kullanıcı hangi tool'un
  istendiğini görsün (`agent tool_name='read_file' istedi`).
  Debug için altın; Görev 016.1'de hangi tool'ları desteklememiz
  gerektiğini önceliklendirmeye yardımcı.
- [KARAR] `tool_call_update` de red — tool sonucu güncellemesidir;
  agent tool başlattıysa update de gelir. İkisini birleştirdik ki
  kısmi tool-use vermeyelim.
- [KARAR] Diğer `sessionUpdate` türleri (bilinmeyen, ör. `plan_update`,
  `available_commands_update`) **sessizce atlanır** — ACP forward-
  compatible olmalı; agent yeni türler eklerse ATLAS kırılmasın.
  Yalnız `tool_call` (üye izin/güvenlik sorunu) ve `agent_message_chunk`
  (ana yol) özel işlem görür.
- Kapsam: 1 modül düzenleme (planner.py: _call_acp session/update
  dispatcher ~15 sat), 1 test dosyası genişleme (+3 test). Toplam
  440 test yeşil (437 → +3). mypy strict + ruff temiz. Artefaktlar
  `pipeline/tasks/016-acp-tool-reject/`.

## 2026-07-29 (Görev 015 — Anthropic prompt caching)
- [KARAR] `Goal.prompt_cache: bool = False` — 003.2 kalıbıyla
  simetrik, yeni alan son sırada + default'lu. Eski YAML'lar hiç
  değişmedi.
- [KARAR] Cache tek başına anlamsız — `llm_prompt is None` iken
  `prompt_cache=True` verilse bile system alanı **gövdeye eklenmez**.
  Kullanıcı yanlış YAML yazsa bile Anthropic API hata döndürmez;
  sessiz doğru davranış.
- [KARAR] Cache TTL **yalnız ephemeral** (5 dk) — `type: "1h"` YAGNI;
  ATLAS'ın plan turları saatlerce sürmez. 5 dk çoğu senaryoda tam.
- [KARAR] `_call_anthropic` `system` tipi `str | list[dict] | None` —
  aynı endpoint, tek yol. Fabrika seviyesinde form seçilir (bit veya
  liste), çağrı seviyesinde şeffaf iletim. `payload["system"] = system`
  Anthropic JSON serializer'ı halleder.
- [KARAR] claude/acp backend'ler alanı yok sayar — anthropic-özel
  optimizasyon; protokolleri farklı. `prompt_cache=True` claude'ta
  no-op (fatura değişmez ama hata da yok).
- [KARAR] Cache_control token indirim ücretlendirmesi bu görevde
  DIŞI — 013 `charge_tokens` şu an `input_tokens`+`output_tokens`
  tam sayarız; cache_read_input_tokens ayrı bir field. Görev 015.1
  ile ayrılır.
- Kapsam: 1 modül düzenleme (goals.py: +prompt_cache alan + load kolu),
  1 modül düzenleme (planner.py: _call_anthropic system tip
  genişletme + _anthropic_planner cache dallanma), 2 test dosyası
  genişleme (+7 test). Toplam 437 test yeşil (430 → +7). mypy strict
  + ruff temiz. Artefaktlar `pipeline/tasks/015-anthropic-cache/`.

## 2026-07-29 (Görev 014 — Retry jitter + Retry-After header)
- [KARAR] `RetryAfterError` **`LLMPlannerError` alt sınıfı** — LSP
  uyumlu; mevcut `except LLMPlannerError:` yakalamaları hâlâ
  çalışır. Attribute `retry_after_s: float` özel bilgi taşır;
  sarmalayıcı `isinstance` kontrolü ile ayırır.
- [KARAR] Header saniyesi verildiyse **jitter eklenmez** — sunucu
  ipucuna saygı. Alternatif "header + jitter" ilk bakışta sağlıklı
  görünse de "Retry-After 30 sn" derse 30 sn beklemek istenir,
  30.4 sn değil. Deterministik güven.
- [KARAR] Header parse **sadece int saniye** — Anthropic saniye
  kullanır; HTTP-Date formatı (RFC 7231) YAGNI. Parse hatası →
  normal `LLMPlannerError` (backoff'a düş).
- [KARAR] `ATLAS_LLM_JITTER` **default 0.0** (kapalı) — 008
  davranışı bit-uyumlu, mevcut testler `random.uniform`'u hiç
  çağırmadığı için pyright/coverage etkilenmedi. Jitter etkisi
  test tarafında `random.uniform` monkeypatch ile deterministik.
- [KARAR] `_parse_retry_after` `getattr(exc, "headers", None)` ile
  savunmalı — bazı monkeypatched HTTPError'lar headers=None döner;
  crash yerine None döner, backoff kullanılır.
- Kapsam: 1 modül düzenleme (planner.py: +RetryAfterError,
  +_read_jitter_env, +_parse_retry_after, HTTPError kolu, sarmalayıcı
  ~20 sat), 2 test dosyası genişleme (+11 test). Toplam 430 test
  yeşil (420 → +10). mypy strict + ruff temiz. Artefaktlar
  `pipeline/tasks/014-retry-jitter-header/`.

## 2026-07-29 (Görev 010.1 — claude subprocess `--append-system-prompt`)
- [KARAR] `goal.llm_prompt` claude subprocess'e **argv** üzerinden
  `--append-system-prompt <text>` argümanı olarak geçer; gövde
  `include_system=False` kalıbıyla üretilir (llm_prompt stdin'den
  atılır). Anthropic body.system alanıyla birebir simetri — üç backend
  (claude / anthropic / [acp bekliyor]) aynı prensiple sistem rolünü
  gövdeden ayırıyor.
- [KARAR] `--append-system-prompt` yerine `--system` yok — Claude Code
  CLI native argümanı `--append-system-prompt`. Simetri açısında
  argüman adı önemli değil; işlev aynı.
- [KARAR] Argv geçişi (`shlex` splitting'e ihtiyaç yok) — `system`
  string tek bir positional argüman olarak subprocess'e gönderilir;
  `shell=False` şart, boşluk/quote sorunu yok. Windows uyumu (CVE-2024-4030
  kalıbı) korundu.
- [KARAR] SPEC 003.2 kalıbının test uygulaması güncellendi:
  `test_003_2_ozel_prompt_claude_stdin_de_gorunur` → `test_010_1_ozel_prompt_claude_argv_de_gorunur`.
  llm_prompt semantiği aynı (kullanıcı sistem rolü), yalnız iletim
  kanalı stdin → argv değişti; kullanıcı YAML'da değişiklik yok.
- Kapsam: 1 modül düzenleme (planner.py: _call_claude system keyword,
  _claude_planner include_system=False + system bind — ~15 sat),
  1 test dosyası düzenleme (003.2 testi 010.1 kalıbına dönüşüm +
  1 yeni test). Toplam 420 test yeşil (419 → +1 net). mypy strict +
  ruff temiz. Artefaktlar `pipeline/tasks/010-1-claude-system-arg/`.

## 2026-07-29 (Görev 013 — CallBudget'a token maliyeti entegrasyonu)
- [KARAR] `charge_tokens` **ayrı method** — `charge()` sözleşmesi
  dokunulmadı. Ayrı yol, "token akışını takip et ama kredi denklemini
  bozma" ilkesini korur. Aynı `spent` alanı biriktirir; run_loop
  görünür değil (mevcut budget.charge çağrısı aynen çalışır).
- [KARAR] Callback stili (`on_usage: Callable[[int,int], None] | None`)
  seçildi — planner sözleşmesi (`(str, list) -> str`) genişletilmedi.
  Alternatif ("planner tuple döndürsün") her çağrı yerini kırardı.
  Fabrika-seviyesi bind (`_anthropic_planner(..., on_usage=budget.
  charge_tokens)`) test yalıtımını temiz tutar.
- [KARAR] Fiyat 0/negatif → **no-op** (011 fail-safe kalıbı). Env
  yoksa/hatalıysa `_read_llm_prices()` `(0.0, 0.0)` döner; `charge_tokens`
  cost hesaplamaz, bütçe hiç değişmez. Geriye uyumluluk garantisi:
  fiyat set edilmemiş kurulumlar hâlâ Görev 002+003 gibi çalışır.
- [KARAR] `_extract_usage(data)` yardımcısı 011 trace ve 013 charge
  arasında paylaşıldı — usage parse tek yerde, ikizleşme yok.
- [KARAR] BudgetExceededError callback'ten **saracak yok** — planner
  yakalar ama `LLMPlannerError`'a çevirmez, olduğu gibi run_loop
  yukarısına iletir. run_loop `except` bloklarında BudgetExceededError
  zaten normal karşılanır (SPEC 002 exit 3). Callback throw = plan
  başarılıydı ama bütçe dolu — semantik doğru.
- [KARAR] claude/acp backend'ler `on_usage` parametresini **yok sayar**
  (make_planner sadece anthropic dallanmasına iletir). Protokoller
  native usage taşımıyor; kapsam DIŞI.
- Kapsam: 1 modül düzenleme (core.py CallBudget +25 sat), 1 modül
  düzenleme (planner.py +25 sat: _extract_usage, callback), 1 CLI
  düzenleme (+15 sat: _read_llm_prices, on_usage bind). 1 yeni test
  dosyası (9 test), 1 backend test dosyası genişleme (+3 test).
  Toplam 419 test yeşil (407 → +12). mypy strict + ruff temiz.
  Artefaktlar `pipeline/tasks/013-callbudget-tokens/`.

## 2026-07-29 (Görev 012 — atlas archive --all toplu arşivleme)
- [KARAR] Aday seçimi `pipeline/tasks/*/09-ship.md` glob — SHIP aşaması
  geçmiş görevler zaten "arşive uygun" gate'ini geçmiş demektir. `00-need`
  yeter mi? Hayır — çünkü ihtiyaç yazılmış ama görev bitmemiş olabilir.
  09-ship SPEC tarafından zaten yazılıyor (pipeline gate); doğal filtre.
- [KARAR] **Çift kapı (`--apply --yes`)**: toplu yıkıcı işlem, tekil
  yıkıcı işlemin **iki katı sonuç doğurur** — bir yanlış çağrı
  10 klasörü birden siler. Tek bir onay bayrağı (`--apply`) mevcut
  disipline ters düşmese de, çoklu yıkıcı için kullanıcı **niyetini
  bir kez daha söyler**. `--yes` verilmezse exit 2 (SPEC hatası
  ile aynı — CLAUDE.md "onay iste" kuralı).
- [KARAR] **Fail-fast**: ilk hata → dur. Alternatif "hepsini dene,
  hataları raporla" idi; ancak fail-fast diski ve audit'i temiz tutar
  (kısmi başarılar açık, arka arkaya 10 hata değil). Kullanıcı hatayı
  çözüp tekrar çalıştırır — kalan görevler henüz duruyor.
- [KARAR] Rapor sözleşmesi: `arşivlendi: N/M görev` + `başarılı: ...`
  + `başarısız: <task> — <mesaj>` (stderr) + `atlanan: ...`. Tek
  ekranda kısmi başarı + hangi görevlerin hâlâ beklediği görünür.
- [KARAR] Exit kodu YENİ değil — 2 (SPEC: --yes yok, kök dizin yok)
  ve 6 (arşiv hatası, fail-fast). Kullanıcı tek tablo öğrenir.
- [KARAR] Positional `task` `nargs="?"` — `--all` verilirse sessizce
  yok sayılır; verilmezse eskisi gibi zorunlu (yeni SPEC HATASI mesajı
  `<task> ya da --all zorunlu`). SPEC 007 mevcut testleri hiç değişmeden
  yeşil kaldı.
- Kapsam: 1 modül genişleme (cli.py — +_cmd_archive_all,
  +_iter_archive_candidates, dallanma), 1 test dosyası genişleme (+5 test).
  Toplam 407 test yeşil (402 → +5). coverage %93.69. mypy strict +
  ruff + scan temiz. Artefaktlar `pipeline/tasks/012-archive-all/`.

## 2026-07-29 (Görev 011 — Token cost, report-only)
- [KARAR] Kapsam **report-only** — CallBudget'a token yansıması YOK.
  Soyut kredi modeli 003+002'den beri stabil; onu kırmak Görev 013'ün
  işi. Bu görev sadece "kullanıcı ne kadar yakıyor?" sorusunu görünür
  kılar.
- [KARAR] `ATLAS_LLM_TRACE=1` env'i Görev 008 retry trace'iyle
  **paylaşılır**. Tek env ile hem retry hem usage görünür; kullanıcı
  ayrı bayrak yönetmez. Kapalıysa sıfır yan-etki (`_emit_...` yalın
  return, yalnız kısa dict lookup).
- [KARAR] Fiyat env'leri `ATLAS_LLM_PRICE_IN`/`ATLAS_LLM_PRICE_OUT`
  **per million token, USD**. Parse hatası → `cost≈?` (fail-safe).
  Model-specific sabit tablo eklemedik — Anthropic modelleri değişken
  (aylık fiyat değişimi yaygın); env kullanıcının kontrolünde daha
  esnek. Model-özel default tablo Görev 013+.
- [KARAR] claude/acp backend'ler **usage yayınlamaz** — claude subprocess
  cevap gövdesinde token bilgisi yok, ACP protokolü native usage
  taşımıyor. Şu an ertelendi; ACP genişleyince tekrar bakılır.
- [KARAR] Trace format: `[llm] anthropic tokens: in=N out=N cost≈$X.XXXX`
  — retry trace'i `[retry] ...` prefix'iyle simetrik. Grep/awk ile
  ayrıştırma kolay.
- Kapsam: 1 modül genişleme (planner.py +30 sat: 2 yeni yardımcı),
  1 test dosyası genişleme (+5 test). Toplam 402 test yeşil (397 → +5).
  mypy strict + ruff temiz. Artefaktlar `pipeline/tasks/011-token-cost/`.

## 2026-07-29 (Görev 010 — Anthropic system rolü ayrımı)
- [KARAR] `goal.llm_prompt` **anthropic** backend request gövdesinin
  `system` üst-düzey alanına gider; `messages[0].content` sadece
  ATLAS'ın plan sözleşmesi + görev + context + gözlem taşır. Model
  system'i user'dan **daha güçlü** izler → kullanıcı persona kilidi
  gerçekten kilit gibi çalışır.
- [KARAR] `_format_prompt`'a `include_system: bool = True` **keyword-only**
  parametre; anthropic backend `False` geçirerek llm_prompt'un
  messages gövdesinde tekrarlanmasını engeller. Diğer backend'ler
  değişmez (varsayılan). Sözleşme kırılmadı.
- [KARAR] claude ve acp backend'lerinde llm_prompt **prepend** kalıbı
  korundu — bu backend'lerin protokollerinde system rolü ayrımı yok
  ya da farklı (claude subprocess `--system` argümanı ve ACP session-level
  prompt sonraki görevlerde).
- [KARAR] `_call_anthropic`'e `system: str | None = None` keyword-only;
  None/boş → payload'a alan **hiç eklenmez** (temiz body, Anthropic
  tolerate etse bile). `goal.llm_prompt or None` bind edilir — boş
  string falsy düşer.
- Kapsam: 1 modül düzenleme (planner.py — 3 fonksiyon), 1 test dosyası
  düzenleme (003.2 anthropic testi 010 kalıbına dönüşüm + 2 yeni test).
  Toplam 397 test yeşil (395 → +2 net). mypy strict + ruff temiz.
  Artefaktlar `pipeline/tasks/010-anthropic-system-role/`.

## 2026-07-29 (Görev 009 — Goal.llm_model opsiyonel alanı)
- [KARAR] `Goal.llm_model: str | None = None` — 003.2 llm_prompt kalıbı
  birebir taşındı: son sırada + default'lu, boş string → None sessiz
  fallback, tip yanlış → SpecError. Eski YAML'lar hiç değişmedi.
- [KARAR] Model öncelik zinciri anthropic backend'inde:
  `goal.llm_model` > `ATLAS_LLM_MODEL` env > `_DEFAULT_ANTHROPIC_MODEL`
  sabiti. `_resolve_anthropic_env(goal=None)` opsiyonel goal alır;
  `None` verilirse davranış eskisiyle aynı.
- [KARAR] claude/acp backend'ler alanı **yok sayar** — kapsam DIŞI.
  claude subprocess `--model` argümanı Görev 010+; ACP protokolü
  model bildirimini agent'ın kendi yapılandırmasına bırakır.
- [KARAR] Model listesi doğrulaması YOK — Anthropic modelleri
  değişken; env yolu zaten bir emniyet supabı. Kullanıcı bilmeyen
  model verirse API 400 döner, `LLMPlannerError` üzerinden görünür.
- Kapsam: 1 modül düzenleme (goals.py — +llm_model + load kolu),
  1 modül düzenleme (planner.py — _resolve_anthropic_env(goal)),
  1 test dosyası genişleme (+5 test), 1 backend test dosyası
  genişleme (+3 test). Toplam 395 test yeşil (387 → +8). mypy strict
  + ruff temiz. Artefaktlar `pipeline/tasks/009-llm-model/`.

## 2026-07-29 (Görev 008 — LLM retry/backoff sarmalayıcı)
- [KARAR] Retry mantığı planner'ın **dışında** — `make_retrying_planner`
  ayrı fabrikadır, `make_planner` sözleşmesi hiç değişmedi. Böylece
  static planner, stub planner, üç LLM backend ve gelecek backend'ler
  aynı sarmalayıcıyı ücretsiz kullanır; test yalıtımı temiz.
- [KARAR] `retries <= 0` → `inner` **aynen** döner (`is inner`
  kimlik-geçiş). Bu, "env kapalıysa hiç maliyet yok" garantisi verir
  ve mevcut test suite bit-uyumlu kalır.
- [KARAR] Sadece `LLMPlannerError` yakalanır; `PlannerExhaustedError`,
  `KeyboardInterrupt`, `ValueError` sarma **geçer**. LLM'in "geçici"
  hatasıyla static planner'ın "tükendi" durumu farklı sözleşmedir —
  ikincisi retry ile düzelmez.
- [KARAR] `time.sleep` yerine `planner_mod._sleep` modül-seviyesi
  hook. Test tarafı `monkeypatch.setattr(planner_mod, "_sleep", ...)`
  ile uykuları anında geçer. Alternatif: `time.sleep` doğrudan
  patch'lemek → hangisi sarmalayıcı için ise belirsizlik. Modül
  hook'u niyeti açıklar.
- [KARAR] Env sözleşmesi: `ATLAS_LLM_RETRIES` (0 = kapalı),
  `ATLAS_LLM_BACKOFF` (saniye taban), `ATLAS_LLM_TRACE` (`1` →
  stderr). Negatif retry/backoff **sessizce 0'a düşürülür** —
  kullanıcı env'i yanlış yazsa bug yerine kapalı kalır.
- Kapsam: 1 modül düzenleme (planner.py +45 sat), 1 CLI düzenleme
  (2 sat), 1 yeni test dosyası (15 test), 1 CLI test ekleme.
  387 test yeşil (371 → +16). mypy strict + ruff temiz.
  Artefaktlar `pipeline/tasks/008-retry-backoff/`.

## 2026-07-29 (Flaky düzeltmesi — test_doctor_gui mtime granülerliği)
- [HATA] `test_restore_defaults_to_newest_and_can_pick_by_name`: iki
  yedek aynı Windows sistem-saati tick'i (~15.6 ms) içine düşünce
  `Path.stat().st_mtime` (float saniye) beraberliği "en yeni"yi
  belirsizleştiriyordu. `list_backups`'ın sort'u `key=st_mtime, reverse=True`
  idi; beraberlikte sıralama Python `sort` stabilliğine ve `iterdir()`
  dönüş sırasına bırakılıyordu — Windows FS bunda belirlenimci değil.
- [KARAR] `list_backups` sort anahtarı `(st_mtime_ns, name)` desc'e
  yükseltildi: `_ns` NTFS 100 ns hassasiyet verir; kalan çok nadir
  beraberlikte klasör adı (versiyon etiketli) tiebreaker olur —
  `juggler-backup-v0.5.0` > `juggler-backup-v0.4.2` lexicographic
  desc → "yeni sürüm önce" hem yaygın hem beklenen.
- [KARAR] Regresyon savunması: `test_list_backups_ayni_mtime_de_deterministik`
  iki yedeğin `st_mtime_ns`'sini `os.utime(..., ns=(c, c))` ile
  **zorla eşitleyip** sıralamanın 10 çağrı boyunca belirlenimci
  kaldığını doğruluyor. Beraberlik senaryosunu artık gerçek Windows
  tick'ine bırakmıyoruz.
- Kapsam: 1 modül düzenleme (`tools/doctor_gui/checks.py::list_backups`
  — sort anahtarı + `mtime_ns` alanı), 1 test dosyası genişleme
  (+1 test). Toplam 371 test yeşil, mypy strict + ruff temiz.
  Flaky retry gereksinimi kalktı.

## 2026-07-29 (Görev 007 — atlas archive CLI komutu)
- [KARAR] Yıkıcı işlem **dry-run varsayılan**; `--apply` bilinçli seçim.
  CLAUDE.md kuralı ("yıkıcı işlem öncesi onay iste") CLI yüzeyinde
  varsayılan davranışa gömüldü.
- [KARAR] Özet öncelik zinciri: `--summary` argümanı → `09-ship.md`'nin
  ilk paragrafı → fallback `"<task> arşivlendi"`. SHIP aşaması pipeline
  gate'i gereği zaten yazılmış olduğundan doğal kaynak; `_read_ship_summary`
  H1 satırlarını atlar ve ilk boş-satır'da keser.
- [KARAR] Yeni exit kodu YOK. `SPEC HATASI` (klasör yok) → mevcut 2;
  arşiv/tarfile/vault hatası → mevcut 6 (workflow-handler ile aynı
  semantik: "arşiv işi kırıldı"). Kullanıcıya iki koddan seçim yaptırmadık.
- [KARAR] Audit sözleşmesi: `--apply` başarılı → `("atlas-archive",
  "archive", "<task>")`; hata → `("atlas-archive", "error", "<mesaj>")`.
  Dry-run **audit'e yazmaz** — yıkıcı olmadığı için gereksiz gürültü.
- [KARAR] `--tasks-root` ve `--archive-root` override argümanları
  eklendi. Sadece test için değil; portable kurulumlarda `pipeline/tasks`
  farklı bir yolda olabilir. Varsayılanlar CLAUDE.md ile uyumlu.
- Kapsam: 1 modül düzenleme (cli.py — +_cmd_archive + _read_ship_summary
  + parser), 1 test dosyası genişleme (+6 test). Toplam 370 test yeşil,
  coverage %93.44, mypy strict + ruff temiz. Artefaktlar
  `pipeline/tasks/007-archive-cli/`.

## 2026-07-29 (Görev 003.2 — Goal.llm_prompt opsiyonel alanı)
- [KARAR] `Goal.llm_prompt: str | None = None` — SPEC 006 kalıbı:
  yeni alan **son sırada + default'lu**; eski `Goal(...)` positional
  çağrıları ve eski YAML'lar hiç değişmeden çalışır.
- [KARAR] Boş string (`""`) → `None` — kullanıcı yanlışlıkla
  `llm_prompt:` yazıp değer vermezse veya `""` bırakırsa **sessiz
  fallback**. SpecError patlatmıyoruz çünkü kullanıcı niyeti belirsiz
  ve mevcut sabit prompt her zaman iş görür.
- [KARAR] Prompt sıralaması: kullanıcı promptu **başta**, ATLAS'ın plan
  sözleşmesi (verbs + biçim + "TEK SATIRLIK yaz" direktifi) **sonda**.
  Kullanıcı sistem rolünü tanımlarken çıktı sözleşmesini bozamasın —
  LLM sonda gördüğü direktifi daha güçlü izler.
- [KARAR] Merkezî değişiklik `_format_prompt`'ta; üç backend (claude,
  anthropic, acp) yeniden derlenmeden aynı davranır. Test tarafında
  her backend için ayrı doğrulama (`dataclasses.replace(goal,
  llm_prompt=...)`) — üç kanal da özel promptu ilettiğini gösteriyor.
- [KARAR] Rol ayrımı (system vs user, anthropic API'de) **ertelendi**
  (Görev 010+). Şu an tek "user" mesajı yeter; sistem promptu YAML
  kullanıcısından tek gövde olarak akıyor. Anthropic'te bu yaklaşım
  "assistant persona" için çalışır ama tam sistem-rol kilidi vermez.
- Kapsam: 2 modül düzenleme, 4 test dosyası genişleme (+9 test),
  1 YAML fixture. Toplam 364 test yeşil, coverage %90 üstü, mypy
  strict + ruff temiz. Artefaktlar `pipeline/tasks/003-2-llm-prompt/`.

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
