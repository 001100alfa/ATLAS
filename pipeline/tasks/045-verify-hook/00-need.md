# Görev 045 — İhtiyaç

SPEC 042 (`atlas vault verify --strict`) tamamlandı ama commit
zamanında çağrılmıyor. Kırık `[[wikilink]]` veya orfan not/tag commit'e
girebiliyor — kalite bozulması geç fark ediliyor.

SPEC 034 pre-commit hook zinciri hâlihazırda `atlas doctor --strict
--scan-src` gate'ini çalıştırıyor. Aynı zincirin sonuna vault verify
gate'i eklenmeli.

## Kabul kriteri

- `tools/hooks/pre-commit` şablonu v2 → v3'e yükselir; imza satırı
  `# atlas-hook v3`.
- Yeni gate: `if [ -d vault ]; then atlas vault verify --strict; fi`.
  Doctor gate'inden SONRA (bağımsız iki gate).
- Fresh clone (vault/ yok) → verify çağrılmadan hook exit 0
  (SPEC HATASI exit 2'yi tetiklememek için).
- `_HOOK_SIGNATURE` sabiti (`atlas_core/cli.py`) v3'e yükselir —
  mevcut v1 stringiyle aynı prefix'e sahip; `_is_atlas_hook` versiyon
  bilinçsiz (mevcut davranış korunur).
- Kurulu v2 hook'lar `hooks status`'ta `target_up_to_date=False`
  gösterir (kullanıcı `hooks install --force` ile v3'e geçer).
- +5 test (v3 imzası + vault verify çağrısı + guard sırası + doctor
  gate korundu + install sonrası .git/hooks/pre-commit v3 imzalı).
- Mevcut 24 hook testi BİT-UYUMLU.

## Riskli

- Autouse fixture `_HOOK_TEMPLATE_PATH`'i sahte şablona monkeypatch
  ediyor. Şablon içerik testleri repo kökündeki gerçek dosyayı
  okumak zorunda (`Path(__file__).parent.parent`). Yeni testler bu
  yaklaşımı kullanır; install testi mevcut fixture ile yeter (install
  sonrası target dosyaya v3 imzasını kontrol eder — fixture sahte
  şablon zaten v3 imzası taşır çünkü `_HOOK_SIGNATURE` sabitini
  kullanıyor).
- Windows `sh.exe` yoksa hook çalışmaz (SPEC 034.1 mevcut uyarı).
  045 bunu değiştirmez.
