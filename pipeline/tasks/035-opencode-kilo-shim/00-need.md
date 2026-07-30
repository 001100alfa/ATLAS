# 035 — İhtiyaç: `opencode_Run.cmd` + `kilo_Run.cmd` thin shim refactor

## Bağlam
14-15. tur launcher zinciri (`claudecode_Run.cmd`, `goose_Run.cmd`,
`cline_Run.cmd`, `kimi_Run.cmd`) `tools/agents/<name>.cmd`
sarmalayıcısını `call` eden **thin shim** kalıbıyla yazıldı.
Ancak `opencode_Run.cmd` ve `kilo_Run.cmd` **tarihsel** — kendi
XDG env kurulumlarını yapıyor ve BIN'i doğrudan çağırıyor. İki farklı
kalıp bir arada: DRY ihlali, `tools/agents/*.cmd` değişirse bu iki
launcher senkron kalmıyor.

## İhtiyaç (tek cümle)
`opencode_Run.cmd` ve `kilo_Run.cmd` de thin shim kalıbına
(`call tools\agents\<name>.cmd %*`) çekilsin; 6 kök launcher tam
simetri.

## Ölçülebilir Başarı
- **M1 — `opencode_Run.cmd` refactor:** kendi XDG env satırlarını
  kaldır; `tools/agents/opencode.cmd` sarmalayıcısını çağır.
  Ek: PATH prefix + cwd + call + exit code (14-15. tur kalıbı).
- **M2 — `kilo_Run.cmd` refactor:** aynı kalıp; `tools/agents/kilo.cmd`
  sarmalayıcısını çağır.
- **M3 — Smoke:** her ikisi de `--version` çıktısı vermeli (davranış
  regresyonu yok).
- **M4 — DRY:** tek gerçek env kurulumu `tools/agents/*.cmd`'de.
  Kurulum sihirbazı bu dosyaları üretir/günceller; kök launcher
  otomatik yararlanır.
- **M5 — Sarmalayıcı yok = net hata:** `tools/agents/*.cmd` yoksa
  kök launcher `[HATA] tools\agents\...cmd yok. Kurulum: setup-acp-
  agents.cmd` bassın (14-15. tur kalıbı).
- **M6 — DECISIONS:** [KARAR] neden 14-15. turda beklendi (regresyon
  riski); iki launcher'ın tarihsel farkı (kilo'nun HOMEDRIVE/HOMEPATH
  override'ı) bu kez kaldırılıyor mu (kontrol).

## Kapsam DIŞI
- `tools/agents/*.cmd` içinde değişiklik — kurulum sihirbazı
  tarafından üretiliyor, buraya dokunulmaz.
- Yeni launcher — 6 tam sette.
- PowerShell wrapper — 034.1 kararı: git hooks sh üstünde, PS
  giriş noktası yok (launcher için de tarihsel yok).
- Test — launcher batch script; canlı `--version` smoke yeter,
  pytest regresyonu ana repo kalite kapısı üstünden geliyor.

## Kısıt
- `opencode` / `kilo` CLI'ları normal çalışmaya devam etmeli
  (smoke: --version).
- `tools/agents/*.cmd` mevcut env davranışı (XDG proje-yerel, Node
  direkt çağrı) korunuyor — bu launcher'lar yalnız `call` ediyor.
- HOMEDRIVE/HOMEPATH override kaldırılıyorsa (mevcut `kilo_Run.cmd`'de
  var, `tools/agents/kilo.cmd`'de yok) kilo işlevi doğrulanmalı.
- Türkçe yorum.
- Yeni env DEĞİL, yeni exit kodu YOK.
