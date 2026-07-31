# Görev 042 — İhtiyaç

`vault/` (Obsidian-uyumlu Markdown) ATLAS'ın uzun-vadeli belleği. Zamanla
graf sağlığı bozulur:
- silinen notlara verilen `[[wikilink]]`'ler kırık kalır,
- ne link veren ne link alan notlar orfanlaşır (bakım sinyali kayıp),
- tek notta bırakılmış `#tag`'lar tag sözlüğünü kirletir.

Yazma zaten `Vault` API'sinden geçtiği için _yeni_ bozulma nadir; ama
mevcut ve dış müdahaleyle (elle Obsidian düzenleme, rebase, çakışma
çözüm) oluşan bozulmayı tespit edecek bir sağlık kontrolü YOK.

## Kabul kriteri

- `atlas vault verify [--vault-root PATH] [--json] [--pretty] [--strict]`
- Rapor alanları:
  - `broken_links` : `[{from, to}, ...]` — hedef notu vault'ta olmayan
    wikilink'ler; deterministik sıralı (frm, to sözlük sırası).
  - `orphan_notes` : `Graph.orphans()` — ne link veren ne link alan notlar.
  - `orphan_tags`  : yalnız **bir** notta geçen tag'ler (sözlük sıralı).
  - `notes_total`, `links_total`, `tags_total` : sayaçlar.
  - `is_clean` : `broken_links + orphan_notes + orphan_tags` boş ise `True`.
- İnsan çıktısı: özet + ilk 10 kırık link + ilk 10 orfan not/tag; temiz
  ise `✔ temiz` satırı.
- `--strict` + bulgu → **exit 4** (doctor semantik eşleniği).
- `--strict` + temiz → exit 0.
- Vault dizini yok → exit 2 SPEC HATASI.
- Audit satırı: `atlas-vault` / `verify` / `<vault_root>`.
- **Vault yazılmaz** — analiz salt-okunur.

## Riskli

- `Vault.graph()` bugün `dict.fromkeys` ile not içindeki link/tag
  tekrarlarını tekilleyip tuple'a alıyor. Bu yüzden `links_total`
  "not başına tekil link sayısının toplamı"dır — bir notta aynı `[[b]]`
  iki kez geçse bile 1 sayılır. Rapor semantiği bunu döner (metrik
  değişimi değil, netleştirme).
- Exit kodu 4: `atlas run` içinde `PlannerExhaustedError` için 4
  kullanılıyor. Bağımsız komut olduğu için çakışma yaratmaz (aynı
  bağlamda dönmez); yine de SPEC'te açık.
