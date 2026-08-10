# Görev 183 — İhtiyaç

SPEC 172 `vault verify --schema --format json-lines [--out --gzip]`
uygulandı ve 9 test var. Ancak SPEC 159 doctor kalıp simetrisindeki
4 edge kanıt (parent auto-mkdir + idempotent `.gz` suffix + stdout↔file
satır-bazında eşitlik + tam MUTEX mesajı) vault verify için EKSİK —
kalıp simetrisi kanıt testleri gelecek regresyon kilidi.

## Kabul

- Envanter doğrulaması: SPEC 172 kalıbı doğru — `--schema --format
  json-lines --out PATH [--gzip]`; parent auto-mkdir + auto-suffix
  `.gz`; MUTEX --gzip yalnız --out ile.
- +4 ekstra kanıt test (SPEC 159 kalıbı vault verify için):
  1. Parent auto-mkdir (nested dizin — mkdir(parents=True) kalıp
     doğrulaması).
  2. Zaten `.gz` uzantısı varsa ikinci `.gz` eklenmez (idempotent).
  3. Stdout ↔ düz dosya satır-bazında eşitlik (bit-uyumluluk sıkı
     kanıt; SPEC 172 mevcut testinde gzip decompress ile vardı,
     düz dosya için AYRI test).
  4. `--gzip` `--out` olmadan tam MUTEX mesajı (hem `--gzip` hem
     `--out` err içinde geçer).
- Yeni CLI kodu YOK — yalnız test ekleme (canlı kanıt).
