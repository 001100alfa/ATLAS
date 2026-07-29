# 020 — Ship

## Sonuç
`atlas run --goal-file <yaml> --dry-run` bayrağı eklendi. Planner **gerçek**
çağrılır (LLM + cost audit + retry), ancak action `_p → ("[dry-run]
eylem yürütülmedi: <p>", 0.0)` stub'lanır ve yargıç tek adımda `True`
döner. Disk / sandbox yıkıcı iş YOK.

- stdout: `MOD: dry-run — action yürütme kapalı`
- audit: `("atlas-run", "dry_run", <goal cümlesi>)` işareti + normal
  plan/observe kayıtları
- LLM hata yolları (bin yok, API key yok, timeout) — hâlâ exit 7
  çalışır (dry-run bypass etmez).

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +Callable import,
                                            _cmd_run_goal dry-run
                                            dallanma — act/judge stub;
                                            parser --dry-run flag)
tests/test_cli_direct.py                  (+4 test — stub backend + audit,
                                            action stub dosya yaratmaz,
                                            --dry-run yoksa normal yol,
                                            LLM hata hâlâ exit 7)
pipeline/tasks/020-run-dry-run/*.md       (5 artefakt)
```

## Sözleşme değişmezliği
- `run_loop`, `make_planner`, `make_action`, `make_judge`, `Goal` —
  hiç dokunulmadı.
- `--dry-run` yoksa mevcut SPEC 002 davranışı bit-uyumlu (regresyon
  testi ile doğrulandı).
- Yeni exit kodu YOK.

## Kalite kapıları
- pytest: **481 passed** (477 → +4)
- mypy strict + ruff: temiz

## Branch
`feat/020-run-dry-run` — 019 üstünde tek commit.

## Kullanım örneği
```bash
# Prompt/YAML'ı test et — cost gerçekten Anthropic'e gitsin ama
# dosya sisteme yansımasın
atlas run --goal-file gorevler/rapor.yaml --dry-run

# Çıktı:
#   Bağlam: (kapalı)
#   MOD: dry-run — action yürütme kapalı
#   ...
#   plan: write:rapor.md:<LLM'nin ürettiği içerik>
#   observe: [dry-run] eylem yürütülmedi: write:rapor.md:...
```

## Bekleyen
- Görev 020.1: `--dry-run --steps N` — çok-adımlı rehearsal
- Görev 020.2: cost tahmini önizleme (`--estimate-cost`)
