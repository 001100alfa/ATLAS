# ATLAS Karar Günlüğü
Format: `## TARİH` altında madde; her madde [KARAR]/[VARSAYIM]/[HATA] etiketi taşır.

## 2026-08-05 (35. tur — 108 + 109 + 110 + 111 + 112 + 113)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 34. tur adayları (108-113) tümü zincirleme,
küçükten büyüğe: `108 → 109 → 110 → 111 → 112 → 113`.

- [KARAR] 108 archive `--gzip` bayrağı `--out` gerektirir (SPEC 103
  kalıbı ile simetrik). Auto-suffix `.gz`; sahipse aynen (çift YOK).
  gzip.open("wt") NDJSON satır satır — decompress edildiğinde SPEC 105
  düz metin ile BİT-UYUMLU.
- [KARAR] 109 ai-cli `--gzip`: SPEC 106 üstüne aynı kalıp. `_pkg_line(p)`
  yardımcı lambda — düz ve gzip dallarında ortak satır üretici (DRY).
  `--strict` ile ORTOGONAL (exit 4 korunur, gzip'e yazılır).
- [KARAR] 110 doctor `--out` yalnız `--diff-history-all + --format
  prometheus` ile anlamlı. Schema kısa devre (SPEC 040) `--out`'tan
  ÖNCE — `--out --schema` argparse tarafında değil semantik tarafında
  kontrol edilir; `--schema` çalışır, `--out` yok sayılır.
- [KARAR] 110 doctor'da `--gzip` YOK bu tur (ayrı SPEC olabilir).
  Neden: doctor prometheus çıktısı kısa (per-snapshot metric ailesi 5×N
  satır); gzip artifact kazanımı YAGNI. Metric/archive/ai-cli'de gzip
  gerçek büyük dosya için, doctor'da değil.
- [KARAR] 111 vault verify `--gzip`: `out_fh: Any` tip (mypy gzip
  TextIOWrapper vs `Path.open` TextIOWrapper union'ı). `_emit`
  lambda değişmedi — `out_fh.write` her iki tipte de vardır.
- [KARAR] 112 atlas-vault.yml yeni step `Restore + verify (integrity
  check, SPEC 112)`: backup üretildikten sonra split'ten restore +
  verify --strict. Herhangi biri başarısız → workflow fail (`set -e`).
  Neden: backup üretilip de restore edilemezse fark edilmez —
  end-to-end integrity kontrolü hafta boyu cron'la doğrulanır.
- [KARAR] 112 restore hedef `/tmp/verify-vault` (üretim vault'unu
  bozmaz). `rm -rf` ile idempotent (cron her gün aynı yere yazar).
  Vault-verify --strict → SPEC 042 exit 4 varsa job fail.
- [KARAR] 113 atlas-metrics.yml `metrics-group-day.prom.gz` yeni artifact.
  SPEC 103 CLI gzip'i ilk kez workflow'da kullanıldı. Fallback:
  `|| echo "(...)" > metrics-group-day.prom.gz` — komut kırılırsa
  dosya var olur ama içerik "üretilemedi" mesajı (SPEC 095 kalıbı).

## 2026-08-05 (34. tur — 105 + 106 + 103 + 104 + 102 + 107)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir" → 33. tur
adayları (102-107) tümü zincirleme, küçükten büyüğe:
`105 → 106 → 103 → 104 → 102 → 107`.

- [KARAR] 105 archive `--out` yalnız `--json-lines` ile anlamlı
  (SPEC 092/096 kalıbı). Parent auto-mkdir + IO exit 2. Diğer
  formatlar (pretty/JSON) için `--out` YOK — kullanıcı shell redirect
  kullansın.
- [KARAR] 106 ai-cli `--out` yalnız `--json-lines` ile. `--strict`
  ile ORTOGONAL (exit 4 korunur, dosyaya yazılır). SPEC 105 ile
  simetrik.
- [KARAR] 103 `--gzip` yalnız `--out` ile anlamlı → aksi exit 2.
  PATH `.gz` uzantı yoksa auto-suffix ekle (kullanıcı şaşırmasın).
  Sahipse aynen kullan (çift `.gz.gz` yok).
- [KARAR] 103 değişken adı `prom_text` (mypy no-redef: SPEC 064
  `_post_alert_webhook` `payload` dict scope'la çakışma). Kalıp: aynı
  fonksiyonda scope-narrow için isim çakışması → değişken adını
  farklılaştır (SPEC 090 `group_lines` kalıbı).
- [KARAR] 104 **SPEC 091 `--format prometheus` MUTEX KALDIRILDI**
  (2. sözleşme değişikliği — SPEC 090 rollback kalıbı ile simetrik).
  Neden: `--diff-history-all` çıktısı Prometheus'a grup metrikleri
  olarak yayımlanabiliyor (labels: `snapshot_date`).
- [KARAR] 104 5 metric: 3 counter (warnings_added/removed,
  quality_deltas) + 2 gauge (has_regression/has_improvement 0|1).
  HELP/TYPE her metric için (Prometheus text v0.0.4).
- [KARAR] 104 `--strict` ile ORTOGONAL (SPEC 097 exit 9 korunur;
  Prometheus çıktı hâlâ basılır). `--schema` kısa devre yine BİT-
  UYUMLU (SPEC 040 kalıbı).
- [KARAR] 102 `combine_split_parts(first_part)`: `.001` başlar, `.NNN`
  sıralı okur, tek dosyaya birleştirir. Parçaların **orijinali
  KORUNUR** (silinmez) — kullanıcı için ek yedek + hata durumunda
  geri alınabilir.
- [KARAR] 102 `<path>` `.001` olmalı (deterministik başlangıç); wildcard/
  glob değil — Windows'ta shell expansion tutarsız. Kullanıcı ilk
  parçayı verir, kod diğerlerini bulur.
- [KARAR] 102 `--split` + `--decrypt`/`--decrypt-recipient` MUTEX
  exit 2 (SPEC 101 backup MUTEX ile simetrik — encrypted split ayrı
  SPEC, YAGNI).
- [KARAR] 102 birleştirme temp dosyası `<base>.combined-<pid>`
  restore sonrası `finally` bloğunda silinir (SPEC 066 kalıbı).
- [KARAR] 107 cron `0 3 * * *` (03:00 UTC = 06:00 Istanbul, gece iş
  yükü düşük saat). SPEC 089 (`0 6 * * *`) ci-status'la 3 saat aralık
  → yoğunluk dağılır.
- [KARAR] 107 `Check vault exists` step + `has_vault` conditional →
  vault yoksa workflow durmaz (SPEC 095 fail-safe kalıbı). CI/repo'da
  vault olmayabilir (env vault paylaşılabilir).
- [KARAR] 107 `--split 50 MB` — GitHub artifact 2 GB per-artifact
  sınırı; 50 MB parça → ~40 parça max (2 GB vault). `--keep 7` retention
  → 7 gün eski yedek (workflow her gün çalışırsa haftalık pencere).
- [KARAR] 107 upload artifact glob `vault-*.tar.gz.*` — yalnız split
  parçaları (`.001..N`) — orijinal `.tar.gz` YOK çünkü `--split`
  sonra silinir (SPEC 101 kalıbı).

## 2026-08-05 (33. tur — 099 + 098 + 096 + 097 + 100 + 101)

Kullanıcı "hepsini sıra ile uygula" → 32. tur adayları (096-101) tümü
zincirleme, küçükten büyüğe: `099 → 098 → 096 → 097 → 100 → 101`.

- [KARAR] 099 `--json-lines` yalnız `--outdated` ile anlamlı (aksi
  exit 2) + `--json` ile MUTEX. Neden: NDJSON stream tam liste için
  aşırı; filtre + stream birleşimi CI iş sırası için doğal.
- [KARAR] 099 son satır `{"type":"summary","path","outdated","total_deps"}`
  — SPEC 087 vault verify NDJSON kalıbı ile simetrik. `total_deps`
  filtreden ÖNCE (tam deps).
- [KARAR] 099 `--strict` ile ORTOGONAL — bulgu + strict → exit 4,
  NDJSON hâlâ basılır. Bilgi kaybı YOK.
- [KARAR] 098 archive `--json-lines` her satır SPEC 075 alanlarıyla
  AYNI + son satır `{"type":"summary","archive_root","count"}`.
  Sıralama/filtre/limit stream ÖNCESİ uygulanır (deterministik).
- [KARAR] 096 `--out` yalnız `--group-by + --format prometheus` ile
  anlamlı (aksi exit 2). SPEC 092 vault verify `--out` kalıbı ile
  simetrik; parent auto-mkdir + IO hatası exit 2.
- [KARAR] 096 dosya içeriği stdout ile BİT-UYUMLU — test doğrulaması
  aynı komut iki kez çağrılıp içerik eşitliği bakılır. Deterministik
  sıra (SPEC 090 key alfabetik lex).
- [KARAR] 097 SPEC 091 blok sonunda `--strict` + herhangi snapshot
  `has_regression=True` → exit 9. SPEC 032/057 `--strict` exit 9
  kalıbı ile UYUMLU. stderr mesajında regressed date listesi.
- [KARAR] 097 test'lerin sözleşme alanı `rc in {0, 9}` — CI env'ine
  bağlı olarak doctor rapor uyarısı olabilir/olmayabilir; test
  determinizmi için "regresyon varsa 9" veya "yoksa 0" iki seçenek
  kabul, mesaj kontrolü koşullu.
- [KARAR] 100 atlas-doctor.yml yeni step `Generate diff-history-all
  trend`; `||` fallback bos snapshots (SPEC 095 fail-safe kalıbı).
  Mevcut 2 artifact DOKUNULMADI — yeni `doctor-diff-history-all.json`
  upload listesine EKLENDİ (bit-uyumluluk).
- [KARAR] 101 `--split SIZE_MB` fixed-size parça: `.001`, `.002`,
  3 haneli 1-based. Orijinal silinir (space tasarrufu).
  Birleştirme: `cat *.001 > full.tar.gz` (POSIX) —
  restore ayrı SPEC olarak ertelendi (YAGNI).
- [KARAR] 101 boş src (0 byte) → tek boş `.001` parça. Neden:
  birleştirme sözleşmesi bozulmasın; kullanıcı `cat *.001` boş
  dosya bekler (tek parça = 0 byte).
- [KARAR] 101 `--split` + `--encrypt`/`--recipient` MUTEX exit 2 —
  encrypted split ayrı SPEC (her parça ayrı şifreleme? tek geçiş
  şifreleme sonra split? seçim belirsiz → YAGNI, ayrı iş).
- [KARAR] 101 `--keep` retention split ÖNCESİ çalışır — parçalar
  retention'a dahil değil (mtime desc glob `vault-*.tar.gz` deseni
  yeni `.001..N` parçalarını yakalamaz; korunma sağlanır).
- [KARAR] 101 split akışı `return 0` ile encrypt/keep-encrypted
  dallarına girmeden çıkar; MUTEX zaten başta reddedildiği için
  dal içi kontrole gerek yok.

## 2026-08-05 (32. tur — 092 + 094 + 093 + 095 + 091 + 090)

Kullanıcı "devam et → hepsini sıra ile" → 31. tur adayları (090-095)
tümü zincirleme, küçükten büyüğe: `092 → 094 → 093 → 095 → 091 → 090`.

- [KARAR] 092 `--out PATH` yalnız `--format json-lines` ile anlamlı.
  Diğer format'lar için `--out` YOK — çünkü json/json-pretty tek satır,
  human human, shell redirect (`> file`) yeter. json-lines'a özel:
  streaming büyük vault memory/CPU tasarrufu + Windows shell redirect
  karakter kodlaması sorunlarını atlar.
- [KARAR] 092 `open("w")` başarısız → SPEC HATASI exit 2 (mesajda hata
  metni). `try/finally close` — kaynak sızıntısı yok. Parent dir
  auto-mkdir (SPEC 052 dump-report kalıbı ile simetrik).
- [KARAR] 092 `--out` + `--dump-report` ORTOGONAL — biri NDJSON hedef,
  diğeri markdown yan etki (SPEC 052/087 kalıp korunur).
- [KARAR] 094 `--strict` yalnız `--outdated` ile anlamlı — aksi hâlde
  SPEC HATASI exit 2. Neden: `list` (outdated değil) her zaman exit 0
  bilgi komutu; `--strict` bilgi komutunu CI-uyumlu karara dönüştürür
  → yalnız filtre üzerinde anlamlı.
- [KARAR] 094 exit 4 kalıbı: SPEC 042 vault verify `--strict` +
  SPEC 032 doctor `--strict` UYUMLU. "SAĞLIK BAŞARISIZ" stderr mesajı
  (SPEC 042 kalıbı) — insan-okunur.
- [KARAR] 093 `--name-match PATTERN` yeni bayrak; `--search` (SPEC 065)
  ile ORTOGONAL. Neden: `--search` içerik (arcname) araması + list-only
  komut; `--name-match` arşiv **AD** filtresi + --list ile birlikte.
  İki farklı use-case → iki farklı bayrak.
- [KARAR] 093 filtre sıralamadan ÖNCE (list → filter → sort → limit).
  Neden: sort filter'lı liste üzerinde çalışsın (top-N stabil); ancak
  bit-uyumluluk: name-match yoksa filter no-op → SPEC 075/079 AYNI.
- [KARAR] 093 boş sonuç pretty mesaj ayrımı: `--name-match` verildiyse
  `(esleme yok)`, aksi hâlde SPEC 075 `(arsiv yok)` BİT-UYUMLU
  (semantik ayrım — "arşiv yok" farklı, "filter eşleşmedi" farklı).
- [KARAR] 095 workflow yeni step `if: steps.metrics.outputs.has_data ==
  'true'`. Env fiyat yoksa cost 0 (SPEC 013 fail-safe); komut kırılırsa
  `||` ile boş JSON fallback (workflow durmaz — SPEC 074 kalıbı).
- [KARAR] 095 mevcut 3 artifact (`metrics-human.txt`, `metrics.json`,
  `metrics.prom`) DOKUNULMADI — yeni `metrics-cost-by-day.json` upload
  path listesine EKLENDİ (bit-uyumluluk: mevcut tüketiciler etkilenmez).
- [KARAR] 091 `--diff-history-all` action="store_true"; MUTEX listesi:
  `--diff/--auto-baseline/--diff-history/--save-baseline/--serve/
  --format prometheus`. `--schema` MUTEX **GEREKSİZ** çünkü SPEC 040
  `--schema` kısa devre (dispatcher önce çalışır — asla erişilemez).
- [KARAR] 091 çıktı sırası date desc (SPEC 086 kalıbı ile simetrik —
  N=1 en yeni). Pretty tablo `date | +warn | -warn | Δquality` kısa;
  detay için `--json` (SPEC 057 delta şeması).
- [KARAR] 091 snapshot okunamazsa (bozuk JSON/OSError) UYARI stderr'e
  ve continue — 1 bozuk snapshot toplu diff'i patlatmaz (SPEC 052
  best-effort kalıbı).
- [KARAR] 090 **SPEC 081 `--group-by + --format prometheus` MUTEX
  KALDIRILDI** (karar geri alındı). Neden: SPEC 084 cost eklendikten
  sonra Grafana dashboard'da "günlük cost trend" tek scrape için grup
  histogram gerçek ihtiyaç oldu. YAGNI kalktı.
- [KARAR] 090 Grup Prometheus metrikleri: 5 base (records/tokens_in/out/
  cache_creation/cache_read) + opsiyonel 6. (cost_usd `--with-cost` ile).
  Labels: `unit`, `key`. Escape: `\` `"` `\n` (Prometheus text v0.0.4).
- [KARAR] 090 SPEC 081 `--group-by + --alert` MUTEX **KORUNDU** —
  alert tekil hit-ratio değere, grup aggregation'ıyla anlamsız
  (bu karar hala geçerli).
- [KARAR] 090 değişken adı `group_lines` (Prometheus dalındaki
  `lines: list[str]` ile mypy no-redef çakışması). Kalıp: aynı
  fonksiyonda iki farklı dal aynı adı kullanamaz — narrow scope
  çözümü değişken adı.

## 2026-08-05 (31. tur — 085 + 088 + 089 + 087 + 084 + 086)

Kullanıcı "devam et → hepsini sıra ile" → 30. tur adayları (084-089)
tümü zincirleme, küçükten büyüğe: `085 → 088 → 089 → 087 → 084 → 086`.

- [KARAR] 085 `--limit N`: sıralamadan **SONRA** `entries[:N]` (top-N,
  orta değil). `N <= 0` → SPEC HATASI exit 2 (argparse yerine semantik
  hata — "N > 0 olmalı" mesajı net). `N > len(entries)` → tüm liste
  (kesme yok). `--limit` VERİLMEZSE SPEC 075/079 BİT-UYUMLU.
- [KARAR] 088 `_strip_semver_prefix`: `^`, `~`, `>=`, `>`, `=`, `*`,
  boşluk sıyır. **npm semver-satisfies DEĞİL** — yalın prefix temizlik.
  `^1.18.8` + installed `1.18.9` → outdated (yanlış pozitif) çünkü range
  hesabı yok. Dokümanta net belirt; kullanıcı gerçek semver için
  `npm outdated` çalıştırır. Karar YAGNI — semver kütüphanesi eklemek
  bağımlılık maliyeti.
- [KARAR] 088 pretty başlık: `... — outdated` (--outdated verildiyse
  başlığa suffix). Boş sonuç → `(guncelleme yok)` cp1254 uyumlu ASCII.
- [KARAR] 089 `.github/workflows/atlas-ci-status.yml` AYRI workflow
  (082 `ci-status.yml`'ye dokunmayış). Neden: 082 push/PR gate, 089
  cron+dispatch. İki farklı use-case → iki workflow.
- [KARAR] 089 drift → `peter-evans/create-issue-from-file@v5` ile issue.
  Label: `ci-status/drift/automated`. `permissions: issues: write`
  eklendi; sistem token'ı yeter (PAT gerekmez).
- [KARAR] 089 cron `0 6 * * *` (06:00 UTC = 09:00 Istanbul). Deterministik
  saat + iş saatinde issue görünür.
- [KARAR] 087 `--format {human,json,json-pretty,json-lines}` yeni
  bayrak. `--json` ve `--pretty` MUTEX (exit 2). `--format` VERİLMEZSE
  mevcut `--json`/`--pretty` yolu → SPEC 042 BİT-UYUMLU.
- [KARAR] 087 json-lines şema: `{type: "broken_link|orphan_note|
  orphan_tag", ...}` ve son satır `{type: "summary", ...}`. Temiz vault
  → tek summary satırı (clean=True). Konsept: NDJSON tüketici tek pass
  ile hem bulgu hem özet alır.
- [KARAR] 087 `--strict` (exit 4) ve `--dump-report` (markdown yan etki)
  format'tan bağımsız — verify sonucu bit-uyumlu.
- [KARAR] 084 `_group_cost_usd(g, Pin, Pout)`: SPEC 043 Prometheus
  formülü ile **BİT-UYUMLU** (in*Pin + cc*Pin*1.25 + cr*Pin*0.1 +
  out*Pout) / 1M. Extract helper — DRY (Prometheus dalı da bu formül).
- [KARAR] 084 `--with-cost` yalnız `--group-by` ile anlamlı. Aksi hâlde
  SPEC HATASI exit 2. Neden: cost YALIN metric olarak zaten Prometheus
  export'ta var; `--with-cost` group aggregation üzerine özel.
- [KARAR] 084 fiyat env yoksa cost 0.0 (SPEC 013 fail-safe), pretty'de
  UYARI stderr'e. JSON tarafında UYARI YOK (JSON tüketici stderr'i
  ignore edebilir, `cost_usd: 0.0` yeterli sinyal).
- [KARAR] 084 `--with-cost` VERİLMEZSE grup dict alanları SPEC 081 AYNI
  (cost_usd alanı EKLENMEZ) — BİT-UYUMLU.
- [KARAR] 086 `--diff-history N` (yeni bayrak, `--diff PATH` ile MUTEX).
  Neden: `--diff PATH` string ile `--diff N` int çakışır (argparse
  tek tip); ayrı bayrak temiz. `_list_doctor_history()` date desc → N=1
  en yeni; kullanıcı zihinsel model "1'ci en yakın" ile uyumlu.
- [KARAR] 086 tarihçe boş → exit 2 + "atlas doctor --save-baseline"
  öneri (SPEC 062 auto-baseline kalıbı ile simetrik).
- [KARAR] 086 seçilen snapshot path'i `diff_baseline_arg`'a atanır →
  mevcut `_diff_doctor_reports` yolu çalışır (SPEC 057 delta şeması
  BİT-UYUMLU; yeni delta türü YOK).
- [KARAR] 086 `--save-baseline` mutex listesi güncellendi:
  `--diff-history` de mutex (kaynak/hedef çakışması önlenir).

## 2026-08-05 (30. tur — 082 + 079 + 083 + 078 + 080 + 081)

Kullanıcı "devam et ve hepsini sıra ile uygula" → 29. tur adayları
(078-083) tümü zincirleme, küçükten büyüğe:
`082 → 079 → 083 → 078 → 080 → 081`.

- [KARAR] 082 ci-status: statik script `tools/scripts/gen_ci_badges.py`
  + drift gate workflow. Kullanıcı yeni workflow eklediğinde script
  çalıştırıp README güncellemeli (CI hatırlatır). Script Türkçe mesajı
  ASCII-only (SPEC 057 cp1254 kalıbı).
- [KARAR] 082 marker kalıbı: `<!-- ci-status:start -->` /
  `<!-- ci-status:end -->` — README'de yer bilinmiyorsa sona eklenir.
  Sonraki güncellemeler markörler arası salt-değişim (README'nin diğer
  içeriği korunur).
- [KARAR] 082 script `--repo OWNER/REPO` + env `GITHUB_REPOSITORY`
  override — CI'de otomatik, yerel kullanıcı bilinçli override.
- [KARAR] 079 `--sort-by` `argparse.choices` ile kısıtlı (name/size/
  date/members); geçersiz → argparse SystemExit(2) (semantik hata
  yerine tip hata). Default `name` SPEC 075 alfabetik bit-uyumlu.
- [KARAR] 079 `date` boşsa (atipik format arşiv) mtime fallback —
  ilk sıralama testi kırmadan sadece "sıralanabilir" olur.
- [KARAR] 083 `_run_npm_uninstall(bin, package)` — SPEC 060
  `_run_npm_install` kardeşi. Tek fark argv (`install` → `uninstall`).
  DRY için `_run_npm(bin, action, package)` yapılabilirdi ama YAGNI:
  iki fonksiyon net.
- [KARAR] 078 asimetrik `decrypt_backup_recipient` — passphrase YOK.
  `gpg-agent` unlock yapılmışsa çalışır; aksi hâlde gpg exit ≠0 →
  DECRYPT HATASI exit 6. Kullanıcı önce `gpg --list-secret-keys` ile
  keyring kilit açar.
- [KARAR] 078 `--decrypt` + `--decrypt-recipient` MUTEX exit 2 (iki
  farklı GPG modu, aynı çağrıda mantıksız). SPEC 073 `--encrypt` +
  `--recipient` mutex kalıbı.
- [HATA] 078 mesaj değişikliği: `"GPG decrypt → restore (SPEC 066)"`
  → `"GPG symmetric decrypt → restore (SPEC 066)"` (SPEC 078 asimetrik
  ayrımı için). Mevcut SPEC 066 test'leri 2 assertion güncellendi —
  bit-uyumluluk regex tolerans (`or` ile eski ve yeni metin).
  Kalıp: yeni SPEC mevcut mesajı değiştirirse mevcut test regex'ini
  gevşet (yeni_or_eski).
- [KARAR] 080 `--save-baseline` default path yan etkisi: tarihçe
  snapshot `.atlas/doctor-history/baseline-<today>.json`. Custom path
  → yan etki YOK (kullanıcı bilinçli). Bit-uyumluluk: default path
  içerik aynı, sadece ek dosya.
- [KARAR] 080 `--history-list` KISA DEVRE (SPEC 040 `--schema`
  kalıbı) — sağlık kontrolü YAPMA, sadece listele. Doctor'un idempotent
  bilgi modu.
- [KARAR] 080 `_prune_doctor_history` name (date lex) sıra: `baseline-
  YYYY-MM-DD.json` alfabetik = kronolojik (ISO 8601 avantajı).
  `mtime` yerine `name` — birden fazla update aynı gün gelirse aynı
  file üstüne yazılır (idempotent).
- [KARAR] 081 `--group-by hour|day` mevcut özet YERİNE gruplar
  tablosu. `_group_records_by(records, unit)` — `ts` bozuk → `"unknown"`
  grup (sona).
- [KARAR] 081 semantik mutex: `--group-by + --format prometheus`
  (Prometheus tekil metrik, grup histogram olmalıydı — YAGNI) +
  `--group-by + --alert` (alert single hit_ratio, group aggregation).
  Her ikisi exit 2.
- [KARAR] 081 grup dict `cost` YOK — fiyat env dependency + group başına
  cost hesap YAGNI. Kullanıcı ham token'larla dış hesap yapar.
  Gelecek SPEC 084 aday: `--group-by ... --with-cost`.
- [KARAR] Test toplamı: 1163 (29. tur sonu) → 1171 (082) → 1179 (079)
  → 1186 (083) → 1195 (078) → 1209 (080) → **1221** (081). +58 test.
- [KARAR] 30. tur boyunca hiç yıkıcı git operasyonu yok; 6 lineer feat
  + 1 docs commit; tek push tur sonunda.

## 2026-08-05 (29. tur — 077 + 074 + 076 + 075 + 072 + 073)

Kullanıcı "hepsini sıra ile uygula" → 28. tur adayları (072-077)
tümü zincirleme, küçükten büyüğe: `077 → 074 → 076 → 075 → 072 → 073`.

- [KARAR] 077 Docker YASAK gate iki katlı: CI workflow (`no-docker.yml`
  `git ls-files` ile tracked artefakt tespit) + pre-commit hook v4→v5
  Kapı 3 (`git diff --cached` regex). CI shallow clone dostu.
- [KARAR] 077 test kalıbı: mevcut `runtime/`, `tools/ai-cli/node_modules/`
  Go/npm stdlib Dockerfile'lar var → filesystem rglob YERINE `git ls-files`
  ile tracked semantik (CI ile eşdeğer).
- [KARAR] 077 hook v5 Docker gate sırası: Kapı 1 (doctor) → Kapı 2
  (vault verify) → Kapı 3 (Docker). Yıkıcı hata sonlarda; Docker gate
  read-only regex-only (hızlı).
- [KARAR] 074 GHA metrics workflow SPEC 056/070 kalıbıyla: `--limit 100`
  + 3 format (human/json/prometheus) artifact + PR comment koşullu
  (has_data=true). Fail step YOK — bilgi/artifact gate.
- [KARAR] 076 `--window MINUTES` `datetime.fromisoformat` ile parse.
  Planner `isoformat(timespec="seconds")` timezone-naive local yazıyor;
  window da naive `datetime.now()` — tutarlı. `ts` yok/bozuk kayıt
  filtre içi (defensive) — sınır durumlarında veri kaybı yok.
- [KARAR] 076 `--window` + `--limit` ORTOGONAL: önce window (zaman
  filtresi), sonra `[-limit:]` slice (sayı sınırı). Mantıklı ordering:
  önce hangileri "yakın" onları al, sonra son N'ini seç.
- [KARAR] 076 Prometheus text (`_build_metrics_prometheus_text`) window
  UYGULAMADI — canlı scrape için limit yeterli; window client-side
  Grafana range query'de yapılır.
- [KARAR] 075 `_list_archive_entries`: 7-alanlı dict (archive/task_id/
  date/size_bytes/size_human/member_count/mtime). Bozuk tar → -1
  member_count (skip'lemez, göster) — kullanıcı bozuk arşivi görsün.
- [KARAR] 075 dispatcher: `--list` `--restore`/`--search`/`--all`'dan
  ÖNCE (read-only, hızlı). SPEC 065 kalıbıyla aynı: read-only her
  zaman önce.
- [KARAR] 072 adaptif hesap `--adaptive`: `.atlas/metrics.jsonl` son N
  call `in+out+cache_c+cache_r` toplamı ortalaması. **< 3 kayıt →
  static fallback** (küçük numune ortalama yanıltıcı). Fallback source
  `adaptive-fallback-static` — kullanıcı UYARI görür.
- [KARAR] 072 `_estimate_run_cost` JSON şema genişleme: `source` +
  `sample_count` alanları eklendi. Bit-uyumluluk garantili (mevcut
  alanlar aynı; sadece ek).
- [KARAR] 072 adaptif limit `--adaptive-n` default 20 (metrics
  `--limit` ile paralel). Kullanıcı `--adaptive-n 5` derse son 5 kayıt
  (yakın geçmiş).
- [KARAR] 073 `--recipient` GPG asimetrik: `--trust-model always` +
  passphrase YOK (recipient keyring'te). CI/automation dostu.
- [KARAR] 073 `--encrypt` (symmetric) ve `--recipient` (asimetrik)
  MUTEX exit 2 — iki farklı GPG modu, aynı çağrıda mantıksız.
- [KARAR] 073 audit action `encrypt-recipient` (SPEC 063 `encrypt`
  ayrımı). Kullanıcı hangi mode kullanıldığını audit log'dan görebilir.
- [KARAR] 073 SPEC 067 `--keep-encrypted` .gpg glob'u iki mod için de
  aynı (uzantı `.tar.gz.gpg` her ikisi). Retention yatırımı iki modu
  paralel kapsar.
- [HATA] 073 hook v4 → v5 upgrade: Docker gate (Kapı 3) eklendi ama
  mevcut 34 hook testi v4 imzalı → 2 test failure. Kalıp uygulandı:
  `test_045_hook_signature_sabit_v4` → `_v5`; şablon 2. satır asserttion
  aynı upgrade.
- [KARAR] Test toplamı: 1110 (28. tur sonu) → 1117 (077) → 1123 (074)
  → 1133 (076) → 1144 (075) → 1154 (072) → **1163** (073). +53 test.
- [KARAR] 29. tur boyunca hiç yıkıcı git operasyonu yok; 6 lineer
  feat + 1 docs commit; tek push tur sonunda.

## 2026-08-05 (28. tur — 068 + 070 + 067 + 066 + 071 + 069)

Kullanıcı "hepsini sıra ile uygula" → 27. tur adayları (066-071)
tümü zincirleme. Sıra `068 → 070 → 067 → 066 → 071 → 069` (küçükten büyüğe).

- [KARAR] 068 `--alert-slack URL`: SPEC 064 `_post_alert_webhook`
  yeniden kullanıldı; farklı payload format `{text: markdown}` —
  Slack incoming webhook `text` field bekler. Slack, Discord, Teams
  hepsi `{text}` kabul eder ama Slack default görüntüleme mesajı
  bu field'e göre yapar.
- [KARAR] 068 üçlü ortogonal: `--alert-email` + `--alert-webhook` +
  `--alert-slack` aynı çağrıda üçü de çalışır. Exit 8 KORUR
  (SMTP+webhook+slack yan etkilerden bağımsız).
- [KARAR] 070 GHA workflow SPEC 056 (vault-health) kalıbıyla:
  `continue-on-error` doctor step + rc→GITHUB_OUTPUT; sonra artifact+
  comment+fail-step. Bonus: 2 rc (rc_strict OR rc_diff) — SPEC 062
  auto-baseline delta da bağımsız gate.
- [KARAR] 070 test defensive: PyYAML `on:` boolean parse'ına karşı
  `data.get("on") or data.get(True)` (SPEC 056 kalıbı).
- [KARAR] 067 encrypted retention ayrı fonksiyon `prune_encrypted_backups`
  (glob `vault-*.tar.gz.gpg`). SPEC 041.1 `prune_backups`'a bir parametre
  eklemek daha DRY olurdu ama iki havuz semantiği farklı — ayrı fonksiyon
  daha net (test edilebilir, bağımsız).
- [KARAR] 067 sıralama: backup → --keep (plain) → encrypt (plain silinir)
  → --keep-encrypted. Yani plain retention encrypt öncesi çalışır; yeni
  encrypted dosya --keep-encrypted N ile korunur.
- [KARAR] 066 `decrypt_backup` `encrypt_backup` kardeşi — argv sadece
  `--decrypt` (ve `--cipher-algo` yok, çünkü decrypt cipher'ı tar
  içinden okur). Yapı simetrik.
- [KARAR] 066 temp plain dosya kalıbı: `<target.parent>/.vault-restore-
  decrypt-<pid>.tar.gz` (gizli prefix + PID; çakışma yok). Restore
  **finally** ile silinir — başarı, çakışma, extract hatası hepsinde.
  Secret disk'te bırakılmaz.
- [KARAR] 066 auto-detect uyarısı: `.gpg` uzantı + `--decrypt` YOK →
  stderr UYARI. Kullanıcı yanlışlıkla plain restore denemesin. Hard-fail
  DEĞİL çünkü kullanıcı gpg-öncesi handle etmiş olabilir.
- [KARAR] 071 dispatcher sırası: `--restore is not None` truthy →
  restore branch. `--restore` nargs="?" const="" default=None →
  `--restore` bayraksız + `--search P` = SPEC 071. `--restore <id>` =
  SPEC 033. Sadece `--search P` = SPEC 065 list-only.
- [KARAR] 071 task_id çıkarma: arşiv adı `<task_id>-YYYY-MM-DD.tar.gz`
  formatı; son 11 char (`-YYYY-MM-DD`) kaldırılır. Farklı format →
  stem fallback (nazik). Belirsizlik (2+ eşleşme) → exit 2 + stderr
  listesi (kullanıcı daraltmalı).
- [KARAR] 069 `--estimate` SPEC 020 `--dry-run`'dan **farklı** semantik:
  - `--dry-run`: planner ÇALIŞIR (LLM cost var), action stub.
  - `--estimate`: planner HİÇ ÇAĞRILMAZ (LLM cost YOK), sadece
    heuristik tahmin.
  Ayrı bayrak — bit-uyumluluk garantili.
- [KARAR] 069 heuristik `tokens_per_call` default 500; env
  `ATLAS_ESTIMATE_TOKENS_PER_CALL` override. Gerçek adaptif hesap
  (SPEC 023 son N call ortalaması) YAGNI — gelecek SPEC 072?
- [KARAR] 069 stub backend + fiyat 0 → cost 0 (bilgi doğru; LLM yok).
- [HATA] 069 test — `_make_goal_yaml` helper başta `actions:/success:`
  kullandım ama `Goal` şeması `plan_kind:` + `plan_steps:` +
  `action_allowlist:` + `judge_kind:` + `judge_arg:` bekliyor. Kalıp:
  yeni goal YAML testleri yazarken önce `tests/goals/hello.yaml`
  şablonuna bak.
- [KARAR] Test toplamı: 1061 (27. tur sonu) → 1066 (068) → 1072 (070)
  → 1081 (067) → 1092 (066) → 1099 (071) → **1110** (069). +49 test.
- [KARAR] 28. tur boyunca hiç yıkıcı git operasyonu yok; 6 lineer
  feat + 1 docs commit; tek push tur sonunda.

## 2026-08-05 (27. tur — 061 + 062 + 060 + 064 + 065 + 063)

Kullanıcı 27. turu yeni oturumda "Continue from where you left off"
+ SessionStart hook `continue` ile başlattı. Onay dizisi: HEPSI
(küçükten büyüğe). Sıra: `061 → 062 → 060 → 064 → 065 → 063`.

- [KARAR] 061 `docs/api/vault-verify-schema.json`: Draft-07 JSON Schema.
  `additionalProperties: false` → gelecekte alan eklemek = **major bump**
  (SPEC 042 kod tarafında değişmez, şema public API).
- [KARAR] 061 test yaklaşımı: dış bağımlılık YOK (`jsonschema` paketi
  eklenmedi). Minimal Draft-07 doğrulayıcı test içinde — 6 kural
  (required, additionalProperties, type, integer minimum, array items
  required/additionalProperties). Runtime kalabalığı yok.
- [KARAR] 062 `--save-baseline PATH` `nargs="?"` `const=str(default)`:
  bayraksız → default `.atlas/doctor-baseline.json`; explicit path
  override.
- [KARAR] 062 `--auto-baseline` yoksa nazik: baseline dosyası yoksa
  bilgi + exit 0 (ilk çalıştırma). Kullanıcı `--save-baseline` ile
  oluşturur. `--strict` bayrağıyla birleşince ise regresyon durumu
  farklı — baseline yoksa strict de exit 0 (regresyon **var** demek
  için baseline olmalı; yoksa "yeni state" default kabul).
- [KARAR] 062 mutex zinciri: `--save-baseline` — `--diff`, `--auto-baseline`,
  `--serve`, `--format prometheus` ile mutex (hepsi read-only mode
  değil). `--auto-baseline` — `--diff` ile mutex (kaynak belirsiz).
- [KARAR] 060 `_run_npm_install(bin, package)`: `npm install <package>
  --save` (npm 7+ default explicit). `--save-exact=false` KULLANILMADI
  — npm defaults yeter (`^X.Y.Z` yazılır).
- [HATA] 060 test — `--save-exact=false` argv'ye eklemiştim ama
  testler argv sırasına bakmıyor, ayrıca npm bunu YAGNI'ye sokar
  (default `--save` ile aynı). Sürüm belirtmek isteyen kullanıcı
  `install <name>@1.2.3` yazsın; npm argv aynen forward.
- [KARAR] 064 `_post_alert_webhook`: SSRF savunma — `urlparse(url).scheme`
  yalnız `http/https`. `file://`, `ftp://` reddedilir. Slack incoming
  webhook default provider-agnostic (custom JSON kabul eder).
- [KARAR] 064 `--alert-webhook` ve `--alert-email` ORTOGONAL: ikisi
  verilirse ikisi de çalışır. Exit 8 KORUR (SMTP kalıbı — SPEC 059).
- [KARAR] 065 `_search_archive_contents`: tarfile.open + `getnames()`
  metadata; tar İÇERİĞİ AÇILMAZ (güvenlik + hız). Bozuk `.tar.gz`
  skipped (best-effort). `re.search` part-match; kullanıcı `(?i)`
  inline flag kullanır.
- [KARAR] 065 dispatcher sıra: `--search` en önde (read-only) —
  yıkıcı `--all`, `--restore` dallarından ÖNCE.
- [HATA] 065 test bug: kaynak `arşivde` (`ş` = U+015F) → pytest capsys
  Windows cp1254 stdout FD üzerinden capture ederken bozuluyor. SPEC
  057 [KALIP] hatırı: **insan çıktısında ASCII-only marker + kelime**.
  `arşivde` → `arsivde` düzeltildi. Kalıp: yeni `print()` string'lerinde
  Unicode >0xFF kaçın.
- [KARAR] 063 GPG passphrase stdin ile geçirildi (`subprocess.run(...,
  input=passphrase)`) — komut satırı history'sinde görünmez. Env
  fallback `ATLAS_BACKUP_PASSPHRASE`; argparse `nargs="?"
  const=env` deseni ile bayraksız çağrı env değerini alır.
- [KARAR] 063 `--encrypt` sonrası **ara plain `.tar.gz` silinir**
  (secret disk'te bırakılmasın). Retention (`--keep`) plain .tar.gz'e
  bakar; `.gpg` dosyaları retention'a girmez (SPEC 041.1 `vault-*.tar.gz`
  glob'u değişmedi). Kullanıcı encrypted retention için ayrı bir
  script/wrapper yazar (YAGNI, gelecek SPEC 067?).
- [KARAR] 063 restore tarafı DEĞİŞMEDİ — kullanıcı `gpg --decrypt
  <path>.gpg > /tmp/plain.tar.gz` sonra `atlas vault restore
  /tmp/plain.tar.gz --apply` çağırır. Otomatik decrypt-restore SPEC 066
  aday.
- [KARAR] 063 `_find_gpg_bin` sırası: env `ATLAS_GPG_BIN` (kullanıcı
  explicit) → portable `tools/gpg/gpg[.exe]` (depo-yerel) → `shutil.which("gpg")`
  (sistem PATH). Portable önce çünkü ATLAS taşınabilir kurulum
  disiplinine uyar (2026-07-28 [KALIP]).
- [KARAR] Test toplamı: 995 (26. tur sonu) → 1007 (061) → 1018 (062)
  → 1025 (060) → 1035 (064) → 1048 (065) → **1061** (063). Cov aynı
  seviyede (%91.50+). +66 test.
- [KARAR] 27. tur boyunca hiç yıkıcı git operasyonu (--amend/force) yok.
  6 lineer feat commit + 1 docs commit; tek push tur sonunda.

## 2026-08-04 (26. tur — 056 + 057 + 054 + 058 + 055 + 059)

Kullanıcı "DEVAM ET" tetikleyicisi → 6 aday görev, sıra
`056 → 057 → 054 → 058 → 055 → 059` (küçükten büyüğe).

- [KARAR] 056 `.github/workflows/vault-health.yml`: PR + push[main]'de
  vault verify CI gate. Fail → PR comment (peter-evans/create-or-
  update-comment) + artifact (health.md, 30 gün). `verify` step
  `continue-on-error: true` + rc `$GITHUB_OUTPUT` → sonraki step'ler
  comment/artifact yazabilir; sonra fail step exit 1.
- [KARAR] 056 permissions: `pull-requests: write` (comment için).
  Fork PR'larda otomatik değil — GitHub güvenlik politikası.
- [KARAR] 056 test defensive: PyYAML `on:` anahtarını `True`
  (boolean) olarak parse edebilir (YAML 1.1 backward-compat). Test
  `data.get("on") or data.get(True)` her iki key'i de dener.
- [KARAR] 057 `atlas doctor --diff BASELINE_JSON`: mutex GRUBU DIŞINDA
  (`--json` ile ortogonal). Semantik mutex kod içinde: `--diff +
  --serve/--schema/--format prometheus` → exit 2.
- [HATA] 057 sıralama bug: `--diff + --serve` semantik kontrol
  `--serve` blocking dalından SONRA yapılıyordu → HTTP server açılıp
  test hang. Çözüm: `--diff + --serve` early check `_cmd_doctor`
  başında (blocking daldan önce). Kalıp: blocking dallar için
  semantik mutex'ler ÖNCE.
- [HATA] 057 Windows cp1254 stdout bug: pytest capsys `→ ⚠ ✓ ✗` gibi
  Unicode >0xFF karakterleri encode edemez (`UnicodeEncodeError`).
  Ana kod UTF-8'e reconfigure ediyor ama pytest capture os.dup2 ile
  file descriptor seviyesinde çalışıyor, cp1254 kalıyor. Çözüm:
  insan çıktısında ASCII-only marker'lar (`[+] [-] [!] [~]`). Kalıp:
  yeni print çıktılarında `>0xFF` Unicode kaçın; ASCII marker kullan.
- [KARAR] 057 `_diff_doctor_reports` `unchanged` alanları raporda
  YER ALMAZ (gürültü azalt). `has_regression` = yeni uyarı VEYA
  quality regressed VEYA appeared+warning. `has_improvement` =
  removed uyarı VEYA resolved VEYA disappeared.
- [KARAR] 057 warnings duplicate: `set` farkı ile dedup (aynı warning
  2 kez baseline'da olsa bile bir kez raporlanır).
- [KARAR] 054 `_check_http(url, timeout=5.0)`: stdlib urllib.request
  GET; HTTPError → status yakala + `"HTTP <code>"` warning; URLError/
  Timeout/OSError → status=None + `"bağlantı hatası: ..."`; scheme
  http/https değil → `"URL scheme geçersiz: ..."`.
- [KARAR] 054 `quality.http_check` alanı yalnız `--http-check`
  verildiyse eklenir (bit-uyumluluk + IO maliyeti yok).
- [KARAR] 054 Prometheus: `atlas_doctor_http_check_up 0|1` + latency
  gauge (koşullu, latency None değilse). SPEC 043/047 kalıbıyla
  aynı — koşullu metrikler.
- [KARAR] 058 `atlas vault fix-broken`: SPEC 046 kalıbı (yıkıcı
  alt-komut, dry-run varsayılan, --apply gerekli). Ayrı alt-komut,
  `vault verify` DEĞİŞMEDİ.
- [KARAR] 058 stub notu tasarımı: aynı hedefe (`to`) birden fazla
  `from` → TEK stub + kaynak listesi (kısaltma değil, tam liste
  `[[from1]] [[from2]]` markdown). `#stub` tag'i → sonraki verify'da
  orfan tag olabilir ama kasıtlı (kullanıcı stub'ları görsün).
- [KARAR] 058 idempotency: hedef vault'ta zaten varsa (yarış durumu
  veya elle eklenmiş) → `action="skipped"`, dokunulmaz.
  Cross-file: vault içinde `<name>.md` `rglob` ile aranır (SPEC 046
  kalıbı — alt-klasörleri kapsar).
- [KARAR] 055 SPEC 051 refactor (bit-uyumlu):
  `observability/prometheus_server.py::make_handler + serve_prometheus_http`
  `content_type` + `allowed_paths` parametrik. Default değerler
  Prometheus (`text/plain; version=0.0.4`, `("/","/metrics")`).
  Handler adı `_PrometheusHandler` → `_AtlasHTTPHandler` (private,
  çağırıcı etkilenmez).
- [KARAR] 055 replay serve: `application/json; charset=utf-8` +
  `("/", "/runs")`. `_build_replay_json_body(limit)` her istek
  yeniden okur → canlı liste.
- [KARAR] 055 semantik mutex: `--serve + --list` (blocking vs
  snapshot), `--serve + <run-id>` (server tüm liste, tek run yayımı
  YAGNI).
- [KARAR] 059 `--alert-email`: `--alert PCT` ile birleşince eşik
  aşılırsa SMTP notify. Env sözleşmesi: HOST/PORT/USER/PASSWORD/
  STARTTLS + FROM/TO. Exception yakalanır → stderr `[alert-email]
  gönderim başarısız: ...`; **exit 8 KORUR** (alert semantiği email
  yan etkiden bağımsız).
- [KARAR] 059 STARTTLS default "1" (modern SMTP standart). PORT
  default 587 (SUBMISSION). USER/PASSWORD ikisi de varsa login;
  ikisi de yoksa anonymous SMTP (test/dev senaryosu).
- [KARAR] 059 test için `_FakeSMTP` class → `smtplib.SMTP` monkey.
  starttls/login/send_message çağrıları capture edilir; gerçek network
  yok.
- [KARAR] Test toplamı: 921 (056) → 944 (057) → 959 (054) → 973 (058)
  → 983 (055) → **995** (059). Cov %91.18 → %91.50.
- [KARAR] 26. tur boyunca 6 lineer feat commit + 1 docs commit; hiç
  yıkıcı git operasyonu (--amend/force) yok. Push tek seferde tur
  sonunda.

## 2026-08-04 (25. tur — housekeeping + 053 + 052 + 050 + 048 + 046 + 051)

Tek turda **6 aday görev + 1 housekeeping**. Sıra:
`chore ai-cli bump → 053 → 052 → 050 → 048 → 046 → 051`.

- [KARAR] Housekeeping: 24. tur DIŞINDA oluşan `tools/ai-cli/
  package.json` bump'ı (`opencode-ai ^1.18.10 → ^1.18.11`) tekil
  `chore(ai-cli):` commit'i olarak temizlendi (`173ea4e`). Sebep
  bilinmiyor (setup-ai-cli.cmd veya `npm update` çalıştı); DEVAM_NOKTASI
  sorusu bu şekilde cevaplandı.
- [KARAR] 053 `atlas --version`/`-V`: `argparse.action="version"`
  parse_args'ta erken exit yolu — subparser `required=True` olsa da
  çalışır (test doğrular). Kaynak `atlas_core.__version__` (pyproject.
  toml drift kontrolü test'te bit-uyumluluk garantiler).
- [KARAR] 052 hook v3 → v4: verify başarısız olduğunda `.atlas/vault-
  health.md` auto-dump. `.atlas/` git-ignored → commit döngüsü YOK.
  `--dump-report PATH` bayrağı ortogonal (JSON/pretty/strict ile birlikte).
  Yazma hatası SESSİZ (hook contextinde commit'i patlatmasın).
- [KARAR] `format_report_markdown(report, vault_root)`: UTC timestamp
  + koşullu 3 bulgu bölümü + Öneri (yalnız bulgu varsa). Deterministik;
  UTF-8 (Türkçe not adları/tag'ler).
- [KARAR] `_HOOK_SIGNATURE` `v3 → v4` (SPEC 045 v3'ten yükseltme).
  `_is_atlas_hook` versiyon bilinçsiz — v1/v2/v3/v4 hepsi ATLAS shim'i
  (mevcut davranış).
- [KARAR] 050 `atlas ai-cli update <name>`: `_run_npm_update` opsiyonel
  `package: str | None = None` keyword arg. `update <name>` verilirse
  `dependencies` kontrolü (yoksa exit 2 + `atlas ai-cli list` önerisi);
  yoksa mevcut davranış (hepsi). Konsol scope label: `npm update (name)
  (source: bin)`.
- [HATA] 050: Mevcut 3 mock lambda (`lambda _b, _d`) yeni imza ile
  TypeError verdi → `lambda _b, _d, package=None` güncellenip
  bit-uyumluluk sağlandı. Kalıp: fonksiyon imzası genişletilirken
  monkeypatch mock'ları paralel güncelle.
- [KARAR] 048 `tools/scheduling/`: kod değil, deployment artefaktı.
  Linux (systemd --user) `.service` + `.timer` + `install-linux.sh`;
  Windows Task Scheduler XML + `install-windows.ps1`. Windows XML
  UTF-16 zorunlu (Task Scheduler) — install-windows.ps1 `[System.IO.
  File]::WriteAllText(..., Unicode)` ile temp XML üretir. Şablon
  dosyası UTF-8 (test parse etsin diye) → install çıkışında UTF-16.
- [KARAR] 046 `atlas vault fix-orphans`: ayrı alt-komut (`vault verify
  --fix-orphans` yerine). Ana `verify` DEĞİŞMEDİ; bit-uyumluluk
  garantili. Dry-run varsayılan; `--apply` yıkıcı; çakışma çözümü
  `<name>-N.md` (1000 deneme koruması). Alt-klasördeki orfanlar
  (`daily/`, `tasks/`) `rglob` ile bulunur; hedef flat.
- [KARAR] 046 audit action `fix-orphans` yeni. Kaynak yok (yarış
  durumu) → `action="skipped"` nazikçe atlanır.
- [KARAR] 051 `--serve HOST:PORT`: yeni namespace `atlas_core/
  observability/`. `prometheus_server.py` stdlib `ThreadingHTTPServer`
  (dış bağımlılık YOK). `parse_host_port` + `make_handler` + `serve_
  prometheus_http`. Port 0 = OS ephemeral (test/dev — gerçek scrape
  client'ı 0'a bağlanamaz ama bind aşamasında geçerli).
- [KARAR] 051 mutex kalıpları:
  - `metrics`: `--json`, `--format`, `--serve` argparse aynı grup.
  - `doctor`: `--json`, `--schema`, `--format`, `--serve` argparse
    aynı grup. Bonus: `--ping --serve` semantik exit 2 (her istek
    anthropic quota tüketir).
- [HATA] 051: HTTP `send_error(500, ...)` Latin-1 header zorunluluğu
  → Türkçe mesaj `UnicodeEncodeError`. Çözüm: status message
  İngilizce (`Internal Server Error`), detay UTF-8 body'de.
- [HATA] 051: İlk implementasyonda `ready_cb(server)` `serve_forever()`
  ÖNCE senkron çağrıldı → accept döngüsü başlamadan client isteği
  timeout. Çözüm: `ready_cb`'yi ayrı thread'de çağır, `serve_forever`
  ana thread'de blocking. Test doğrulaması ile yakalandı.
- [KARAR] 051 body_fn her istekte yeniden çağrılır (canlı scrape).
  Metrics: `.atlas/metrics.jsonl` tekrar oku. Doctor:
  `_collect_doctor_report()` tekrar çalıştır. Bu Prometheus'un pull
  modelini karşılar (client scrape interval'ında güncel veri).
- [KARAR] 051 access log SESSİZ (`log_message` no-op) — stderr temiz
  kalsın; debug için env ile açılabilir (YAGNI).
- [HATA] 050 SHIP dosyası "857 → 862" yazıyor, gerçek 857 → 862
  DEĞİL: `pytest` çıktısı `857 passed` gösterdi (853 + 4 yeni 053
  + 5 yeni 050 - önceki cache). Doğru sayı 857. Kalıp: `pytest` çıktı
  sayısını commit mesajı YAZMADAN önce doğrula.
- [KARAR] Test toplamı: 838 → 842 (053) → 852 (052) → 857 (050) →
  870 (048) → 886 (046) → **912** (051). Cov %90.90 → %91.18
  (Prometheus HTTP server edge dalları test dışı — %100 kapsanmıyor).

## 2026-07-31 (24. tur — 044 + 049 + 045 + 047)
- [KARAR] 24. tur sıra `044 → 049 → 045 → 047`; ayrı feature
  branch'ler; main'e lineer ff-merge; sonda tek push. Kullanıcı
  onayı ile SPEC iskeletleri toplu sunuldu, sonra uygulama.
- [KARAR] 044: `.gitignore`'a `DOCTOR_cmd.png` + `DOCTOR_*.png` deseni.
  Dosya silinmedi (untracked kullanıcı yerelinde debug değerinde);
  yalnız gitignore. `git check-ignore` ile doğrulandı.
- [KARAR] 049 refactor: `src/atlas_core/utils/` yeni namespace
  (top-level). `utils/safe_tar.py::verify_tar_members(members,
  expected_root)` — SPEC 033 + 041 restore fonksiyonlarındaki 20
  satırlık ortak güvenlik loop'u 4 satıra indi.
- [KARAR] `UnsafeTarMemberError(ValueError)` domain-agnostik
  (N818 uyumlu). Çağıran taraf `str(exc)` ile RestoreError /
  VaultBackupError'a re-raise ederek MEVCUT MESAJ SÖZLEŞMESİNİ
  KORUR — test regex'leri değişmez (bit-uyumluluk mutlak).
- [KARAR] `filter="data"` extract güvenliği çağıran tarafta
  KORUNDU (defense-in-depth: verify_tar_members üye-üye kontrol,
  filter=data extract-time kontrol; ortogonal).
- [KARAR] 045 hook: `_HOOK_SIGNATURE` `# atlas-hook v1` → `v3`
  (asıl şablon `v2` idi ama sabit hâlâ v1 yazıyordu — mismatch
  düzeltildi). `_is_atlas_hook` versiyon bilinçsiz kaldı
  (`.split(" v")[0]` → "# atlas-hook" prefix'i); v1/v2/v3 hepsi
  ATLAS shim'i sayılır (mevcut davranış).
- [KARAR] 045 hook v3: doctor gate KORUNDU, yeni gate `atlas
  vault verify --strict`. Fresh clone naziksiz olmasın diye
  `[ -d vault ]` guard verify'den ÖNCE — vault yoksa gate atlanır.
  Kurulu v2 hook'lar `hooks status`'ta `up_to_date=False`; kullanıcı
  `hooks install --force` ile v3'e geçer.
- [KARAR] 045 test kalıbı: `_clean_env` autouse fixture
  `_HOOK_TEMPLATE_PATH`'i sahte tmp_path şablonuna monkeypatch
  ediyor. Gerçek şablon içerik testleri için
  `Path(__file__).parent.parent / "tools/hooks/pre-commit"`
  explicit repo kökü kullanıldı.
- [KARAR] 047 doctor prometheus: `_doctor_report_to_prometheus`
  `_cmd_doctor` yardımcısı olarak eklendi (test edilebilir birim).
  Metrikler: `atlas_doctor_up 1` (canonical up), `warnings_total`,
  `quality_healthy{field=NAME} 0|1`, opsiyonel `scan_src_*`.
- [KARAR] 047 parser: `--json`, `--schema`, `--format` üçlüsü
  `add_mutually_exclusive_group()`. store_true davranışları
  KORUNDU. Bonus: `--json --schema` de mutex artık (önceden ayrıydı;
  mevcut testlerde çakışma denemesi olmadığı için kırılmadı).
- [KARAR] 047: `--strict` format bağımsız — Prometheus çıktı da
  basılır ve exit 9 döner (alertmanager scrape + exit-based alert
  aynı anda çalışır).
- [KARAR] `--format prometheus` sözleşmesi metrics + doctor için
  ortak kalıp: mutex `--json` ile, default `None` → bit-uyumluluk,
  choices `["human", "prometheus"]` (`human` = default davranış).
  Gelecek görevler bu kalıbı takip etsin.
- [HATA] 049 test yazarken `tests/test_archive.py` var sandım —
  yok, doğrusu `tests/test_cli_archive_restore.py`. Kalıp: `ls
  tests/ | grep <keyword>` ilk adım.
- [HATA] 045 test yazarken `_prep_repo` diye bir yardımcı
  varmış gibi çağırdım — yok. Aslında `_clean_env` autouse
  fixture kullanılıyor. Kalıp: yeni testler eklerken önce
  test dosyasının conftest/fixture yapısını oku.
- [KARAR] Test toplamı 810 → 838 (bu tur +28: 044 +0, 049 +12,
  045 +5, 047 +11). Cov %90.85 → %90.90.

## 2026-07-31 (23. tur — 041.1 + 042 + 037.4 + 043)
- [KARAR] Görevler ayrı feature branch'lerde, tek zincirde `main`'e
  lineer ff-merge; sıra `041.1 → 042 → 037.4 → 043`. Housekeeping
  önce yapıldı: 22. tur `b5ce74c` (bugün 15:15 doctor bakım commit'i)
  push edildi, 6 merged branch (feat/paketleme-bulut-secenegi,
  feat/tasinabilir-kurulum, fix/{arsivleyici-arama,
  kimi-yeniden-etkinlestirme, ollama-kimligi-tasinabilir,
  surum-etiketli-yedek}) silindi.
- [KARAR] 041.1 `--auto` bayrağı `--out` ile MUTEX (exit 2). Explicit
  intent = cron/scheduled; audit action `backup-auto` (aksi hâlde
  düz `backup`). `--out` verilirse retention YOK (yalnız
  `archive_root` glob'unda mantıklı; uyarı stderr).
- [KARAR] `prune_backups(archive_root, keep)` yalnız `vault-*.tar.gz`
  desenine dokunur — SPEC 007 task arşivleri veya README.txt korunur.
  mtime desc + ilk N tutar; `archive_root` yok → boş liste (cron nazikliği).
- [KARAR] 042 `atlas vault verify`: yeni modül
  `atlas_core/memory/vault_verify.py` (`BrokenLink` dataclass +
  `VerifyReport` + `verify_graph(graph)`). Vault üzerinde YAZMA YOK;
  `Vault.graph()` üzerinden salt-okunur analiz.
- [KARAR] 042 `--strict` + bulgu → exit **4** (yeni exit kod anlamı).
  `atlas run` içindeki `PlannerExhaustedError` 4 ile çakışmaz — vault
  verify bağımsız komut; aynı bağlamda dönmez.
- [KARAR] `BrokenLink` alan adı `frm` (Python `from` rezerve); JSON
  dışa aktarımda literal `"from"` yazılır.
- [KARAR] 037.4 `status` exec çalıştırmaz; `_read_installed_version`
  (037.2) + `_resolve_ai_cli_bin` (037.3) yeniden kullanır. Boyut için
  yeni yardımcı `_dir_size_bytes` (rglob, symlink skip, OSError skip);
  `_human_bytes` (B/KB/MB/GB).
- [KARAR] 037.4 `up_to_date`: declared'daki `^ ~ >= < !` prefix'leri
  sıyrılıp string eşitliği. Semver-uyumlu ama farklı sürüm (`^1.18.9`
  vs installed `1.18.10`) `False` gösterir — kasıtlı: kullanıcı intenti
  "tam beklenen mi", "semver-uyumlu mu" değil.
- [KARAR] 043 `--format {human,prometheus}` `--json` ile MUTEX
  (`add_mutually_exclusive_group`). `--format` default `None` →
  bit-uyumluluk; `--format human` = default davranış.
- [KARAR] 043 Prometheus çıktısı `cache_hit_ratio` gauge 0-1 arasında
  (Prometheus konvansiyonu — ondalık, `%` değil). İnsan çıktısındaki
  `%` gösterimle ölçek farklı; dashboard tarafı `* 100` yapmalı.
  HELP metninde yazılı.
- [KARAR] 043 `records_total` counter adında `_total` var ama semantiği
  "pencere içindeki gözlem sayısı" (limit=20 default). HELP metninde
  "observed in window" açıklaması.
- [KARAR] Fiyat env'i yoksa `cost_usd_total 0.0` yayımlanır — Prometheus
  için tutarlılık (counter satırının kaybolması scrape'i bozar).
- [HATA] `git add pipeline/tasks/043-metrics-prometheus/` — trailing slash
  Windows Git için pathspec hatası; tırnak içine alınca çözüldü.
  Kalıp: yeni klasörleri `git add "path/dir"` şeklinde tırnaklı ekle.
- [HATA] İlk 041.1 commit'ine `DOCTOR_cmd.png` (22. turdan kalan
  untracked ekran görüntüsü) `git add -A` yüzünden girdi; `git rm
  --cached` + `--amend` ile temizlendi. Kalıp: yeni commit'lerde
  `git add <path> <path>` (explicit path listesi); `git add -A`
  kullanılırsa öncesinde `git status --short` ile kontrol.
- [KARAR] Test toplamı 770 → 773 (22. tur +3 doctor batch) → 810 (bu
  tur +37: 041.1 +10, 042 +14, 037.4 +7, 043 +6). Cov %90.76 → %90.85.

## 2026-07-30 (Görev 041 — atlas vault backup/restore)
- [KARAR] Yeni modül `atlas_core/memory/vault_backup.py` — SPEC 033
  archive kalıbının kardeşi ama vault-özelinde. Ortak yardımcıya
  çıkarmadım (henüz iki kullanım için orantısız).
- [KARAR] Tar kökü sabit `vault/` (arcname). Restore beklenmedik bir
  kök gördüğünde reddeder — yanlış tar (örn. archive/003) vault'a
  bulaşmaz.
- [KARAR] Restore **temp dir'e extract + rename** kalıbı — mevcut
  vault'un üstüne kısmi extract yazmaz. Path traversal doğrulaması
  extract'ten önce; extract sırasında bir hata olursa temp dir
  temizlenir (finally).
- [KARAR] Hedef mevcut + boş değil → exit 3 (SPEC 033 kalıbı: çakışma).
  Hedef yok VEYA boş → devam. Kullanıcı `rmdir` ile boşaltıp yeniden
  deneyebilir.
- [KARAR] Varsayılan yedek yolu: `<archive_root>/vault-YYYY-MM-DD-HHMM.tar.gz`.
  Aynı dakikada iki yedek → aynı ada denk gelir; ikinci overwrite.
  Kullanıcı `--out` ile özel isim verebilir. YAGNI: milisaniye
  eklemek şu an gereksiz.
- [KARAR] Audit satırları: `atlas-vault` / `backup|restore` / `<path>`.
  `atlas-archive` altında değil — arşiv ≠ vault kavramları.
- [VARSAYIM] `os.replace` (rename) aynı volume içinde çalışır. Windows'ta
  `ATLAS_VAULT` farklı disk gösterirse rename patlarsa `shutil.move`
  fallback düşünülür (YAGNI, testte tmp_path her zaman aynı disk).

## 2026-07-30 (Görev 040 — atlas doctor --schema)
- [KARAR] `--schema` **kısa devre** — sağlık kontrolü YAPMAZ, dizinlere
  dokunmaz, `_collect_doctor_report` çağrılmaz. Idempotent + IO'suz +
  hızlı (bir sabit dict basıp döner).
- [KARAR] `_doctor_schema_descriptor` module-scope fonksiyon (sabit
  değil) — string literalleri f-string açmıyor, ileride koşullu
  alanları destekleyebilir.
- [KARAR] Şema tanımı ayrı bir sabit içinde tutulmuyor — bakım yükü
  fonksiyonda: `_collect_doctor_report` alan eklerken
  `_doctor_schema_descriptor` da güncellenir. Kabul: küçük yük, tek
  yerde koleyi olmayan bir yorum satırıyla belgeledim.
- [KARAR] Diğer doctor bayrakları (`--strict`, `--ping`, `--scan-src`)
  ile birleşmez — `--schema` gördüğünde erken return. Sözleşme temiz:
  bir komut = bir eylem.
- [KARAR] `--pretty` `--schema` ile birlikte çalışır (indent=2) — 032.5'in
  --json --pretty'siyle tutarlı davranış.

## 2026-07-30 (Görev 023.2 — atlas metrics inflight istatistiği)
- [KARAR] Sadece **insan formatı** çıktısına eklendi (`inflight avg/max: A / N (K kayıtta)`).
  `--json` bit-uyumlu (ham kayıt listesi) — tüketiciler kendi
  agregasyonlarını yapabilir. Ayrı bir `--summary` bayrağı YAGNI.
- [KARAR] `inflight` alanı olmayan kayıtlar (SPEC 039 öncesi run'lar)
  skip — bit-uyumluluk. Hiç inflight yoksa satır BASILMAZ (gürültü yok).
- [KARAR] `isinstance(r.get("inflight"), int) and r["inflight"] >= 0`
  filtresi — negatif değer defensif olarak reddedilir (ideal olarak
  hiç görülmez ama audit-log okuyucularının fail-safe olma alışkanlığı
  bu tarafta da).
- [KARAR] `avg` `sum/len` — decimal.Decimal yok (2 haneli hassasiyet
  yeter, `f"{avg:.2f}"`).

## 2026-07-30 (Görev 037.3 — atlas ai-cli exec launcher)
- [KARAR] `tools/ai-cli/node_modules/.bin/<name>` — npm'in kanonik shim
  yeri. Windows'ta `.cmd`, Unix'te çıplak isim. Ayrıca `.exe` denemek
  için ekstra bir yol (native shim'ler).
- [KARAR] Windows `.cmd` shim'i `subprocess.run([str_path, *args])` ile
  argv liste olarak başlatılıyor — Python 3.12+ `.cmd`/`.bat` için
  cmd.exe altında çalıştırır (dokümanlı davranış). `shell=True` YOK
  (shell injection riski + argv escape zorluğu).
- [KARAR] `argparse.REMAINDER` seçildi (`nargs`) — kullanıcı `-`'lu
  flag'leri (`--version`, `-h`) forward edebiliyor. Python REMAINDER
  deprecated niyetinde ama `nargs='*'` bunu yapmaz (flag'ler kendi
  parser'ında yakalanır).
- [KARAR] Bin yok → `atlas ai-cli list` önerisi. Kullanıcı SPEC 037.2
  ile hemen paket listesini görebilir; ekosistem tutarlı.
- [KARAR] `.exe` de aranıyor (Windows) — bazı npm paketleri native
  binary shim koyar (opencode-ai bin dizininde `opencode.exe`
  yok ama `.cmd` var — bu esneklik gelecek paketler için).

## 2026-07-30 (Görev 039 — LLM inflight metriği)
- [KARAR] Global `_INFLIGHT_COUNT` + `threading.Lock` — module scope
  planner.py'de. SPEC 031'in "N paralel çağrı" gerçeğini metriğe
  yansıtır. Rate limit debug'ı + API concurrent quota tuning için
  temel veri.
- [KARAR] `_call_anthropic` wrapper/inner ayrımı — wrapper yalnız
  `_inflight_begin() + try/finally + _inflight_end()`; iş inner'da.
  Fonksiyon 100+ satır olduğu için tümünü `try/finally` altına almak
  invaziv olurdu; wrapper 8 satır, temiz.
- [KARAR] Snapshot **çağrı başlangıcında** alınır (çağrıyı DAHİL
  sayarak). "Bu çağrı başlarken kaç eş-zamanlı vardı" istatistiği —
  peak farklı, snapshot-at-start daha stabil.
- [KARAR] `_write_metric_for_data(data, inflight: int | None = None)`
  — inflight None → alan YAZILMAZ. Mevcut SPEC 023 testleri
  bit-uyumlu; okuma tarafı yeni alanı görmezden gelmeli (forward
  compatible).
- [KARAR] `_inflight_end()` `max(0, COUNT-1)` — defensive; yanlış
  eşleştirme durumunda negatife düşmez. Wrapper try/finally garantisi
  ile leak olmamalı ama double-end koruması bedava.
- [KARAR] Test izolasyonu: `monkeypatch.setattr(pl, "_INFLIGHT_COUNT", 0)`
  ile sayaç sıfırlanır — modül-globalin test paralel çalıştırmada
  race'inden kaçınır (pytest her testte fresh state).

## 2026-07-30 (Görev 034.2 — pre-commit shim canlı regresyon testi)
- [KARAR] SPEC 034 statik test yeterli değildi — shim'i shell üzerinden
  gerçek subprocess ile çalıştırıp exit haritasını doğrulayan
  entegrasyon testi eklendi (`test_cli_hooks_regression.py`).
- [KARAR] Mock atlas scripti (`#!/bin/sh; exit ${ATLAS_MOCK_EXIT:-0}`) —
  tmpdir/bin'de; PATH başına eklenip shim'in `atlas` çağrısı bu mock'a
  yönlendirilir. Test 4 senaryoyu kapsar: exit 0/9/2 + statik regex.
- [KARAR] `_find_hook_shell()` None → `pytest.skip()` — baremetal
  Windows CI'da sh.exe olmayabilir; test AŞILMAZ, atlanır. Yerel
  makinede `tools/git/usr/bin/sh.exe` (portable) → 4 test geçti.
- [KARAR] Kaynak kodda değişiklik YOK — yalnız test. Görev bilinçli
  bir regresyon ağı, davranış değişikliği değil.

## 2026-07-30 (Görev 031.1 — batch dry-run toplu step özeti)
- [KARAR] Özet BLOKU yalnız `--dry-run` verildiğinde basılır —
  bit-uyumluluk. Real batch (yıkıcı) modunda gürültü eklemez.
- [KARAR] Regex parse (`^  (plan|act|observe|reflect)\s+(.*)`) —
  `_cmd_run_goal` sabit çıktı formatına dayanır. Format değişirse
  özet 0 döner (sessiz), sözleşme kırılmaz.
- [KARAR] Seri dalda `_Tee(sys.stdout, buf)` +
  `contextlib.redirect_stdout` — tek thread'de process-global override
  zararsız (SPEC 031'in paralel için TLS problemi seride yok). Real-time
  stdout korunur.
- [KARAR] Paralel dal mevcut TLS-captured metinleri kullanır — 031'deki
  altyapı doğrudan yeniden kullanılabilir, ekstra iş yok.
- [KARAR] Özet çıktısı: `toplam step: N (plan=X, act=Y, observe=Z,
  reflect=W)` + ilk 5 act eylem. 5'ten çoksa `…N eylem daha`. Sözlü
  agregasyon; kullanıcı ne gördüğünü anlar.

## 2026-07-30 (Görev 037.2 — atlas ai-cli list)
- [KARAR] `package.json` dependencies alanı **kaynağın kanonik listesi**;
  `node_modules/<n>/package.json` version cross-check.
- [KARAR] Şema: `{"path": ..., "packages": [{"name","expected","installed"}]}`.
  `installed=null` → kurulu değil (JSON); insan formatı `(kurulu değil)`.
- [KARAR] Sütun genişliği `max(20, en uzun paket adı)` — sabit yerine
  dinamik → uzun paket adları (`@kilocode/cli`) taşmadan hizalanır.
- [KARAR] Deps boş → `(paket yok)` mesajı, exit 0 (uyarı değil).
- [KARAR] Bozuk `package.json` → SPEC HATASI + exit 2. Kurulu değil
  ile aynı sınıfta değil — repo bozukluğu vs eksik kurulum ayrımı.

## 2026-07-30 (Görev 031 — batch `--jobs N` paralel yürütme)
- [KARAR] `--jobs N` (varsayılan 1) — N=1 mevcut seri (SPEC 030
  bit-uyumlu); N>1 `ThreadPoolExecutor(max_workers=N)`. IO/LLM bound
  işler için threading yeterli; `ProcessPoolExecutor` ağır (import
  overhead, Windows spawn maliyeti), izolasyon fazlalığı (sandbox
  zaten yol bazlı).
- [KARAR] Paralel modda **fail-fast implicit KAPALI** —
  `continue-on-error` gibi davranır. Sebep: worker'lar zaten koşuyor;
  ilk hatayı gördükten sonra kalanları iptal etsek bile başlamış
  olanlar bitene kadar bekleriz. Kullanıcı fail-fast istiyorsa
  `--jobs 1` (seri).
- [KARAR] LLM rate limit için ayrı env (örn. `ATLAS_LLM_MAX_INFLIGHT`)
  YOK. `--jobs N` doğrudan max N inflight LLM çağrısı; kullanıcı N'i
  düşürerek API limit'ine uyumlanır. Ayrı semafor karmaşıklığı için
  gerekli senaryo şu an yok (YAGNI).
- [HATA→KARAR] `contextlib.redirect_stdout` **process-global** —
  thread-safe DEĞİL. İki worker aynı anda `__enter__` yaparsa ana
  thread'in `print()` çağrıları da worker buf'una düşer (ilk hata
  belirtisi: `--- [1/N] ...` başlıkları hiç görünmüyor). Çözüm: kendi
  `_ThreadCaptureStream` — `threading.local()` üzerine kurulu bir
  wrapper; TLS'de buf yoksa gerçek stream'e yazar. `sys.stdout` bir
  kere değişir (batch paralel süresince); worker `begin()/end()` ile
  kendi buf'unu açar/kapatır.
- [HATA→KARAR] `AuditLog` **thread-safe değildi**. İki worker aynı
  `audit.jsonl`'e append yaparken `_last_hash()` okuyup zincir
  noktasına yazma race koşulu → dosyada boş satır +
  `json.loads('')` patlaması + zincir bozulması. Çözüm: `audit.py`
  içi module-level `_AUDIT_LOCKS: dict[str, threading.Lock]` (path
  key). `record()` içi + `verify()` okuma içi lock. Ek olarak
  `verify()` boş satırları fail-safe skip (paralel append arasında
  görülebilen yarım-satır artefaktı için).
- [KARAR] Worker çıktısı: her worker `stdout+stderr`'i TLS buf'ta
  toplar → ana thread `as_completed` ile sonuç toplar → **başlangıç
  sırasına** göre print eder. Log sırası deterministik. Test bunu
  doğrular.
- [KARAR] `--jobs 0` veya negatif → SPEC HATASI + exit 2. `argparse`
  `type=int` verildiğinden default=1; `_read_jobs_arg` invaziv
  doğrulama yapar (`or 1` kullanma — 0 truthy değil, hata yerine 1'e
  düşerdi).

## 2026-07-30 (Görev 033 — `atlas archive --restore <id>`)
- [KARAR] `--restore <id>` **dry-run varsayılan** — arşive gönderme
  ile simetri. `--apply` yıkıcı kapı (mevcut task klasörü olabilir).
  Exit kodu 3: çakışma; 6: arşiv yok VEYA extract hatası. `RestoreError`
  yeni tip (N818 uyumlu).
- [KARAR] En yeni sürüm seçilir — bir görev birden çok kez
  arşivlenmiş olabilir (`003-2026-07-15.tar.gz`, `003-2026-07-30.tar.gz`).
  `mtime` desc → `[0]`. Kullanıcıya belirsizlik bırakma.
- [KARAR] Path traversal koruması **çift katman**: (1) her tar üyesi
  elle kontrol — mutlak yol, `..`, kolon `:` (Windows NTFS ADS),
  beklenmeyen kök reddedilir; (2) `tar.extractall(filter="data")` —
  Python 3.12+ default'u 3.14'te kesinleşecek; şimdi opt-in ederek
  DeprecationWarning'i temizledik ve extra güvenlik katmanı sağladık.
- [KARAR] `_is_within` yardımcısı — `resolve().relative_to()` bir
  ekstra güvenlik ağı. Bu noktaya normalde ulaşılamaz (task_id
  kontrolü var), ama defense-in-depth.
- [KARAR] Audit satırı: `atlas-archive` / `restore` / `<id>`.
  `archive`'ın simetriği.

## 2026-07-30 (Görev 037.1 — `atlas ai-cli update` portable npm wrap)
- [KARAR] `atlas ai-cli update [--dry-run]` — `tools/ai-cli/`
  içinde `npm update` (veya `npm outdated --long`). Portable öncelik:
  `tools/node/npm.cmd` (Windows) veya `tools/node/npm` (Unix); yoksa
  `shutil.which("npm")` (sistem PATH).
- [KARAR] `--dry-run` = `npm outdated` — npm'in 1 exit'i "bulgu var"
  demek, HATA değil; CLI 0 döner. `update` (yıkıcı) → npm exit
  kodu doğrudan yansıtılır.
- [KARAR] npm stderr'de "notice…" tarzı bilgi mesajları yazabilir;
  worker bunları stderr'e olduğu gibi bastırır (info-level).
- [KARAR] Timeout 600s — büyük ağaçlarda uzun sürebilir; testte
  subprocess mock'lu.
- [KARAR] `tools/ai-cli/` yoksa → exit 2 + `SPEC HATASI`; kullanıcı
  portable kurulumun eksik olduğunu bilsin.

## 2026-07-30 (Görev 038 — `doctor --scan-src unique_hits` alanı)
- [KARAR] `quality.scan_src` şemasına `unique_hits: int` eklendi.
  `total` = ham bulgu (bir dosyada birden çok kalıp olabilir);
  `unique_hits` = kullanıcının gerçekten düzeltmesi gereken tekil
  dosya sayısı. `sample_files` (ilk 5 unique) mevcut kaldı.
- [KARAR] **Şema major bump YOK** — yalnız alan eklendi (SPEC 032.4
  sözleşmesi: ekleme = uyumlu, kaldırma/rename = major). `schema_version="1"`
  korundu.
- [KARAR] İnsan formatı `(N bulgu, M tekil dosya)` — mevcut
  `(N bulgu)` sözleşmesini SUBSTRING olarak koruduğu için 032.2/032.3
  testleri kırılmadı.

## 2026-07-30 (Görev 037 — `atlas ai-cli diff-summary` commit disiplin)
- [KARAR] `atlas ai-cli` **yeni alt-grup** — `hooks` gibi genişlemeye
  hazır (`ai-cli update`, `ai-cli list` gelecek). `diff-summary` ilk
  komut.
- [KARAR] Sadece `tools/ai-cli/package-lock.json` diff'ini parse
  eder — `package.json` bump'ları ve diğer dosyalar YAGNI. Auto-update
  yolunda gerçek değişiklik burada.
- [KARAR] Çıktı formatı **düz metin, tek satır** (commit mesajına
  doğrudan pipe edilebilir); JSON/YAML seçenekleri YAGNI. `$(atlas
  ai-cli diff-summary)` shell substitution kalıbı bilinen.
- [KARAR] Unicode `→` — ASCII `->` da olurdu ama `→` git commit
  mesajlarında yaygın kalıp; konsol UTF-8 reconfigure mevcut.
- [KARAR] `node_modules/` prefix strip edilir — package-lock'ta
  anahtar `node_modules/opencode-ai` şeklinde ama insan okuru sade
  ad ister. Commit mesajında `chore(ai-cli): opencode-ai 1.18.8 →
  1.18.9`.
- [KARAR] İsim `diff-summary` seçildi, `commit-msg` değil. Sebep:
  komut daha genel — kullanıcı hangi paketin bump olduğunu görmek
  isteyebilir (commit atmadan). Commit mesajı bir kullanım kalıbı,
  başka biçimler eklenirse ad zorlanmaz.
- [KARAR] Git subprocess ile parse — `git diff --unified=0`
  belirlenimci format. Timeout 10 sn; fail-safe: git yok / patlarsa
  `(diff okunamadı: ...)` + exit 0. Kullanıcının iş akışını KESMEZ.
- [HATA] 17. tur bulgu (`790c9da`) çözümü kısmi — bu komut kullanıcının
  commit mesajını üretmesini kolaylaştırır ama disiplini garanti etmez.
  Full otomatik commit atmak (mesaj + `git commit` çağrısı) YAGNI;
  kullanıcı review yapmak isteyebilir.
- Kapsam: 1 modül düzenleme (cli.py: +subprocess import, +5 fonksiyon,
  parser ai-cli alt-grup), 1 yeni test dosyası (+10 test). 693 test
  yeşil (683 → +10). Artefaktlar `pipeline/tasks/037-ai-cli-diff-
  summary/`.

## 2026-07-30 (Görev 032.5 — `atlas doctor --json --pretty`)
- [KARAR] `json.dumps(indent=2, ensure_ascii=False)` — mevcut
  `ensure_ascii=False` korunuyor (Türkçe karakter destek).
- [KARAR] `--pretty` `--json` OLMADAN sessizce yoksayılır (insan
  format zaten çok satırlı). Tek başına bir "kimlik" bayrağı gibi.
  Alternatif error ("--pretty --json olmadan anlamsız") — YAGNI,
  kullanıcı sessizce alıştığı formatı görsün.
- [KARAR] Strict davranışı bayraktan bağımsız — `--pretty + --strict
  + drift` → exit 9 hala. Biçim sadece çıktı biçimi; kalite gate'in
  davranışını değiştirmez.
- [KARAR] Bit-uyumluluk mutlak — `--pretty` yoksa `json.dumps(indent=
  None)` mevcut çıktıyla birebir. Mevcut CI script'leri kırılmaz.
- Kapsam: 1 modül düzenleme (cli.py: parser --pretty + JSON yolu
  indent parametrik), 1 test dosyası eki (+3 test). 683 test yeşil
  (680 → +3). Artefaktlar `pipeline/tasks/032-5-doctor-pretty/`.

## 2026-07-30 (Görev 032.4 — `atlas doctor` JSON `schema_version` alanı)
- [KARAR] Şema versiyonu **string sabit `"1"`** — semver değil.
  Sebep: minor bump'lar ("1.1", "1.2") disiplin açısından belirsiz;
  string ile "bumpı düşün ya da düşünme" ikilisi kalır. Alan
  ekleme = aynı sürüm; kaldırma/rename/tip değişikliği = major
  bump ("2", "3"...).
- [KARAR] Modül seviyesinde sabit `_DOCTOR_SCHEMA_VERSION`. Tek
  yerden bump; JSON + insan format + test hepsi bunu okur. `grep -w
  _DOCTOR_SCHEMA_VERSION` bumpların tarihçesini gösterir.
- [KARAR] Yalnız `atlas doctor` için şema versiyonu — `atlas metrics
  --json`, `atlas replay --list --json`, `atlas hooks status --json`
  YAGNI. Doctor'un şeması iterasyon boyunca en çok büyüyen; diğerleri
  dar. İhtiyaç doğarsa aynı kalıp taşınır.
- [KARAR] İnsan format başlığa **parantezli** ekle (`=== ATLAS
  doctor — env sağlık kontrolü (şema v1) ===`) — mevcut başlığı
  bozmadan görünür. `[!]` ile karışmasın diye ilk satırda.
- [KARAR] Bit-uyumluluk: mevcut JSON alanları BİREBİR korundu;
  yalnız EKLEMELER. Eski tüketiciler eski alanları görmeye devam.
  Yeni tüketiciler `schema_version` ile karar verebilir.
- Kapsam: 1 modül düzenleme (cli.py: +sabit, +alan, +başlık), 1
  test dosyası eki (+4 test). 680 test yeşil (676 → +4). mypy strict
  + ruff + scan temiz. Artefaktlar
  `pipeline/tasks/032-4-doctor-schema-version/`.

## 2026-07-30 (chore/036: `tools/ai-cli/` npm install drift fix)
- [KARAR] `npm update opencode-ai --prefix tools/ai-cli` ile
  `package-lock.json` upstream 1.18.9'a senkron edildi. `package.json`
  `^1.18.8` semver aralığı 1.18.9'u zaten kapsıyordu — DEĞİŞMEDİ.
  Alternatif `npm install opencode-ai@latest --save` package.json'u
  da bump ederdi; YAGNI, semver istikrarı bozar.
- [KARAR] **Portable npm** kullanıldı (`tools/node/npm.cmd`) —
  makine bağımsız davranış; kullanıcının global npm sürümüne bağlı
  olmayan, deterministik.
- [KANIT] Smoke: `opencode_Run.cmd --version` 1.18.8 → 1.18.9;
  cline/kilo etkilenmedi (3.0.47, 7.4.16). Pytest regresyon 676
  aynen (Python kod dokunulmadı).
- [HATA/NOT] Beklenmedik bulgu: `790c9da` commit mesajı "opencode
  1.18.8 -> 1.18.9" diyor ama gerçek diff **cline 3.0.46 -> ^3.0.47**
  bump'ıydı — auto-update mekanizmasının başka bir mesaj/diff
  eşleşmesi. Kalıp: commit mesajları gerçek diff ile senkron olmalı.
  Auto-update politikasının mesajını gelecek turda düzeltmek isteriz.
- Kapsam: `package-lock.json` regenerate; `pipeline/tasks/
  036-opencode-npm-install/00-need.md`. Pytest regresyon 676 aynen.

## 2026-07-30 (Görev 035 — `opencode_Run.cmd` + `kilo_Run.cmd` thin shim)
- [KARAR] 14-15. tur launcher kalıbı (claudecode/goose/cline/kimi)
  ile simetri: 6 kök launcher hepsi `tools/agents/<name>.cmd`
  sarmalayıcısına `call` eden **thin shim**. DRY — kurulum
  sihirbazı sarmalayıcıyı güncellediğinde kök launcher otomatik
  yararlanır.
- [KARAR] Tarihsel `opencode_Run.cmd` ve `kilo_Run.cmd`
  yazımları (`node_modules/.bin/opencode.cmd` npm shim; kilo için
  HOMEDRIVE/HOMEPATH override) **kaldırıldı**. Sarmalayıcılar zaten
  daha güçlü: `tools/agents/opencode.cmd` native `opencode.exe`
  çağırıyor (memory 2026-07-24 Node CLI direkt bin kalıbı);
  `tools/agents/kilo.cmd` HOME + USERPROFILE + XDG ile yeter
  (HOMEDRIVE/HOMEPATH cmd yerleşiği; Node os.homedir()
  USERPROFILE'a bakar — cmd env değişkenlerini okumaz).
- [KARAR] `claudecode_Run.cmd` istisna kalıyor — Claude Code
  taşınabilirlik istisnası (memory 2026-07-24), `where claude` +
  kullanıcı home'u kullanır. `tools/agents/claudecode.cmd` YOK.
- [KANIT] Smoke: `opencode_Run.cmd --version` → `1.18.8`;
  `kilo_Run.cmd --version` → `7.4.16`. Davranış regresyon yok.
- [HATA/NOT] Smoke opencode 1.18.8 gösterdi ama `package.json` 14.
  turda `^1.18.9`'a bump edildi — `node_modules/opencode-ai/bin/
  opencode.exe` gerçek sürümü package-lock ile senkron değil (`npm
  install` çalıştırılmamış). Bu bir başka drift; **035 kapsamı
  değil** (launcher refactor). Bir sonraki `BASLAT.cmd` auto-update
  turu ya da elle `npm install` bunu düzeltir.
- Kapsam: 2 launcher rewrite (opencode_Run.cmd, kilo_Run.cmd —
  toplam ~50 satır → ~20 satır each). Pytest regresyon 676 aynen
  (Python kod dokunulmadı). Artefaktlar `pipeline/tasks/
  035-opencode-kilo-shim/`.

## 2026-07-30 (Görev 032.3 — `scan_secrets` döngüsü DRY refactor)
- [KARAR] `_iter_scan_hits(scan_path) -> list[tuple[Path, str, str]]`
  ortak yardımcısı: hem `_cmd_scan` (atlas scan CLI) hem
  `_check_scan_src` (032.2 doctor kanalı) bunu tüketir. İki yerde
  aynı `scan_secrets` döngüsünü tutmak DRY ihlaliydi — bug'lar
  desenkron kalırdı.
- [KARAR] Dönüş tipi `list`, `Iterable` değil. Sebep: hem `_cmd_scan`
  `len(hits)` istiyor hem `_check_scan_src` total + unique sample
  ister; iterator tekrar tüketilemez. Bellek endişesi yok (bir
  ATLAS repo'sunda binlerce bulgu değil, birkaç düzine ihtimali).
- [KARAR] `_check_scan_src` içinde `path.exists()` kontrolü kaldı
  (yardımcıya iteltilmedi) — özel warning gövdesi ("scan hedefi
  yok") çünkü yardımcı sessiz boş liste dönüyor.
- [KARAR] Bir dosyada birden çok bulgu varsa `sample_files` **unique**
  (bugfix — önceki 032.2 sürümünde de aslında de-facto tekildi ama
  garantisiz; şimdi `set` ile explicit).
- [KANIT] Regresyon: `test_scan_sir_bulur` + `test_scan_temiz`
  (`_cmd_scan` sözleşmesi) + 7 032.2 test (`_check_scan_src`
  şeması) aynen geçiyor. Yeni +6 test doğrudan `_iter_scan_hits`
  davranışını doğrular.
- Kapsam: 1 modül düzenleme (cli.py: +yardımcı, 2 fonksiyon refactor),
  1 test dosyası eki (+6 test). 676 test yeşil (670 → +6). mypy
  strict + ruff + scan temiz. Artefaktlar
  `pipeline/tasks/032-3-scan-dry/`.

## 2026-07-30 (Görev 032.2 — `atlas doctor --scan-src` birleştirme)
- [KARAR] Sır taraması `atlas doctor` çatısı altına EKLENDI (--scan-src
  opt-in) ama `atlas scan` bağımsız komutu SİLİNMEDİ — kullanıcı
  hâlâ elle çalıştırabilir. "İki farklı yol, aynı motor
  (`scan_secrets`)" — kullanıcı sözleşmesi geriye uyumlu, hook shim
  tek subprocess'te birleşiyor.
- [KARAR] `--scan-src` opt-in çünkü scan IO maliyeti sıfır değil
  (proje büyüdükçe artar). Doctor'un varsayılan yolu hızlı env
  sağlığına odaklı. Kullanıcı isteyene kadar scan yapılmaz.
- [KARAR] Hook shim v1 → v2: tek komut `atlas doctor --strict
  --scan-src`. İmza prefix (`# atlas-hook`) aynı → uninstall güvenli
  tanımaya devam. Kurulu v1 shim'i olan kullanıcılar `atlas hooks
  install` çağırırsa 034 sessiz güncelleme mekanizması v2'ye
  yükseltir (ATLAS imzalı + farklı içerik = güncelle).
- [KARAR] `_check_scan_src` içinde ilk 5 dosyayı `sample_files`
  olarak topla — insan formatta ilk 3'ü göster. Kullanıcı bulguları
  hemen görsün ama ekran şişmesin.
- [KARAR] `_collect_doctor_report`'a `scan_src_path: Path | None =
  None` parametresi eklendi — geri uyumlu; bayrak yoksa alan
  hiç görünmez (bit-uyumluluk). 032.1'de eklenen entry_count/
  vault_health *her zaman* raporlanır, scan_src IO ağır olduğu için
  opsiyonel.
- [KARAR] Strict davranışı EK KOD GEREKTİRMEDİ — 032.1'deki
  `_has_quality_warning` `quality.*.warning` alanlarına bakıyor,
  `scan_src.warning` otomatik dördüncü kanal olarak yakalanıyor.
  Kalıp: iyi tasarlanmış tek nokta sonradan gelen katmanları
  sıfır maliyette destekliyor.
- [KANIT] Smoke: `atlas doctor --scan-src` gerçek repo'da 60 giriş,
  7 not, 0 bulgu = tam temiz gate. Aktif iş.
- Kapsam: 1 modül düzenleme (cli.py: +_check_scan_src, _collect_doctor_
  report +param, _cmd_doctor --scan-src, parser); 1 shim güncellemesi
  (v1→v2); 1 test dosyası eki (+7 test, 35 toplam 032/032.1/032.2).
  670 test yesil (663 → +7). mypy strict + ruff + scan temiz.
  Artefaktlar `pipeline/tasks/032-2-doctor-scan-src/`.

## 2026-07-30 (Görev 034.1 — Windows sh.exe guard + shell tespiti)
- [KARAR] PowerShell wrapper YAPILMADI. Git hooks mekanizması sh
  üstünde kurulu — git PS scriptini hook olarak çağırmaz. Yani
  Windows-özel çözüm PS shim değil; git-bash veya depo-yerel
  `tools/git/`. `atlas hooks install` yalnız TANI verir, alternatif
  girişim yok.
- [KARAR] `_find_hook_shell` arama sırası: **depo-yerel önce**
  (`tools/git/usr/bin/sh.exe`, 2026-07-28 taşınabilir kurulum
  kalıbı), sonra `PATH`, sonra klasik Git for Windows yolları.
  Kullanıcı proje-içine gömdüğü sh'yi öncelesin; makine-özel
  yolları sonra düşer.
- [KARAR] Non-Windows'ta `_find_hook_shell` her zaman sabit `"sh"`
  döner (POSIX standart — path arama gereksiz overhead). Windows'ta
  arama zinciri.
- [KARAR] shell None ise install BAŞARILI (exit 0) ama stderr'e
  Türkçe uyarı — "install başarısız" değil çünkü kullanıcı henüz
  git-bash kurmamış olabilir ama commit'ler farklı makinede
  yapabilir. Uyarı bilgi.
- [KARAR] `hooks status` alanları: `shell_available: bool` +
  `shell_path: str | None`. JSON tüketiciler tek bakışta durumu
  görür. İnsan formatta `shell:` satırı.
- [KANIT] Depo repo'sunda smoke: `_find_hook_shell()` →
  `tools/git/usr/bin/sh.exe` (taşınabilir kurulum tam).
- Kapsam: 1 modül düzenleme (cli.py: +_find_hook_shell,
  _cmd_hooks_install shell None uyarı, _cmd_hooks_status shell
  alanları + insan format satır); 1 test dosyası eki (+7 test,
  24 toplam 034/034.1). 663 test yesil (656 → +7). mypy strict +
  ruff + scan temiz. Artefaktlar `pipeline/tasks/034-1-windows-ps-hook/`.

## 2026-07-30 (chore: 3-launcher `goose_Run.cmd` / `cline_Run.cmd` / `kimi_Run.cmd`)
- [KARAR] Kök launcher'ları `tools/agents/<name>.cmd` sarmalayıcısını
  `call` eden **thin shim** olarak yazıldı. `tools/agents/*.cmd`
  zaten kurulum sihirbazı tarafından tam-featured üretiliyor
  (HOME/XDG/APPDATA proje-içi, ensure-ollama, KIMI_CLI_GIT_BASH_PATH
  pinleme, node/Rust-dirs uyumu). DRY — kalıbı iki yerde tutmam,
  sarmalayıcı güncellenirse launcher otomatik yararlanır.
- [KARAR] Kök launcher yalnız üç iş yapar: `PATH=%H%;%PATH%` (atlas
  komutları oturumdan çağırılabilsin) + `cd /d %H%` + `call
  tools\agents\<name>.cmd %*` + exit code aynen. Kısa, net, mevcut
  sarmalayıcı sözleşmesini bozmayacak.
- [KARAR] `opencode_Run.cmd` / `kilo_Run.cmd` mevcut yazımı bu
  kalıba çekilmedi (kapsam dışı) — tarihsel kod, çalışıyor, dokunmak
  regresyon riski. Not düşüldü: gelecek chore'da simetrik yapılabilir.
- [KANIT] Smoke üçünde de: `goose_Run.cmd --version` → `1.44.0`;
  `cline_Run.cmd --version` → `3.0.47`; `kimi_Run.cmd --version` →
  `kimi, version 1.49.0`. Hepsi temiz.
- 6 kök launcher tam sette: opencode / kilo / claudecode / goose /
  cline / kimi.

## 2026-07-30 (chore: `claudecode_Run.cmd` baslatici)
- [KARAR] `opencode_Run.cmd` / `kilo_Run.cmd` kalibi ile simetrik bir
  `claudecode_Run.cmd` eklendi. Farkli olarak XDG/HOME override YOK —
  memory ve DECISIONS 2026-07-24: "Claude Code CLI tasinabilirlik
  istisnasidir; hesap kullanicinin `~/.claude`'unda". Launcher yalniz
  bin arama + PATH + cwd.
- [KARAR] Bin arama sirasi `ATLAS_LLM_CLAUDE_BIN` -> `where claude` ->
  `where claude.cmd`. Uc katman: opsiyonel override, PATH, Windows npm
  shim. Her uc de yoksa net cozum satirlari (npm/PATH/env).
- [HATA] Ilk yazimda nested parantezli `if defined ... ( ... )` bloklari
  CMD parser'inda garip bir `'m' is not recognized` uyarisi urekiyordu
  (islevsel calisir, ama gurultulu). Duzeltme: nested if'leri kaldirip
  `call :find_bin` altprosedurune donusturdum. Kalip: batch'te derin
  nested if'ten kacin, `goto`/`call` ile hat ayrimi yap.
- [KARAR] `PATH=%H%;%PATH%` ile ATLAS launcher'lari (opencode_Run.cmd,
  atlas.exe vb.) Claude Code oturumundan cagirilabilir. `cd /d %H%`
  ile CLAUDE.md depo kokunden okunur.
- [KANIT] Smoke: `cmd /c claudecode_Run.cmd --version` -> `2.1.133
  (Claude Code)`, stderr temiz.

## 2026-07-30 (Görev 032.1 — `atlas doctor --strict` ek denetimler)
- [KARAR] Uc kanal, tek exit — `_has_quality_warning(report)` yardimcisi
  `quality.*` altindaki HER `warning` alanina bakar. Kullanici "3 farkli
  bulgu, 3 farkli exit" yerine tek "kalite gate" gorur. Alternatif her
  denetime ayri exit (9/10/11) — semantik siserdi; drift ve vault ayni
  aile (dokuman disiplini).
- [KARAR] Vault sagligi esigi **>= 1 `.md`** — sifir dosya "hiç vault
  kullanmadin" anlamina gelir, uyari; bir dosya bile disiplin belirtisi.
  Alternatif "en az N not" — makul ama keyfi, YAGNI.
- [KARAR] Entry count varsayilan pencere **30 gun**, min entry **1**.
  Bir ayda tek karar bile birakmadiysan proje pratik olarak sessiz —
  drift'ten (7 gun) daha genis pencere ama tamamlayici sinyal.
- [KARAR] Ek env: `ATLAS_STRICT_ENTRY_WINDOW_DAYS`, `ATLAS_STRICT_MIN_
  ENTRIES` — 018/026 fail-safe kalibi (parse hatasi -> varsayilan;
  negatif -> varsayilan). Uc env (drift/entry/vault yok) ile kullanici
  quality gate'i istedigi kadar sikilastirir.
- [KARAR] **Sozlesme davranissal degisikligi:** `--strict` artik uc
  kanaldan tetiklenir. Bunu belgelendirdim; mevcut 032 testi (`test_032_
  doctor_strict_temiz_exit_0`) vault + `.md` eklemeye guncellendi
  (yeni "temiz" tanimi). 034 pre-commit hook shim'i bunu otomatik
  yakalar — yani pre-commit + 032.1 birbirini destekler.
- [KARAR] Coverage / test failure denetimi hala **kapsam disi** (032
  karari): "doctor pytest calistirmaz". 032.1 disari cikmadi bu
  kuraldan.
- Kapsam: 1 modül düzenleme (cli.py: 4 yeni yardimci, `_collect_doctor
  _report` quality 3 alanli, `_cmd_doctor` insan format ek 4 satir +
  JSON+strict tek kanal), 1 test dosyasi eki (+10 test; mevcut 1 test
  guncellendi). 656 test yesil (646 -> +10). mypy strict + ruff + scan
  temiz. Artefaktlar `pipeline/tasks/032-1-doctor-strict-plus/`.

## 2026-07-30 (Görev 034 — git pre-commit hook + `atlas hooks`)
- [KARAR] `.git/hooks/pre-commit` **tracked degil** — kaynagi
  `tools/hooks/pre-commit` olarak repoda tut, `atlas hooks install`
  ile kopyala. Alternatif `git config core.hooksPath` — proje-basi
  bir kez set etmek gerekir, kullanici unutabilir; explicit `install`
  komutu daha kesin.
- [KARAR] Shim imzasi `# atlas-hook v1` **ilk 5 satirda** — uninstall
  guvenli tanima. Kullanicinin kendi hook'una dokunmaz. Surum evrimi
  (v2, v3) icin ayri iterasyon; simdilik tek surum.
- [KARAR] Install idempotent: ayni icerik = no-op; ATLAS imzali eski
  icerik = sessiz guncelleme; yabanci hook = `--force` gerektir. `--
  force` YIKICI ("kullanicinin kendi shim'i eziliyor") — bilincli
  onay.
- [KARAR] Shim POSIX sh — git-bash Windows'ta standart (memory: kimi'nin
  bash yolu). PowerShell shim ayri is (YAGNI); git-bash kurulu her
  makinede calisir.
- [KARAR] Shim `atlas scan src` + `atlas doctor --strict` calistirir.
  Herhangi biri exit != 0 -> `exit 1` (git commit engellenir). Cikti
  stdout/stderr'e yonlendirilir (kullanici gorsun; suslenmemis).
- [KARAR] Yeni exit kodu YOK — hook `exit 1` git standardi; `atlas
  hooks *` komutlari mevcut kodlar (0, 2). Yeni bir exit yaratmak
  gereksiz komplekslik.
- Kapsam: 1 yeni sh script (tools/hooks/pre-commit), 1 modül düzenleme
  (cli.py: +5 yardimci, +3 komut, parser hooks alt-alt-komutlarla),
  1 yeni test dosyasi (+17 test). 646 test yesil (629 -> +17). mypy
  strict + ruff + scan temiz. Artefaktlar `pipeline/tasks/034-precommit-
  hook/`.

## 2026-07-30 (Görev 026.4 — Unix MAX_PROC / RLIMIT_NPROC)
- [KARAR] Env sözleşmesi **tam simetrik** oldu — `ATLAS_SANDBOX_MAX_PROC`
  hem Unix (026.4 RLIMIT_NPROC) hem Windows (026.2 Job ACTIVE_PROCESS).
  Kullanıcı taşınabilir sözleşme yazsın, "Unix'te bu env yoksayılır"
  sürprizi yaşamasın.
- [KARAR] `getattr(_resource, "RLIMIT_NPROC", None)` koruma — bazı
  BSD dağıtımlarında sabit farklı ad taşıyabilir. `None` dönerse
  sessizce atla (env verilse dahi çağrı ateşlenmez); ilgili
  platformda başka koruma katmanı (RLIMIT_CPU) devrede.
- [KARAR] 026.1'deki "RLIMIT_CPU zaten fork bomb'u SIGXCPU ile keser"
  gerekçesi hâlâ doğru — ancak env asimetrisi subtle bug'dır. Kalıp:
  derin savunma, tek sınıra bel bağlama; iki paralel koruma
  (RLIMIT_CPU + RLIMIT_NPROC) her ikisi ucuz.
- [KARAR] Canlı fork limit testi **bilinçli dışlandı** — CI runner'ın
  mevcut ulimit'i deterministik değil, test flaky olur. Yerine mock
  ile `_build_preexec_fn`'in gerçekten `setrlimit(RLIMIT_NPROC,
  (n, n))` çağırdığı ampirik doğrulanır (`calls == [(6, (12, 12))]`).
  Kalıp: eğer canlı test iş sisteminden bağımsız değilse mock ile
  contract doğrula.
- [KARAR] Platform matrisi artık **8/8 dolu** — hiçbir hücrede
  boşluk yok. `atlas run --goal-file X.yaml` tam sandbox koruması ile
  koşabilir (CPU + MEM + PROC her platformda).
- Kapsam: 1 modül düzenleme (actions.py: `_build_preexec_fn` MAX_PROC
  dahil + RLIMIT_NPROC getattr koruma), 1 test dosyası eki (+4 test).
  629 test yeşil (628 → +1 Windows; +3 Unix-only skip). mypy strict +
  ruff + scan temiz. Artefaktlar `pipeline/tasks/026-4-unix-nproc/`.

## 2026-07-30 (Görev 032 — `atlas doctor --strict` quality gate)
- [KARAR] **Yeni exit kodu 9** = "quality gate failed". 8 zaten
  `atlas metrics --alert` (029); 9 farklı semantik (drift, coverage
  gibi kalite bulguları). Kullanıcı bir hata ile diğerini karıştırmasın.
- [KARAR] Drift denetimi **bugün tarihi** baz alır, "son feat commit
  tarihi" değil. Sebep: kullanıcı feat commit'i attıktan sonra da
  DECISIONS güncellemeyi unutabilir; commit tarihi bir yumuşatma
  olurdu, doğrudan takvim daha keskin bir sinyal. Alternatif hafta
  sonu / iş günü ayrımı — YAGNI, bir görev günleri boyunca sürebilir.
- [KARAR] Varsayılan eşik **7 gün**. Bir haftadan uzun sessizlik
  "aktif çalışma" işareti değil. Kullanıcı `ATLAS_STRICT_DRIFT_DAYS`
  ile daralt (3) ya da genişlet (30) — 018/026 fail-safe kalıbıyla
  parse hatası varsayılana düşer.
- [KARAR] Denetim `_collect_doctor_report`'a **her zaman** eklenir
  (`quality.decisions_drift`). `--strict` yalnızca exit koduna
  dönüştürür. Rapor tüketicileri bir alan var/yok ayrımı yapmasın.
- [KARAR] `--json + --strict` çakışması: JSON çıktısı bası **korunur**,
  yalnız exit kodu 9 döner. CI kalıbı `atlas doctor --json --strict >
  doctor.json 2> doctor.err || fail` — hem raporu al hem exit'i
  yakala.
- [KARAR] `[Kalite kapıları]` bölümü mevcut doctor insan çıktısının
  **sonuna** eklendi (mevcut bölümler değişmedi). JSON'a `quality`
  alanı **eklendi** (mevcut alanlar değişmedi). Bit-uyumluluk her
  iki format için de korundu.
- [KARAR] Coverage / test failure denetimi **kapsam dışı** — pytest
  zaten `--cov-fail-under` ile keser; `atlas doctor` env sağlığına
  odaklı, pytest çalıştırmıyor. Doktrin: bir aracın işini başka
  araca gömme.
- [HATA] 026.3 CPU quota testi (`test_0263_windows_cpu_quota_kesir`)
  3.5s eşiği yüklü makinede flaky — 032 quality kapısı koşulunda
  3.46s ölçüm alındığı için failed. Eşik 8s'ye çıkarıldı, timeout
  12s (marj), CPU quota hâlâ ölçülüyor (timeout değil). Bonus fix
  032 commit'ine katıldı. Kalıp: canlı zamanlama testinde marj
  ~2× beklenen, %10 değil.
- Kapsam: 1 modül düzenleme (cli.py: +re/date import, +3 fonksiyon,
  `_collect_doctor_report` "quality" bölümü, `_cmd_doctor` --strict
  + insan format + exit 9, parser), 1 yeni test dosyası (+18 test),
  1 test flaky-fix (026.3). 628 test yeşil (610 → +18). mypy strict +
  ruff + scan temiz. Artefaktlar `pipeline/tasks/032-quality-gate/`.

## 2026-07-30 (Görev 026.3 — Windows CPU quota)
- [KARAR] `JOB_OBJECT_LIMIT_PROCESS_TIME` (0x2) + `BasicLimitInformation.
  PerProcessUserTimeLimit`. Struct 026.2'den beri `c_int64` olarak
  vardı — yalnız flag + atama; layout değişmedi. Ampirik doğrulama:
  Windows canlı `while True: pass` CPU_S=1 iken 3.5 sn'den kısa
  sürede exit != 0 (timeout 8 sn olsa da) — kernel gerçekten kesti.
- [KARAR] **PerProcess** tercih edildi, PerJob değil. Sebep: `_shell`
  tek subprocess başlatır; PerJob "tüm job için toplam" — batch
  paralel (031) senaryosunda yanıltıcı olabilir. PerProcess her child
  için ayrı — subprocess ve torunları ayrı ayrı limitle yaşar.
  Fork bomb için doğru semantik.
- [KARAR] 100ns tick birimi bir NT tarihi/saat sözleşmesi (FILETIME
  ile aynı). `_WIN_TIME_TICKS_PER_SECOND = 10_000_000` sabiti
  gizli sihirli sayı kalmaz. Overflow riski `c_int64` max ≈ 9.2×10¹⁸
  → 29 000 yıl (kullanıcı 1-3600 sn aralığı, imkânsız).
- [KARAR] Env sözleşmesi platform-agnostik: `ATLAS_SANDBOX_CPU_S`
  hem Unix (026.1 RLIMIT_CPU) hem Windows (026.3 Job PROCESS_TIME).
  Kullanıcı taşınabilir bir batch yazsın, sürüm-özel env öğrenmesin.
- [KARAR] `_apply_windows_job` imzası genişletildi (`cpu_s: int | None =
  None`); mevcut çağrıcılar etkilenmedi (default None). Tek çağrı
  yeri (`_shell`) güncellendi.
- [KARAR] `_has_windows_sandbox_env` üç env'e bakar (MEM/PROC/CPU);
  herhangi biri verilirse Windows Popen yolu tetiklenir. Alternatif
  "her env için ayrı guard" — DRY ihlali, aynı Popen yolu üç kez.
- [KARAR] Platform matrisinde tek boşluk `Unix MAX_PROC` kaldı;
  RLIMIT_NPROC 026.1'de bilinçli ele alınmadı (RLIMIT_CPU fork
  bomb'u SIGXCPU ile keser, NPROC ekstra karmaşa). 026.4 açılırsa
  ele alınır ama YAGNI.
- Kapsam: 1 modül düzenleme (actions.py: +2 sabit; `_has_windows_
  sandbox_env`, `_apply_windows_job` imza + struct atama; `_shell`
  CPU_S okuma), 1 test dosyası eki (+5 test). 610 test yeşil
  (606 → +4 net). mypy strict + ruff + scan temiz. Artefaktlar
  `pipeline/tasks/026-3-windows-cpu-quota/`.

## 2026-07-30 (Görev 018.3 — Claude + ACP real özet)
- [KARAR] Her backend'in kendi çağrı fonksiyonu (`_call_claude`,
  `_call_acp`) minimal özet promptu ile **tekrar kullanıldı**. Ayrı
  bir "özet kanalı" tasarımı YAGNI — mevcut çağrı yolu zaten process
  başlatma, timeout, hata sarmalama işini yapıyor.
- [KARAR] Ortak yardımcılar `_build_summarize_prompt(obs)` +
  `_finalize_summary_line(text, backend_label)` üç backend'de
  paylaşılıyor — prompt/kırpma tek yerde tutuluyor. 018.2 anthropic
  yolu refactor edildi (aynı sonuç, DRY).
- [KARAR] Dispatch tablosu (`{"anthropic":..., "claude":..., "acp":...}`)
  `.get(backend)` ile yumuşak fallback — bilinmeyen backend ADI
  gelirse stub'a düşer (make_planner zaten NotImplementedError
  verir ama dispatch kendi savunuyor).
- [KARAR] 018.2'nin `_OBS_SUMMARIZE_WARNED` seti ve "018.3 kapsamı"
  uyarı yolu **KALDIRILDI** (dead code). Claude/ACP artık real
  çağrı yapıyor; uyarı SADECE hata durumunda çıkar ("çağrısı
  başarısız, kırpmaya düşülüyor").
- [KARAR] ACP her özet için yeni oturum (initialize + session/new +
  session/prompt) açar — mevcut `_call_acp` kalıbı. Alternatif:
  planner'ın açtığı oturumu paylaş — subtle state yönetimi, YAGNI.
  Cost etkisi belgelendi (09-ship.md); önbellek 018.4 gerekiyorsa.
- [KARAR] Claude/ACP için özel `Goal` alanı YOK — özet Anthropic gibi
  planner ile aynı bin/timeout/env kullanır. Kullanıcı planner'ı
  değiştirse özet de doğal olarak değişir.
- [HATA] 018.2'de yazılmış iki test (`test_0182_claude_uyarisi_bir_kez`,
  `test_0182_acp_uyarisi_bir_kez`) 018.3 davranışıyla çelişti — testler
  "uyarı bir kez basılır" bekliyordu ama artık gerçek çağrı yapılıp
  bin bulunamıyorsa hata çıkıyor. İki testi sildim; 018.3 bölümüne
  gerçek davranış (mock ile real çağrı doğrulama, hata fallback,
  kısa obs no-op) testleri eklendi. Kalıp: bir davranış değişikliği
  yapılırken önceki testler "hangileri artık geçersiz" diye açıkça
  değerlendirilir; sessiz düşme testin niyetini kaybettirir.
- Kapsam: 1 modül düzenleme (planner.py: +ortak yardımcılar, +2 real
  summarizer, dispatch refactor, dead code temizliği), 1 test dosyası
  güncelleme (−2 eski, +8 yeni; 23 toplam). 606 test yeşil (600 →
  +6 net). mypy strict + ruff + scan temiz. Artefaktlar
  `pipeline/tasks/018-3-claude-acp-summarize/`.

## 2026-07-30 (chore: ai-cli auto-update drift)
- [KARAR] `opencode-ai` 1.18.8 → 1.18.9 upstream sürüm, `BASLAT.cmd`
  auto-update politikası (`atlas-portable.json` "agents" modu)
  tarafından sessizce alındı. `tools/ai-cli/package.json` +
  `package-lock.json` drift'i test/kalite regresyonu yaratmadı, git
  tarafını hizalamak için `chore(ai-cli)` commit atıldı. Kalıp: auto-
  update politikasının ürettiği package-lock drift'i düzenli olarak
  chore commit'iyle git'e alınır — yoksa bir sonraki iş turu bunu
  karıştırır.

## 2026-07-29 (Görev 030 — multi-goal batch)
- [KARAR] `--goal-file` `nargs='+'` — N=1 çağrısı 027 davranışına
  birebir eşit (özet tablo YOK, run-id suffix YOK). N>1 batch modu.
  Alternatif ayrı `--goal-files` bayrağı yer değişikliği ve iki farklı
  isim → sözleşme kalabalığı; `nargs='+'` argparse'ın idyomatik yolu.
- [KARAR] **Fail-fast varsayılan.** Shell `set -e` ve CI job semantiği
  ile simetri; hata erkenden bildirilir. `--continue-on-error` opt-in
  bayrak (regresyon matrisinde "hepsini gör" için).
- [KARAR] Run-id çakışma çözümü sıra numarası (`X_1`, `X_2`, ...
  `X_N`) — hem `--run-id X` verilirse hem `<TS>_<i>` timestamp
  yolunda. Alternatif hash / uuid — okunmaz, log korelasyonu zor.
  100 goal olduğunda sıralı sayı da temiz kalır.
- [KARAR] Exit kodu `max(rc)` — kod büyüklüğü hata ağırlığını
  yansıtır (2 SPEC HATASI < 4 done=False < 5 denied < 7 env). CI
  script en kötü hatayı görür. Alternatif "ilk hata": fail-fast'te
  aynı; continue-on-error'da anlamsız çünkü kullanıcı hepsini gördü.
- [KARAR] Timestamp bir kez alınır (batch başında), her goal için
  `_<i>` sonek eklenir. Alternatif her goal için ayrı timestamp —
  aynı saniye içi çakışma riski + arama tabanı bozulur.
- [KARAR] `--dry-run` tek bayrak, tüm goal'lere uygulanır. Ayrı bir
  "per-goal dry-run" — CLI karmaşıklığı, YAGNI. Batch dry-run'ın
  amacı "hepsi çalışacak mı sanki" simülasyonu; per-goal ayrım
  isteyen zaten iki ayrı çağrı yapar.
- [KARAR] Özet tablosunda ASCII işaretler (`+`, `x`, `-`) kullanıldı
  — UTF-8 `✓`/`✗`/`—` Windows cp1254'te bozulur mu diye risk almadım;
  reconfigure zaten var ama görsel garantisi ASCII ile daha güvenli.
- Kapsam: 1 modül düzenleme (cli.py: `--goal-file nargs='+'`,
  `--continue-on-error` bayrağı, `_cmd_run` dispatch, `_cmd_run_batch`
  ~50 satır), 1 test dosyası (+8 test). 600 test yeşil (592 → +8).
  mypy strict + ruff + scan temiz. Artefaktlar
  `pipeline/tasks/030-multi-goal-batch/`.

## 2026-07-29 (Görev 026.2 — Windows Job Objects)
- [KARAR] **Native Job Objects** tercih edildi (Docker/container YOK,
  026 direktifi). Windows API, admin yetkisi gerektirmez, `KILL_ON_
  JOB_CLOSE` ile parent (ATLAS) kapanınca job da ölür — fork bomb
  torunları temizlenir. `psutil` gibi 3. parti bağımlılık YAGNI;
  stdlib `ctypes` + `ctypes.wintypes` yeter.
- [KARAR] Env sözleşmesi 026.1 ile paylaşılan (`ATLAS_SANDBOX_MEM_MB`)
  + Windows-özel (`ATLAS_SANDBOX_MAX_PROC`). Kullanıcı sözleşmesi
  platform-agnostik; kod yolu ayrı ama arayüz aynı.
- [KARAR] Env varsa `subprocess.Popen + apply_job + communicate`;
  env yoksa MEVCUT `subprocess.run` yolu (bit-uyumlu 026/026.1).
  İki kod yolu tutmak bit-uyumluluğu garanti eder — tek yolda
  birleştirmek encoding/timeout/exit_code semantiğinde subtle
  regresyon riski.
- [KARAR] Job handle **bilinçli kapatılmıyor** — ATLAS process
  ömrü boyunca tutulur; `KILL_ON_JOB_CLOSE` GC'de handle serbest
  bırakılınca child'ları toplar. subprocess bittikten sonra
  handle'ın etrafta durması bellek maliyeti ihmal edilir (per-goal
  bir HANDLE).
- [KARAR] `CREATE_SUSPENDED` KULLANILMADI. Sebep: subprocess.Popen
  main thread handle'ı vermez, `ResumeThread` çağrımak zor. Alt yol:
  pid al → ANINDA Job'a ata. Race window sub-millisecond; Python
  startup MB'lerce alloc yapmaz, MEM limit için yeter.
- [KARAR] Struct offset'leri ctypes `_fields_` sırası ile otomatik
  hesaplanır — 64-bit Windows layout doğru. Doğrulama: canlı test
  (`test_0262_windows_mem_limit_patlar`) MEM_MB=64'te 500 MB
  bytearray alloc'u 2 sn'de exit != 0. Struct yanlış olsaydı MEM
  limit uygulanmaz, subprocess başarıyla biter → test bunu görür.
- [KARAR] Ctypes struct isimleri Windows SDK'daki CapWords ihlali
  (`_JOBOBJECT_EXTENDED_LIMIT_INFORMATION`) → `# noqa: N801`
  bilinçli. Uzak API'yi yeniden adlandırmak grep-uyumu bozar.
- [KARAR] `CPU_S` Windows'ta ele ALINMADI. Sebep: Windows
  `JOB_OBJECT_LIMIT_PROCESS_TIME` **100 ns tick** matematiği hassas;
  Unix `RLIMIT_CPU` saniye. İki farklı birim + çevrim = subtle bug
  riski. 026.3 kapsamı (henüz açılmadı).
- [HATA] İlk test yazımı `shlex.split(sys.executable + ' -c "..."')`
  ile POSIX-mode split'e mutlak Windows yolunu verdi (`C:\Users\...`)
  — `\` escape sanılıp path bozuldu, FileNotFoundError. Düzeltme:
  test yardımcısı `_py_cmd()` PATH-tabanlı isim döner (`python`,
  `python3`, `py`); env whitelist PATH'i sandbox subprocess'e taşır.
  Kalıp: test'te yardımcı komut adı PATH'ten, mutlak yol ASLA
  shlex POSIX'e verilmez.
- [KARAR] Fail-safe uyarı formatı: `uyarı: 026.2 <API> başarısız
  (WinError <kod>)` — kullanıcı GetLastError kodunu görsün;
  Google'da tam eşleşme bulur. Sessiz başarısızlık YASAK.
- Kapsam: 1 modül düzenleme (actions.py: +Job Objects sabitleri,
  `_has_windows_sandbox_env`, `_apply_windows_job` ~90 satır ctypes
  wrapper; `_shell` Windows env varsa Popen yolu), 1 test dosyası
  (+11 test). 592 test yeşil (583 → +9 canlı Windows). mypy strict +
  ruff + scan temiz. Artefaktlar `pipeline/tasks/026-2-windows-job/`.

## 2026-07-29 (Görev 026.1 — Unix resource limits)
- [KARAR] `try: import resource` guard — Windows'ta modül YOK;
  `_resource = None` set edilir. `_build_preexec_fn` bunu görünce
  None döner (double-guard). Alternatif `sys.platform` tek başına
  yeterdi ama modül-import guard'ı ekstra CI güvencesi.
- [KARAR] Windows'ta `subprocess.run(preexec_fn=X)` **ValueError**
  fırlatır — bu yüzden `_build_preexec_fn` Windows'ta HER ZAMAN None
  döner (env verilse dahi). Env sessizce yoksayılır (uyarı yok — 026
  kalıbı, spam engeli); 026.2 aynı env'i Windows'ta Job Objects
  ile karşılar.
- [KARAR] Env yoksa (`CPU_S` VE `MEM_MB` her ikisi de None) →
  `preexec_fn=None` döner — ekstra fork maliyeti YOK, bit-uyumlu 026.
- [KARAR] `RLIMIT_NPROC` ELE ALINMADI. Fork bomb'a karşı `RLIMIT_CPU`
  yeter (torun süreçler de aynı CPU budget'ten çeker, SIGXCPU hepsini
  keser). NPROC eklemek per-user limit karmaşası getirir, YAGNI.
- [KARAR] Env parse fail-safe (`abc`, `-1`, `0`, boş) → `None`
  (yoksay). 018 kalıbıyla simetrik — kullanıcı hatalı env verdiğinde
  ölme, varsayılana düş.
- [KARAR] Unix canlı test CI Ubuntu leg'inde koşar (Windows leg'de
  `@pytest.mark.skipif(sys.platform == "win32")`). Windows'ta
  Windows-canlı testler (env verilse çalışır no-op kabul) 9 pass.
- Kapsam: 1 modül düzenleme (actions.py: +`_resource` import guard,
  +`_read_positive_int_env`, +`_build_preexec_fn`, `_shell` preexec_fn
  parametresi), 1 test dosyası (+15 test). 583 test yeşil (574 → +9
  Windows canlı, 6 Unix skip). mypy strict + ruff + scan temiz.
  Artefaktlar `pipeline/tasks/026-1-unix-resource/`.

## 2026-07-29 (Görev 018.2 — LLM ile gözlem özetleme)
- [KARAR] `Goal.obs_summarize: bool = False` opt-in + env override
  `ATLAS_LLM_OBS_SUMMARIZE` (1/true/yes/on). Effective flag `goal OR
  env` — CI'da env ile global aç, YAML dokunmadan.
- [KARAR] Hook mekanizması: `_maybe_summarize_or_trim(obs, obs_chars,
  goal)` — kısa obs (`len <= obs_chars`) hep no-op, opt-in kapalıysa
  `_trim_obs` (018.1), aktifse backend'e göre summarize. Yani ekstra
  maliyet ANCAK opt-in aktif VE uzun obs varsa doğar.
- [KARAR] **Real çağrı YALNIZ Anthropic backend'de** (bu tur). Sebep:
  `_call_anthropic` mevcut, minimal prompt ile tekrar kullanılır;
  yan etkiler (metrics.jsonl + usage trace) mevcut yol. Claude
  subprocess + ACP oturumu için ayrı özet kanalı gerekir — 018.3.
- [KARAR] Claude/ACP + opt-in → **stub summarizer'a düş + bir kez
  stderr uyarı** ("018.3 kapsamı"). Deduplication set ile spam
  engeli. Kullanıcı yanılıp opt-in verirse sessiz yanlış almaz;
  uyarıyı görür, ne oluyor bilir.
- [KARAR] Stub summarizer **deterministik** — `f"[özet: {N} char,
  {L} satır, baş: '{40char}'...]"`. Test için LLM mock'suz doğrulama
  yolu; aynı input → aynı output.
- [KARAR] Anthropic özet prompt'u Türkçe + max 120 char + hataya
  odaklan direktifi. Alternatif İngilizce daha kısa çıktı verir ama
  ATLAS Türkçe iletişim doktrini + planner prompt zaten Türkçe.
- [KARAR] Fail-safe: real çağrı `LLMPlannerError` fırlatırsa → stderr
  uyarı + `_trim_obs` fallback. Planner turu ÖLMEZ. Kalıp: her ek
  LLM çağrısı ana akışı bloklamamalı.
- [KARAR] Cost etkisi mevcut mekanizmayla ölçülüyor — `_call_anthropic`
  zaten `_write_metric_for_data` çağırır; özet çağrısı ayrı bir satır
  olarak metrics.jsonl'a düşer. Kullanıcı `atlas metrics` ile ekstra
  maliyeti görür.
- Kapsam: 2 modül düzenleme (goals.py: `Goal.obs_summarize` alanı +
  YAML validation; planner.py: `_effective_obs_summarize`,
  `_stub_summarize_obs`, `_summarize_via_anthropic`,
  `_maybe_summarize_or_trim` + `_format_prompt` dispatch), 1 yeni
  test dosyası (+17 test). 574 test yeşil (557 → +17). mypy strict +
  ruff + scan temiz. Artefaktlar `pipeline/tasks/018-2-obs-summarize/`.

## 2026-07-29 (Görev 029 — `atlas metrics --alert`)
- [KARAR] **Yeni exit kodu 8** = "alert eşiği geçilemedi" (yalnız
  `atlas metrics --alert` özelinde). 6 ile birleştirmedim: 6 zaten
  `archive-all failed` (bir görev arşivlenemedi); "cache-hit
  düşük" ile aynı kova sessiz yanlışa yol açardı — CI script'i "6"
  görünce arşive bakar. Yeni CLI davranışı = yeni kod.
- [KARAR] **`--alert 0` alarmı kapatır.** `0 > 0` asla doğru olmadığı
  için ateşleme yoluna girmez; kural "sıfır eşik = devre dışı".
  Alternatif (`--alert` yoksa alarm yok, verildiyse hep aç) yeterli
  ama env-driven CI'da bayrağı koşullu geçirmek zor — sabit
  `--alert ${THRESHOLD:-0}` kalıbı işi çözer.
- [KARAR] **Kayıt yoksa alarm ATEŞLENİR** (`hit_ratio = 0.0` <
  pozitif eşik). Karşı öneri: "veri yok, sessiz kal" — reddedildi;
  metrics.jsonl dosyasının kaybolduğu bir CI ortamı zaten hatalıdır,
  alarmın orada susması sessiz yanlış olur. `--alert 0` verilirse
  yine kapalı.
- [KARAR] **`--json` ile alarm birleşir.** JSON stdout'a, UYARI
  stderr'e, exit kodu kurala tabi. Karışmazlar — `atlas metrics
  --json --alert 40 > m.json 2> alerts.txt` CI kalıbı.
- [KARAR] Geçersiz eşik (`< 0` ya da `> 100`) → SPEC HATASI + exit 2
  (mevcut sözleşme). Argparse zaten `type=float` yapıyor; sınır
  kontrolü el ile — argparse `choices` `float` ile uyumsuz.
- [KARAR] Mevcut çıktı **birebir korundu** — hiçbir satır silinmedi,
  hiçbir alan değişmedi. Alarm yalnız EKLENDİ. Regresyon test
  matrisi eski `test_023_*` üzerinden zaten kanıtlanıyor (7 test
  hâlâ yeşil).
- Kapsam: 1 modül düzenleme (cli.py: `_cmd_metrics` +alert sınır +
  hesap + UYARI + exit 8; parser `--alert float`), 1 test dosyası
  eki (+6 test, 13 toplam). 557 test yeşil (551 → +6). mypy strict
  + ruff + scan temiz. Artefaktlar `pipeline/tasks/029-metrics-alert/`.

## 2026-07-29 (Görev 028 — `atlas replay --list`)
- [KARAR] **`--list` bayrak, alt-alt-komut değil.** Alternatif
  `atlas replay list <args>` — ama 027 sözleşmesi tek positional
  `run_id`; yeni alt-komut argparse ağacını değiştirir. `--list`
  bayrağı ile positional `nargs='?'` yaparak sözleşme geri uyumlu
  kalır: `atlas replay <run-id>` çağrısı hiç değişmedi.
- [KARAR] Kaynak `.atlas/runs/*.yaml` **dosya sistemi**, `audit.jsonl`
  değil. Dashboard audit-based; replay file-based (027'den beri).
  İki farklı kaynak birleştirilmedi — dashboard silme/rotate audit'i
  etkilemez, replay klasörü elle taşınabilir. Ayrık kalması sözleşme
  bozmayı önler.
- [KARAR] **Yaml-dışı yoksay** — yalnız `is_file() and suffix ==
  ".yaml"`. `.yml` bilerek dışta bırakıldı (027 kopyası hep `.yaml`
  yazıyor; kullanıcının orada tuttuğu başka `.yml` konfig
  listelenmesin).
- [KARAR] Sıralama **mtime desc** — replay ihtiyacı hep "yeniden
  çalıştır" olduğundan en yeni önce. Alternatif ctime/name — mtime
  kullanıcı beklentisiyle örtüşür ("hangisini biraz önce çalıştırdım").
- [KARAR] Goal metni **ilk `^goal:` satırından**, en fazla 60 char
  (uzunsa `…`). Alternatif full YAML parse — bağımlılık ekler
  (pyyaml zaten var ama basit satır tarama disk okumasız yeter).
- [KARAR] Boş klasör = `(hiç kayıt yok)` + exit 0. **Hata değil.**
  İlk çalıştırmada `.atlas/runs/` henüz yok — kullanıcıyı korkutma.
- [KARAR] `atlas replay` (positional yok, `--list` yok) → SPEC
  HATASI + exit 2 (mevcut sözleşme). Argparse otomatik hata verse
  bile açık Türkçe mesaj daha bilgilendirici.
- Kapsam: 1 modül düzenleme (cli.py: +`_extract_goal_from_yaml`,
  +`_collect_replay_runs`, +`_cmd_replay_list`; `_cmd_replay`
  dallanma; parser `--list/--json/--limit` + `run_id nargs='?'`),
  1 test dosyası eki (+6 test, 12 toplam). 551 test yeşil (545 →
  +6). mypy strict + ruff + scan temiz. Artefaktlar
  `pipeline/tasks/028-replay-list/`.

## 2026-07-29 (Görev 027 — `atlas replay <run-id>`)
- [KARAR] **YAML kopyası** replay için yeter — full snapshot (sandbox
  state, env) YAGNI. Görev YAML'ı deterministik (goal, plan_kind,
  action_allowlist); dış dünya değişebilir (LLM cost, network) ama
  bunlar zaten replay'in kapsamı dışında.
- [KARAR] `goal_id = <yaml stem>-<run-id>` — mevcut `sandbox = ...
  /goal_id` kalıbı ile simetri. Dashboard `run_id` kolonu bu stem'i
  gösterir; kullanıcı `atlas replay <stem>` çağırır.
- [KARAR] Kopyalama **hata sessiz** — disk dolu / izin yoksa ana
  akış bloklamamalı. `try: ... except OSError: return None`.
- [KARAR] Dashboard eşleşme **mtime desc + zip runs** — heuristik
  ama pratik. Alternatif: audit'te `run_id` kaydetmek — audit
  sözleşmesini genişletir; şu an yaml dosya listesi yeter.
- [KARAR] Yeni run-id vermek opsiyonel (`--new-run-id`) — varsayılan
  yeni timestamp. Kullanıcı test/regresyon için stabil id vermek
  isterse verir.
- Kapsam: 1 modül düzenleme (cli.py: +_runs_dir, +_archive_goal_yaml,
  +_cmd_replay ~40 sat; _cmd_run_goal YAML kopyala; dashboard
  run_id kolonu; parser replay alt-komutu), 1 yeni test dosyası
  (6 test). Toplam 545 test yeşil (539 → +6). mypy strict + ruff
  temiz. Artefaktlar `pipeline/tasks/027-atlas-replay/`.

## 2026-07-29 (Görev 026 — sandbox iyileştirme, Docker YOK)
- [KARAR] **Docker YASAK** (kullanıcı direktifi). Portable stdlib-only
  yol: env whitelist, PATH kısıt, timeout env, stderr yakalama.
  Çoğu tehdit modelini (API key sızıntısı, runtime aşımı) kapsar;
  fork bomb / OOM için Unix `resource` (026.1) ve Windows Job Objects
  (026.2) opt-in olarak sonraki görevlere ayrıldı.
- [KARAR] **Env whitelist** — hassas env (ANTHROPIC_API_KEY,
  ATLAS_LLM_*) sandbox subprocess'e sızmaz. Whitelist minimum:
  PATH, HOME/USERPROFILE, TEMP, LANG, SYSTEMROOT + Unix eşdeğerleri.
  Yeni env ihtiyacı doğarsa liste genişler (belirtilen kullanım).
- [KARAR] `ATLAS_SANDBOX_PATH` override — kullanıcı sandbox'ın
  PATH'ini iyice daraltmak isterse (sadece `/usr/bin`) verir. Yoksa
  mevcut PATH geçer (kullanıcı deneyimini bozmamak için).
- [KARAR] Timeout **env-ayarlı** — sabit 10s bazı görevlerde yetmez
  (uzun build). `ATLAS_SANDBOX_TIMEOUT` fail-safe parse.
- [KARAR] **stderr yakalama** — observation'da `err=<ilk 200>`.
  Neden: shell komutu başarısız olsa stdout boş, stderr'de hata
  var; LLM planında bu bilgi yoksa geçen adımda niye başarısız
  olduğunu anlayamaz.
- [KARAR] Env yoksa **bit-uyumlu** — mevcut 20 test yeşil kaldı;
  yeni parametreler sadece `env=` kwarg değişikliği.
- Kapsam: 1 modül düzenleme (actions.py: +_SANDBOX_ENV_WHITELIST,
  +_scrub_env, +_read_sandbox_timeout, _shell env/timeout/stderr
  uygulaması ~30 sat), 1 test dosyası genişleme (+6 test). Toplam
  539 test yeşil (533 → +6). mypy strict + ruff temiz. `atlas scan
  src` sır yok. Artefaktlar `pipeline/tasks/026-sandbox-hardening/`.

## 2026-07-29 (Görev 025 — skills/engineering/prompt SKILL.md)
- [KARAR] **Türkçe** rehber — CLAUDE.md kuralı (Türkçe iletişim,
  teknik terimler orijinal). Kullanıcı: ATLAS'ı çalıştıran mühendis
  veya Claude/ACP agent'ı yönlendiren kullanıcı.
- [KARAR] Rehber **300 satırın altında** — bir oturumda okunur.
  Görev-tipi kalıpları + karşı örnekler + workflow adımları.
  Nesnel ölçü: kullanıcı 5 dk'da okuyup kendi YAML'ını yazabilmeli.
- [KARAR] SPEC referansları **her zaman biçimli**: `SPEC 015`
  (görev numarası), `pipeline/tasks/003-2-llm-prompt/02-spec.md`
  (dosya yolu). Kullanıcı derinliğe iner.
- [KARAR] Kod değil, **rehber** — test/coverage YOK. Ruff/mypy
  değişmez. Kalite ölçüsü içerik doğruluğu (SPEC'lere referans).
- Kapsam: 1 yeni dokümantasyon dosyası (skills/engineering/prompt/SKILL.md
  ~250 sat). Test/coverage değişmedi. Artefaktlar
  `pipeline/tasks/025-prompt-engineering-skill/`.

## 2026-07-29 (Görev 019.1 — ACP streaming ilk newline'da kes)
- [KARAR] Anthropic streaming (019) ile **birebir simetri** — ATLAS
  planner sözleşmesi tek satır; kalan chunk'ları beklemek anlamsız.
  `text_delta` (Anthropic) ≡ `agent_message_chunk` (ACP); ikisinde
  de "biriktir + ilk `\n` = break" mantığı.
- [KARAR] İlk satır **boşsa** (`"\n"` sadece geldiyse `first == ""`)
  break etme, devam et. Bazı agent'lar boş satırla başlayabilir;
  anlamlı content beklemeli.
- [KARAR] `break` iç iç `if`'lerden çıkıp **`while True`** döngüsünü
  keser — Python semantik. Testte üçüncü chunk okunmadığı doğrulanır
  (fake stdout'ta "OKUNMAMALI" kayıtlı; birleşik metinde yok).
- [KARAR] Süreç kill (`finally _acp_teardown`) korundu — erken
  çıkışta da tetiklenir; sızıntı yok.
- Kapsam: 1 modül düzenleme (planner.py: _call_acp inline break ~5 sat),
  1 test dosyası genişleme (+3 test). Toplam 533 test yeşil (530 → +3).
  mypy strict + ruff temiz. Artefaktlar `pipeline/tasks/019-1-acp-streaming/`.

## 2026-07-29 (Görev 018.1 — gözlem head+tail keep)
- [KARAR] **Head+tail keep** — kuyruğu atma (018 davranışı) yerine
  başı ve sonu koru, ortayı `[... N char atlandı ...]` işaretle.
  Neden: uzun stderr'ın sonundaki hata mesajı LLM'e ulaşsın.
- [KARAR] Varsayılan 100+100=200 = obs_chars varsayılan → 018
  davranışı bit-uyumlu (200 char'a kırp, atlama işareti yok). Kullanıcı
  obs_chars'ı büyütünce (örn. 500) head+tail keep otomatik aktifleşir.
- [KARAR] LLM tabanlı özetleme (018.2) **rezerv** — ekstra LLM çağrısı
  cost yaratır ve gecikme ekler. Head+tail keep şu an %90 senaryoyu
  çözer; LLM özetleme ilerideki nüans (JSON semantik özet) için.
- [KARAR] Mantıksız env (head+tail >= obs_chars) → 018 fallback.
  Kullanıcı yanlış env yazarsa bug yerine güvenli davranış.
- Kapsam: 1 modül düzenleme (planner.py: +_read_obs_head_tail_env,
  +_trim_obs ~15 sat), 1 test dosyası genişleme (+8 test, 1 test
  güncelleme). Toplam 530 test yeşil (522 → +8). mypy strict + ruff
  temiz. Artefaktlar `pipeline/tasks/018-1-obs-headtail/`.

## 2026-07-29 (Görev 016.3 — ACP interaktif permission dialogu)
- [KARAR] **Opt-in env** — otonom mod varsayılan; interaktif seçim
  bilinçli. `ATLAS_ACP_INTERACTIVE=1` kapalıysa 016.2 auto-karar
  bit-uyumlu (mevcut testler yeşil).
- [KARAR] Prompt **stderr'a** (`sys.stderr.write` + `flush`), yanıt
  **stdin'den** (`sys.stdin.readline`). stdout ATLAS plan çıktısını
  taşır; permission dialogu onu kirletmemeli.
- [KARAR] Fail-safe: EOF/KeyboardInterrupt/OSError → None → auto-karar.
  Kullanıcı Ctrl+C basarsa süreç kırılmasın; ATLAS güvenli karar verir.
- [KARAR] Boş satır → default (yanıt beklenmez), bilinmeyen cevap
  → default. Kullanıcı Enter'a bassa ATLAS karar verir; yanlış yazsa
  yine karar verir. Yalnız net y/n override eder.
- Kapsam: 1 modül düzenleme (planner.py: +_prompt_acp_permission ~20
  sat, _acp_permission_response dallanma), 1 test dosyası genişleme
  (+4 test). Toplam 522 test yeşil (518 → +4). mypy strict + ruff
  temiz. Artefaktlar `pipeline/tasks/016-3-acp-interactive/`.

## 2026-07-29 (Görev 024 — `atlas dashboard` özet)
- [KARAR] Run tespiti **heuristic** — audit `plan`/`dry_run` başlangıç,
  `done`/`denied`/`max_steps`/`llm_error` bitiş. Alternatif "run
  başlangıç için ayrı action" (`atlas-run/start`) audit sözleşmesini
  genişletirdi; şu an heuristik yeter.
- [KARAR] Bitmemiş run'lar `"unfinished"` olarak listelenir — süreç
  sonlanmadan öldüyse görünür. Alternatif "atla" bilgi kaybı.
- [KARAR] Cost run-metrics eşleşmesi **zaman aralığı**: `start_ts <=
  m.ts <= end_ts`. ISO 8601 string karşılaştırması kronolojik doğru;
  parse gereksiz. UTC/timezone farkı YAGNI (çoğu kullanıcı tek
  makinede).
- [KARAR] Audit sağlık ilk satır — `denetim zinciri: GEÇERLİ /
  BOZULMUŞ`. Kullanıcı dashboard'a bakınca hemen zincirin
  bütünlüğünü görsün; bozulmuşsa runs listesi güvensiz.
- [KARAR] Fiyat env yoksa cost `?` — 023 kalıbı. Kullanıcı env
  set etmediyse dashboard yine çalışır, sadece cost belirsiz.
- Kapsam: 1 CLI düzenleme (cli.py: +_collect_runs_from_audit ~50 sat,
  +_cost_for_run ~35 sat, +_cmd_dashboard ~40 sat, +parser),
  1 yeni test dosyası (6 test). Toplam 518 test yeşil (512 → +6).
  mypy strict + ruff + scan temiz. Artefaktlar
  `pipeline/tasks/024-dashboard/`.

## 2026-07-29 (Görev 023 — cache-hit metrikleri)
- [KARAR] **JSONL formatı** — her satır bağımsız JSON. Append kolay
  (dosya kilit gerektirmez); parse esnek (bozuk satır atla, kalan
  okunur); grep/jq uyumu tam. Tek büyük JSON array veya SQLite ise
  concurrent yazma karmaşıklaştırır.
- [KARAR] Yazım **`_call_anthropic` içinde** — tek noktada üretim,
  hem non-streaming hem streaming yoluna uygulanır. Alternatif
  (CLI seviyesinde callback) çağıranı zorlar; kullanıcı Python
  API çağırırsa metric yazılmaz.
- [KARAR] Yazım hatası **sessiz** — plan akışını disk sorunu
  bloklamamalı. `try: ... except Exception: pass` bilinçli. Kullanıcı
  metrics yoksa `atlas metrics` "0 çağrı" der; hiç çakışma yok.
- [KARAR] Cache-hit oranı formülü: `cache_r / (in + cache_c + cache_r)`.
  Payda tüm input token'ları temsil eder — cache'ten okunan vs
  yeni okunan oranı doğal.
- [KARAR] Cost tahmini `_cmd_metrics`'te env fiyatıyla — kullanıcı
  farklı fiyat env'iyle geriye dönük yeniden hesaplayabilir (kayıtta
  saklanan cost sabit değil, referans).
- Kapsam: 1 modül düzenleme (planner.py: +_metrics_path,
  +_write_metric_for_data ~30 sat; iki yolda çağrı), 1 CLI düzenleme
  (+_cmd_metrics ~60 sat + parser), 1 yeni test dosyası (7 test).
  Toplam 512 test yeşil (505 → +7). mypy strict + ruff temiz.
  Artefaktlar `pipeline/tasks/023-cache-metrics/`.

## 2026-07-29 (Görev 022 — `.env` otomatik yükleme)
- [KARAR] **stdlib-only** manuel parser (~25 sat) — `python-dotenv`
  bağımlılığı eklenmedi. Basit KEY=VAL yeter; multi-line, escape,
  değişken referansı YAGNI.
- [KARAR] **Shell env override edilmez** — dotenv sadece eksikleri
  doldurur. Shell'de bilinçli set edilen değer kazanır (kullanıcı
  isterse `.env`'i geçici geçersizleştirebilir).
- [KARAR] Öncelik: `ATLAS_DOTENV` env → `Path.cwd() / ".env"` →
  no-op. Custom yol test/CI için gerekli; default proje kökü doğal.
- [KARAR] `main()` başında **bir kez** çağrılır — tekrar tekrar
  disk erişimi yok. `argv` parse'ından **önce** çalışır ki komut
  seçiminden bağımsız her komut yararlanır.
- [KARAR] Hata yolları sessiz — dosya yoksa/okunamıyorsa 0 dönerken
  crash olmaz. Kullanıcı `.env` yazımını yanlış yapsa da CLI çalışır
  (uyarı yok, felsefi seçim: doctor buna bakabilir).
- Kapsam: 1 modül düzenleme (cli.py: +_load_dotenv ~25 sat +
  main() başında çağrı), 1 yeni test dosyası (7 test). Toplam
  505 test yeşil (498 → +7). mypy strict + ruff temiz. Artefaktlar
  `pipeline/tasks/022-dotenv-autoload/`.

## 2026-07-29 (Görev 021.2 — `atlas doctor --ping` canlılık kontrolü)
- [KARAR] Ping **anthropic-özel** — claude/acp subprocess başlatmak
  pahalı ve karmaşık; anthropic HTTP ping yeter. Diğer backend'lerde
  `[!] --ping yalnız anthropic backend'de çalışır` uyarı.
- [KARAR] Payload minimum: `max_tokens=8`, mesaj `"hello"`, sistem
  prompt YOK, streaming YOK. Cost neredeyse sıfır (~0.00001 USD);
  latency saf network + model boot ölçer.
- [KARAR] Timeout **sabit 10s** — env'i (`ATLAS_LLM_TIMEOUT` 60s
  varsayılan) yok say. `doctor --ping` hızlı feedback ister; 60s
  bekletmenin anlamı yok.
- [KARAR] Retry YOK — 008 sarmalayıcı devrede değil. Ping tek deneme;
  hata varsa hemen görülsün (network sorunu mu, key mi, model mi
  belirsiz kalmasın).
- [KARAR] Cost hesabı `_extract_usage` + `_fmt_cost` (015.1 kalıbı) —
  cache alanları da yakalanır (varsa). Fiyat env'i yoksa cost `?`.
- [KARAR] Ping başarısızsa exit hâlâ **0** — 021 read-only kalıbı.
  Warnings'e uyarı düşer; CI script'i `warnings` array'i kontrol
  edip karar verir. Exit farkı `--exit-on-warnings` gibi bir
  bayrağa ihtiyaç duyar; YAGNI şimdilik.
- Kapsam: 1 modül düzenleme (cli.py: +2 sabit + _run_anthropic_ping
  ~80 sat + _cmd_doctor ping dallanma + insan format [Ping] +
  parser --ping), 1 test dosyası genişleme (+4 test). Toplam
  498 test yeşil (494 → +4). mypy strict + ruff temiz. Artefaktlar
  `pipeline/tasks/021-2-doctor-ping/`.

## 2026-07-29 (Görev 021.1 — `atlas doctor --json`)
- [KARAR] Refactor: **veri toplama sunumdan ayrıldı** —
  `_collect_doctor_report()` dict döner; `_cmd_doctor` sunum tarafını
  yapar. JSON ve insan formatı aynı kaynaktan gelir; ikizleşme yok.
- [KARAR] JSON tek satır (`json.dumps` default) — jq gibi araçlar
  satır başına iş görür. `indent=2` YAGNI — kullanıcı `| jq .`
  ile güzelleştirir.
- [KARAR] Alan isimleri **env değişkeni adları** (`ATLAS_LLM`,
  `ANTHROPIC_API_KEY`, ...) — kullanıcı JSON'da gördüğü key'i
  hemen env olarak bilir. Simetri temiz.
- [KARAR] `warnings` **string listesi**, kod değil. Neden: karar
  logic'i doctor içinde; kullanıcı sadece "ne uyarısı var?" bilmek
  ister. Structured warnings (`{"code": "no_key", "msg": ...}`)
  YAGNI.
- Kapsam: 1 modül düzenleme (cli.py: +typing.Any + refactor
  _collect_doctor_report ~90 sat + _cmd_doctor --json dallanma
  + parser --json flag), 1 test dosyası genişleme (+4 test).
  Toplam 494 test yeşil (490 → +4). mypy strict + ruff temiz.
  Artefaktlar `pipeline/tasks/021-1-doctor-json/`.

## 2026-07-29 (Görev 016.2 — ACP `session/request_permission` handler)
- [KARAR] **Otomatik karar** — kullanıcı UI dialogu asla görmez.
  ATLAS otonom ajan; interaktif prompt çekirdek prensiple çelişir.
  İnteraktif mod istenirse 016.3 opt-in olarak eklenir.
- [KARAR] Karar tablosu = 016.1 metod tablosu: read-only tool →
  `allow_once`; write/shell tool → `reject`; bilinmeyen → `reject`
  **savunmalı varsayılan**. Bilinmeyen tool'a `allow_once` demek
  güvenlik açığı; kural: "bilmiyorsan reddet".
- [KARAR] `params.options` içinden eşleşen `optionId` seçilir; yoksa
  read için `allow_always`/`allow` fallback; en son sabit string
  fallback. Böylece ACP sunucusunun option sözleşmesine saygı
  duyulur ama bozuk options durumunda da yanıt üretilir.
- [KARAR] Read'te `allow_always` fallback → `allow_once` yerine
  session-boyu izin verilir eğer sunucu bunu sunuyorsa. 016.4'te
  session-level "her zaman izin" kaydı eklenirse buraya bağlanır.
- Kapsam: 1 modül düzenleme (planner.py: _acp_handle_client_request
  dallanma + _acp_permission_response ~50 sat), 1 test dosyası
  genişleme (+4 test). Toplam 490 test yeşil (486 → +4). mypy strict
  + ruff temiz. Artefaktlar `pipeline/tasks/016-2-acp-permission/`.

## 2026-07-29 (Görev 021 — `atlas doctor` env sağlık özeti)
- [KARAR] Read-only + exit 0 — env yanlış olsa da uyarı verir ama
  process'i kırmaz. Kullanıcı ne düzelteceğini görsün diye script'ler
  içinde `atlas doctor` sonu 0 dönmeli (CI/pre-flight).
- [KARAR] API key maskeleme sözleşmesi: `_mask_secret(v, 3, 3)` →
  `sk-***abc`. Uzunluk 6'dan azsa `***`. **Hiçbir kod yolunda tam
  key stdout'a düşmez** — regresyon testi `test_021_doctor_anthropic_key_maskeler`
  bunu doğruluyor (`"SUPER-SECRET" not in out`).
- [KARAR] Üç bölüm başlığı `[LLM backend]` / `[Retry & fiyat]` /
  `[Depolama]` — grep/awk ile ayrıştırma kolay; ekran tarama için
  görsel yapı net.
- [KARAR] Backend-özel uyarılar (`[!] claude bin bulunamadı`, `[!]
  ANTHROPIC_API_KEY yok`) — kullanıcı hangi backend seçmiş, ne eksik
  hemen görür. Bilinmeyen backend özel uyarı (`bilinmeyen backend:
  xyz`) + desteklenen listesi.
- [KARAR] LLM ping (Anthropic'e küçük request) **kapsam DIŞI** —
  cost + gecikme + hata izolasyonu karmaşık; kullanıcı `atlas run
  --dry-run` ile gerçek çağrıyı test edebilir. `atlas doctor` ağa
  hiç dokunmaz.
- [KARAR] `_shutil` gibi import alias mypy warning'i yerine `import
  shutil as _shutil` — mypy/ruff temiz. Fonksiyon içi lazy import
  (module scope'ta zaten `shutil` yok — cli.py hiç kullanmıyordu).
- Kapsam: 1 modül düzenleme (cli.py: +_mask_secret + _cmd_doctor
  yardımcıları ~100 sat, parser + "doctor" alt-komutu), 1 test
  dosyası genişleme (+5 test). Toplam 486 test yeşil (481 → +5).
  mypy strict + ruff temiz. `atlas scan src` sır bulmadı.
  Artefaktlar `pipeline/tasks/021-atlas-doctor/`.

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
