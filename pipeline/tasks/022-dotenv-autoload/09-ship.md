# 022 — Ship

## Sonuç
`atlas` CLI başlangıcında proje kökündeki `.env` dosyası (veya
`ATLAS_DOTENV` env'inde belirtilen yol) el ile parse edilip
`os.environ`'a yüklenir.

- **Override yok:** shell'de zaten set edilmiş değişkenler kazanır.
- **Basit format:** `KEY=VALUE`, `#` yorum, boş satır atla, tırnak sıyırma
  (`"..."`, `'...'`).
- **stdlib-only:** ~30 sat manuel parser; `python-dotenv` bağımlılığı
  eklenmedi.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_load_dotenv ~25 sat;
                                            main() başında çağrı)
tests/test_cli_dotenv.py                  (yeni, 7 test)
pipeline/tasks/022-dotenv-autoload/*.md   (5 artefakt)
```

## Sözleşme değişmezliği
- CLI komutları değişmedi.
- Mevcut env değişkenleri override edilmez.
- Yeni exit kodu YOK.

## Kalite kapıları
- pytest: **505 passed** (498 → +7)
- mypy strict + ruff: temiz

## Branch
`feat/022-dotenv-autoload` — 021.2 üstünde tek commit.

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_DOTENV` | `.env` yolu override (varsayılan `./.env`) |

## Kullanım örneği
```bash
# ./ .env
ANTHROPIC_API_KEY="sk-ant-..."
ATLAS_LLM=anthropic
ATLAS_LLM_PRICE_IN=3
ATLAS_LLM_PRICE_OUT=15

# Artık her shell'de env set etmeye gerek yok:
$ atlas doctor
[LLM backend]
  ATLAS_LLM: anthropic
  ANTHROPIC_API_KEY: sk-***...
```
