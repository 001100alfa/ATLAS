# Görev 058 — İhtiyaç

SPEC 042 `atlas vault verify` kırık `[[wikilink]]`'leri raporluyor.
SPEC 046 `fix-orphans` orfan notları arşivliyor. Ama kırık linkler için
düzeltme yok — kullanıcı elle:
- Silinmiş notu geri oluşturmak (içerik kaybı)
- Link'i güncellemek (potansiyel geniş refactor)
- Notu silmek + link'i temizlemek (context kaybı)

Otomatik middle-ground: her kırık hedef için "stub" not oluştur.
Kullanıcı içeriği sonra doldurur; boş bırakırsa `atlas vault fix-orphans`
temizler (stub linkli olmadığı için orfan sayılır).

## Kabul kriteri

- Yeni alt-komut: `atlas vault fix-broken [--apply] [--vault-root]
  [--target DIR]`
- Dry-run varsayılan (YIKICI iş).
- Aynı hedefe (`to`) birden fazla `from` link veriyorsa TEK stub;
  stub içeriğinde tüm kaynaklar `[[from]]` olarak listelenir.
- Hedef adı vault'ta zaten varsa (yarış/eklenmiş) → `action="skipped"`,
  dokunulmaz.
- Stub içeriği:
  ```markdown
  # <target>

  #stub

  Bu not `atlas vault fix-broken` tarafından otomatik oluşturuldu
  (SPEC 058). Kaynağı doldur veya alakasız ise
  `atlas vault fix-orphans --apply` ile temizle.

  ## Kırık link kaynağı (<N>)

  - `[[from1]]`
  - `[[from2]]`

  <!-- oluşturulma: <UTC-ts> -->
  ```
- Varsayılan hedef: `<vault>/_stubs/`; `--target` override.
- Audit: `atlas-vault / fix-broken / '<N> stub -> <target>'`.
- Vault dizini yok → exit 2 SPEC HATASI.
- Kırık link yok → "Kirik link yok" + exit 0.

## Değişmezlik

- `atlas vault verify` (SPEC 042) BİT-UYUMLU — fix-broken bağımsız
  alt-komut (SPEC 046 kalıbı).
- `atlas vault fix-orphans` (SPEC 046) BİT-UYUMLU.

## Riskli

- ASCII marker (`.. OK --`) — Windows cp1254 stdout uyumu (SPEC 057
  bug hatırı).
- Stub'lar `_stubs/` altında — verify tekrar çalıştığında bu notlar
  orfan sayılır (link vermez, alınır). Bu KASITLI: kullanıcı bilinçli
  bir aksiyon almadıkça vault graf'ında görünsün.
- Stub notu vault içinde `.md` uzantısı → `Vault.graph()` tarafından
  algılanır → sonraki `verify` çalıştırmasında kırık link
  YOK OLUR (hedef mevcut şimdi).
