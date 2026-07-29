# 021 — İhtiyaç: `atlas doctor` sağlık kontrolü

## Bağlam
ATLAS artık **20 env değişkeni + Goal alanları + backend** ekosistemi
taşıyor: `ATLAS_LLM`, `ANTHROPIC_API_KEY`, `ATLAS_LLM_MODEL`,
`ATLAS_LLM_TIMEOUT`, `ATLAS_LLM_RETRIES`, `ATLAS_LLM_BACKOFF`,
`ATLAS_LLM_JITTER`, `ATLAS_LLM_PRICE_IN/OUT`, `ATLAS_LLM_OBS_CHARS`,
`ATLAS_LLM_TRACE`, `ATLAS_LLM_CLAUDE_BIN`, `ATLAS_LLM_ACP_BIN`,
`ATLAS_LLM_ANTHROPIC_URL`, `ATLAS_CONTEXT`, `ATLAS_ARCHIVE_AGE_DAYS`,
`ATLAS_VAULT`, `ATLAS_AUDIT`, `ATLAS_SANDBOX`. Kullanıcı bir görev
çalıştırmadan önce **hangi backend'in nasıl yapılandırılmış** olduğunu
görmek istiyorsa el ile 20 env kontrol etmek zorunda.

## İhtiyaç (tek cümle)
`atlas doctor` alt-komutu env sağlık özetini stdout'a yazsın: hangi
LLM backend seçili, API key/bin var mı, retry/jitter/fiyat konfigürasyonu,
audit/vault/sandbox yolları, arşiv yaş eşiği — hepsi tek bakışta.

## Ölçülebilir Başarı
- **M1 — Alt-komut:** `atlas doctor` argparser'a eklenir; args yok.
- **M2 — Bölümler:** çıktı üç bölümde:
  1. **LLM backend** — `ATLAS_LLM`, backend-özel bilgiler (API key
     var mı, bin nerede, model), timeout, stream/cache Goal
     alanları için not.
  2. **Retry & fiyat** — retries, backoff, jitter, prices, trace.
  3. **Depolama** — vault, audit, sandbox, arşiv yaş.
- **M3 — API key gizleme:** `ANTHROPIC_API_KEY` **maskeler** (`sk-...
  ***abc`) — tam key stderr'a/stdout'a **asla** düşmez.
- **M4 — Backend uyarıları:** `ATLAS_LLM=claude` ama `claude` PATH'te
  yok → `[!] claude bin bulunamadı: PATH'e ekleyin veya
  ATLAS_LLM_CLAUDE_BIN`. `ATLAS_LLM=anthropic` ama key yok → `[!]
  ANTHROPIC_API_KEY yok`. Benzer için acp.
- **M5 — Bilinmeyen backend:** `ATLAS_LLM=xyz` → `[!] bilinmeyen
  backend: xyz (desteklenen: stub, claude, anthropic, acp)`.
- **M6 — Exit 0:** doctor read-only; env yanlış olsa da exit 0.
  Uyarılar `[!]` prefix'iyle işaretlenir; kullanıcı fark eder.
- **M7 — Test:** +5 test — stub varsayılan, anthropic key yok
  uyarı, anthropic key var mask, claude bin yok uyarı, bilinmeyen
  backend uyarı, key mask'ta tam key GEÇMEZ.
- **M8 — DECISIONS:** [KARAR] neden read-only + exit 0.

## Kapsam DIŞI
- Otomatik düzeltme — kullanıcı env'i kendi kabuğundan set eder.
- LLM ping/health check (Anthropic'e küçük request atmak) — cost
  ve gecikme; kullanıcı `atlas run --dry-run` ile kendisi test edebilir.
- JSON çıktı formatı — insan-okunur yeter.

## Kısıt
- Sadece env okur; ağ yok, dosya sistemi yalnız `shutil.which` +
  `os.path.isfile`.
- API key hiçbir kod yolunda tam olarak stdout/stderr'a düşmez.
- Türkçe çıktı; teknik terimler orijinal.
