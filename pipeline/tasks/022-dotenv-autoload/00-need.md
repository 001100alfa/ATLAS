# 022 — İhtiyaç: `.env` dosyası otomatik yükleme

## Bağlam
Kullanıcı `ANTHROPIC_API_KEY` ve fiyat env'lerini shell profile'ında
tutmak istemiyor — proje kökündeki `.env` dosyasına yazmak istiyor.
Şu an ATLAS `.env`'i okumuyor; kullanıcı her seferinde `set` /
`export` yapmak zorunda. CLAUDE.md'de `.env` referansı zaten var
(`sır asla koda gömülmez; .env kullan, .env commit edilmez`).

## İhtiyaç (tek cümle)
`atlas` CLI başlangıcında proje kökündeki `.env` dosyası el ile
parse edilip `os.environ`'a yüklensin; **mevcut env değişkenleri
override edilmesin** (shell'de set edilen kazanır).

## Ölçülebilir Başarı
- **M1 — Yükleme yolu:** `_load_dotenv(path)` — verilen yolu okur;
  dosya yoksa sessiz no-op.
- **M2 — Parse:** her satır `KEY=VALUE` formatı; `#` yorum;
  boş satır atla. `VALUE` etrafında tırnak varsa (`"..."` veya `'...'`)
  tırnaklar çıkarılır.
- **M3 — Override yok:** `os.environ`'da zaten varsa dokunma —
  shell env üstünde. Yeni: os.environ'a ekle.
- **M4 — Yol keşfi:** `main()` başında `Path.cwd() / ".env"` denenir;
  yoksa `ATLAS_DOTENV` env'inde belirtilen yol; yoksa no-op.
- **M5 — Güvenlik:** `.gitignore`'a `.env` zaten girmiş olmalı
  (kullanıcı sorumluluğu, ATLAS scan uyarısı zaten var).
- **M6 — Test:** +5 test — dosya yok no-op, basit KEY=VAL,
  tırnak sıyırma, override etmez, yorum/boş satır atla,
  `ATLAS_DOTENV` yolu.
- **M7 — DECISIONS:** [KARAR] neden stdlib-only; neden shell env
  önceliği.

## Kapsam DIŞI
- Multi-line values — YAGNI.
- Escaped karakterler (`\n`, `\"`) — basit tırnak yeter.
- Değişken referansı (`FOO=$BAR`) — YAGNI.
- `python-dotenv` bağımlılığı — YAGNI, ~30 sat stdlib yeter.

## Kısıt
- stdlib-only.
- CLI başlangıcında **bir kez** çalışır — tekrar tekrar okumaz.
- Türkçe hata mesajı iç kullanım için (kullanıcı bunu görmemeli
  — no-op sessiz).
