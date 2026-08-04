# Görev 046 — İhtiyaç

SPEC 042 `atlas vault verify` orfan notları raporluyor ama düzeltmiyor.
Kullanıcı 20+ orfan not için tek tek karar vermek zorunda: silsin mi,
bir yerden linkle sin mi, arşive mi taşısın?

Toplu operasyonel karar: orfan notları vault içinde `_archive/orphans-
YYYY-MM-DD/` altına taşı → vault graf'ından çıkarılır ama içerik kaybol
maz.

## Kabul kriteri

- **Yeni alt-komut**: `atlas vault fix-orphans [--apply] [--vault-root]
  [--target DIR]`
- Dry-run varsayılan (YIKICI iş — `atlas archive` kalıbı).
- `--apply`: gerçek `shutil.move`; her hareket audit'e (`atlas-vault`
  / `fix-orphans` / `<N> not -> <target>`).
- Hedef: varsayılan `<vault>/_archive/orphans-YYYY-MM-DD`; `--target`
  ile override.
- Çakışma çözümü: `<name>.md` mevcut → `<name>-N.md` (N=1,2,...).
- Orfan not yok → "Orfan not yok" mesajı, exit 0.
- Vault dizini yok → exit 2 SPEC HATASI.
- Kaynak dosya yok (verify sonrası silinmiş) → `action="skipped"`
  (nazikçe atla, rapora eklenir).
- Alt-klasördeki orfanlar (ör. `daily/2026-08-04.md`) → `rglob` ile
  bulunur, hedef flat (`_archive/orphans-.../2026-08-04.md`).

## Değişmezlik

- `atlas vault verify` (SPEC 042) BİT-UYUMLU — verify dokunmuyor,
  fix-orphans BAĞIMSIZ alt-komut.
- `Vault` API dokunulmadı.

## Riskli

- Aynı dakikada iki çalıştırma → aynı `orphans-YYYY-MM-DD` klasörünü
  kullanır, çakışma suffix ile çözülür. Idempotent değil ama güvenli
  (kaynak var → yeni suffix; kaynak yok → skipped).
- `_archive/` `.gitignore`'da DEĞİL — kullanıcı vault'ı commit ediyorsa
  arşiv de git'e girer. Bu SPEC'in kapsam dışı bir konu; kullanıcı
  isterse `.gitignore`'a `_archive/` ekler.
- Sonsuz döngü koruması: `_unique_dst` 1000 denemede benzersiz
  bulamazsa `RuntimeError`; pratikte imkânsız.
