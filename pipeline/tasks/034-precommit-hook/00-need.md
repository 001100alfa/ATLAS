# 034 — İhtiyaç: git pre-commit hook + `atlas hooks` alt-komutu

## Bağlam
`atlas scan` (sır taraması) + `atlas doctor --strict` (032, DECISIONS
drift denetimi) mevcut ama **manuel** çalışıyor. Commit öncesi
otomatik koşmadan disiplin kağıt üstünde kalır: 032'de eklenen exit 9
zaten drift'i keskin bir sinyale çevirdi, ama kullanıcı doctor'u
unutup commit atarsa uyarı hiç görmez.

Ek olarak `.env` dosyalarına yanlışlıkla API key düşme riski
`atlas scan` ile yakalanabilir, ama sadece elle çalıştırılırsa.

`.git/hooks/pre-commit` git tarafından tracked DEĞİL — dolayısıyla
kaynağı repoda tutup `atlas hooks install` ile `.git/hooks/`'a
kopyalamak lazım.

## İhtiyaç (tek cümle)
`atlas hooks install` her commit öncesi `atlas scan src` + `atlas
doctor --strict` çalıştıran bir shim'i `.git/hooks/pre-commit`'e
koysun; `uninstall` kaldırsın; `status` durum göstersin.

## Ölçülebilir Başarı
- **M1 — Shim şablonu:** `tools/hooks/pre-commit` — POSIX sh script,
  `atlas scan src` + `atlas doctor --strict` çağırır; herhangi biri
  exit != 0 ise commit engellenir (`exit 1`). Git-bash Windows'ta
  standart, macOS/Linux'ta zaten sh var.
- **M2 — Install:** `atlas hooks install` — repo kökünde `.git`
  varsa `.git/hooks/pre-commit`'i şablondan yaz; **mevcut varsa**
  exit 2 SPEC HATASI (`--force` ile ez).
- **M3 — Uninstall:** `atlas hooks uninstall` — kurulu ATLAS shim'i
  varsa (imza doğrulama: ilk satırda `# atlas-hook`) sil; yoksa
  no-op (idempotent).
- **M4 — Status:** `atlas hooks status` — kurulu mu, hangi imza, ne
  koşuyor. `--json` çıktısı.
- **M5 — İmza:** hook script ilk satırından sonra `# atlas-hook
  v1` comment — uninstall bunu güvenle tanımak için. Kullanıcının
  kendi hook'unu silmemek.
- **M6 — Idempotent install:** aynı shim zaten kuruluysa yeniden
  yazma başarılı (exit 0). Farklı içerik varsa `--force` gerektir.
- **M7 — Repo dışı çağrı:** `.git` yoksa (dizin git repo değil)
  exit 2 SPEC HATASI.
- **M8 — Hook manuel çalıştırılabilir:** kullanıcı `./.git/hooks/
  pre-commit` çağırınca (staged file yok gibi durumda) uyarısız
  koşup exit 0 dönmesi bekleniyor. Test: shim smoke.
- **M9 — Test:** +8 test.
- **M10 — DECISIONS:** [KARAR] neden `.git/hooks/pre-commit`
  yerine `core.hooksPath` değil; imza satırı gerekçesi; --force
  neden zorunlu.

## Kapsam DIŞI
- pre-push, post-merge gibi diğer hook'lar — YAGNI (pre-commit
  yeter).
- pre-commit-framework entegrasyonu — YAGNI (yerel shim kadar
  temiz).
- Otomatik install (pip install sonrası) — YAGNI, kullanıcı
  manuel `atlas hooks install`.
- Windows PowerShell shim — git-bash zaten Windows'ta sh sağlar
  (memory: kimi'nin git-bash arayışıyla ilgili not var).

## Kısıt
- `_cmd_*` mevcut sözleşme korunur; yeni `hooks` alt-komutu.
- Shim yalnız stdlib bash — kısa, denetlenebilir.
- `atlas scan src` + `atlas doctor --strict` çıktısı hook'ta gösterilir
  (stderr'e yönlendirilmez — kullanıcı görsün).
- Türkçe hata mesajı.
- Windows uyumu: `.git/hooks/pre-commit` git tarafından bash ile
  çağrılır (git-bash gerekli). PowerShell shim ayrı iş.
- Yeni exit kodu YOK.
