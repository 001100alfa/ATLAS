# 034 — Ship

## Sonuç
- **`atlas hooks install`** — `.git/hooks/pre-commit` şablondan
  (`tools/hooks/pre-commit`) yazılır. Executable bit Unix'te set.
- **`atlas hooks uninstall`** — yalnız ATLAS imzalı shim (`# atlas-hook`
  ilk 5 satırda) silinir; yabancı hook'a dokunulmaz + exit 2.
- **`atlas hooks status`** — kurulu mu, ATLAS mı, güncel mi (şablonla
  eş mi). `--json` alanları: `template_present`, `target_present`,
  `target_is_atlas`, `target_up_to_date`.
- **Shim davranışı:** her commit öncesi `atlas scan src` + `atlas
  doctor --strict`; herhangi biri exit != 0 → commit engellenir.
- **İmza kalıbı:** `# atlas-hook v1` ilk 5 satırda; sürüm evrimi
  için ayrı iş — mevcut kullanıcılar shim değiştiğinde `atlas hooks
  install` ile günceller.
- **Idempotent install:** aynı içerik zaten yazılıysa no-op; ATLAS
  imzalı ama eski içerik → sessiz güncelle; yabancı → `--force`
  gerektir.
- **Repo dışı çağrı:** `.git` yoksa exit 2 SPEC HATASI.
- **Şablon yoksa:** exit 2 SPEC HATASI.

## Dosyalar
```
tools/hooks/pre-commit                    (yeni, sh script — atlas scan
                                            + atlas doctor --strict)
src/atlas_core/cli.py                     (edit: +_HOOK_SIGNATURE,
                                            +_HOOK_TEMPLATE_PATH,
                                            +_hook_template_text,
                                            +_is_atlas_hook,
                                            +_resolve_hook_target,
                                            +_cmd_hooks_install/uninstall/status;
                                            parser hooks alt-alt-komutlarıyla)
tests/test_cli_hooks.py                   (yeni, +17 test:
                                            _is_atlas_hook x2,
                                            _resolve_target x2,
                                            install x6, uninstall x3,
                                            status x4)
pipeline/tasks/034-precommit-hook/*.md    (2 artefakt)
```

## Sözleşme değişmezliği
- Mevcut CLI komutları KORUNDU; `hooks` yeni alt-komut.
- `atlas scan` ve `atlas doctor --strict` sözleşmeleri değişmedi;
  hook yalnız onları çağırır.
- Yeni exit kodu YOK — hook `.git/hooks/pre-commit` içinde exit 1
  (git standart hook başarısız); `atlas hooks *` komutları mevcut
  exit kodları (0, 2).

## Kalite kapıları
- pytest: **646 passed + 12 skipped** (629 → +17)
- coverage: %91.27 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/034-precommit-hook` — main üstünde tek commit.

## Env sözleşmesi
Değişmedi.

## Kullanım örneği
```bash
# İlk kurulum:
$ atlas hooks install
hooks: kuruldu -> /home/user/ATLAS/.git/hooks/pre-commit

# Durum kontrolü:
$ atlas hooks status
=== ATLAS hooks — durum ===
  şablon: tools/hooks/pre-commit (var)
  hedef: /home/user/ATLAS/.git/hooks/pre-commit
    durum: kurulu (ATLAS shim'i, güncel)

# Her commit'te:
$ git commit -m "feat: X"
Sır bulunamadı.
=== ATLAS doctor — env sağlık kontrolü ===
...
[Kalite kapıları]
  DECISIONS.md: DECISIONS.md
  son giriş: 2026-07-30 (0 gün önce, eşik 7 gün)
[main abc123] feat: X

# Drift varsa (12 gün geçmiş):
$ git commit -m "feat: Y"
Sır bulunamadı.
[!] DECISIONS.md son giriş 12 gün önce, eşik 7 gün.
[pre-commit] atlas doctor --strict başarısız — commit engellendi.
Çözüm: DECISIONS.md'ye günün girişini ekle veya
       ATLAS_STRICT_DRIFT_DAYS eşiğini geçici gevşet.

# Şablon güncellendiğinde:
$ atlas hooks install
hooks: kuruldu -> .git/hooks/pre-commit  # sessiz güncelleme

# Kullanıcı kendi hook'u varsa:
$ atlas hooks install
SPEC HATASI: .git/hooks/pre-commit mevcut ve ATLAS shim'i değil;
üzerine yazmak için --force kullan

# Kaldırma:
$ atlas hooks uninstall
hooks: kaldırıldı -> .git/hooks/pre-commit
```

## Windows uyumu
`.git/hooks/pre-commit` git tarafından `sh.exe` (git-bash) ile
çağrılır. Git for Windows kurulu her makinede bu çalışır. Ayrı
PowerShell shim gerekli değil (memory'de kimi'nin bash arayışı
notu: `KIMI_CLI_GIT_BASH_PATH` — git-bash Windows'ta standart
sayılıyor).
