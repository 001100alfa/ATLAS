# 007 — Ship

## Sonuç
`atlas archive <task>` alt-komutu eklendi. Tamamlanmış bir görevi
tek satırda arşive taşır (`tar.gz` + vault özet notu + klasör silme +
audit kaydı), varsayılan **dry-run** ile yıkıcı işlem asla istem-dışı
tetiklenmez.

Özet kaynağı sırası: `--summary` argümanı → `09-ship.md`'nin ilk
paragrafı → fallback `"<task> arşivlendi"`. Hata dallanması: klasör
yok → exit 2 (SPEC hatası); tarfile/vault hatası → exit 6 (handler
kalıbıyla aynı) + audit `"error"` kaydı.

## Dosyalar
```
src/atlas_core/cli.py                (edit: +_cmd_archive, +_read_ship_summary,
                                      +sub.add_parser("archive"); import archive_task/Vault)
tests/test_cli_direct.py             (+6 test — AC1..AC7)
pipeline/tasks/007-archive-cli/*.md  (5 artefakt)
```

## Sözleşme değişmezliği
- Mevcut alt-komutlar (`context`, `remember`, `recall`, `run`, `reindex`,
  `workflow`, `audit-verify`, `scan`) **hiç değişmedi**.
- Exit kodu tablosu genişlemedi: 2 (SPEC) ve 6 (arşiv-handler) yeniden
  kullanıldı — kullanıcıya iki koddan seçim yaptırılmadı.
- Yeni yıkıcı işlemin CLAUDE.md kuralı: **`--apply` bilinçli seçim**;
  varsayılan dry-run.

## Kullanım örneği
```bash
# Ne olacağını gör
atlas archive 003-llm-planner

# Gerçekten arşivle
atlas archive 003-llm-planner --apply

# Kendi özetini ver
atlas archive 003-llm-planner --apply --summary "SPEC 003: LLM planner..."

# Test için özel kök
atlas archive foo --apply --tasks-root /tmp/pipeline/tasks --archive-root /tmp/arch
```

## Kalite kapıları
- pytest: **370 passed** (baseline 364 + 6 yeni)
- coverage: **%93.44** (eşik %90)
- mypy strict: temiz
- ruff: temiz

## Branch
`feat/007-archive-cli` — `feat/003.2-llm-prompt` üstünde tek commit.

## Notlar
- Vault notu her zaman `vault/tasks/task-<task>.md` yoluna yazılır
  (`archive_task`'ın sözleşmesi).
- Tarih formatı `YYYY-MM-DD` (ISO 8601 date) — çıktıda sabit.
- `archive_task` içindeki `shutil.rmtree` yalnız `--apply` ile çalışır;
  dry-run yolunda `archive_task` hiç çağrılmaz.
