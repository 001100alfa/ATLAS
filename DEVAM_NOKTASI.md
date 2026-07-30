# DEVAM NOKTASI — ATLAS

> ## TETİKLEYİCİ (agent talimatı — bu bloku her açılışta oku)
> Kullanıcı **"devam et"**, **"kaldığı yerden devam et"** veya
> **"projeye devam"** derse, başka soru sormadan:
> 1. Bu dosyanın **tamamını** oku.
> 2. `## Bu turda yapılan` bölümünden son turun sonucunu özetle.
> 3. `## Sıradaki Karar (kullanıcıya sunulacak)` altındaki adayları
>    listeleyip kısa bir seçim sorusuyla yeni turu başlat.
> 4. Kullanıcı onay verene kadar YIKICI işlem yapma (push, rm,
>    force-push, branch silme).
> 5. Zorunlu Döngü'ye (`CLAUDE.md` §Zorunlu Döngü) gir; ilk iş
>    `DECISIONS.md`'nin son 2026-07-30 girişlerini kaba tarama.

**Son çalışma:** 2026-07-30 (16. tur — 032.3 + 035)
**Branch:** `main` (origin/main ile senkron — `58ab0b1` + docs)
**Working tree:** temiz (kapanış öncesi son doğrulama)
**Durum:** 16. tur tamamlandı; 2 lineer commit main'e ff-merge + push
edildi (`1f66a7a..58ab0b1`), 2 feature branch silindi. **676/676
test yeşil** (+12 platform skip), coverage %91.17, mypy strict +
ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-30 — 16. tur)

Zincirleme iki iş (`032.3 → 035`), her biri kendi branch'inde tek
commit; sonrasında main'e lineer ff-merge + docs + push + branch
temizlik.

1. **Görev 032.3** — `scan_secrets` döngüsü DRY refactor (`4a3a9c7`)
   - `_iter_scan_hits(path) -> list[tuple[Path, str, str]]` yeni
     ortak yardımcı.
   - `_cmd_scan` (atlas scan) ve `_check_scan_src` (032.2 doctor
     kanalı) bunu tüketir — iki yerdeki aynı döngü tek yerde.
   - `_check_scan_src` bonus bugfix: `sample_files` **unique** (bir
     dosyada birden çok bulgu → tek defa listelenir).
   - Regresyon: 2 scan + 7 032.2 test aynen geçiyor.
   - +6 test.

2. **Görev 035** — `opencode_Run.cmd` + `kilo_Run.cmd` thin shim
   refactor (`58ab0b1`)
   - Tarihsel yazımlar (`node_modules/.bin/*.cmd` + kendi XDG/HOME
     satırları) **thin shim'e** çekildi: `tools/agents/<name>.cmd`
     sarmalayıcısını `call` eder.
   - Kilo HOMEDRIVE/HOMEPATH override kaldırıldı — Node os.homedir()
     USERPROFILE'a bakar; HOMEDRIVE/HOMEPATH cmd yerleşiği (Node
     okumaz).
   - **6 kök launcher tam simetri:** opencode / kilo / claudecode /
     goose / cline / kimi. Hepsi `tools/agents/<name>.cmd` üzerine
     thin shim (claudecode istisna — Claude Code taşınabilirlik
     istisnası).
   - Smoke: opencode 1.18.8, kilo 7.4.16.
   - Regresyon: 676 pytest aynen (Python kod dokunulmadı).

3. **Merge + push + temizlik**
   - `git merge --ff-only feat/032.3 && feat/035` → 2 commit lineer
     main'e (`58ab0b1`), merge commit YOK.
   - `git push origin main` → `1f66a7a..58ab0b1` uzağa gitti.
   - 2 feature branch silindi (`feat/032.3-scan-dry`,
     `feat/035-opencode-kilo-shim`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 031 — Batch paralel `--jobs N`:** 030'un doğal uzantısı;
  **en büyük scope + risk** (2-3 saat); ThreadPool + sandbox path
  çakışması + LLM rate limit + exit agregasyon. Tek turluk.
- **Görev 033 — `atlas archive --restore <id>`:** arşivlenen görevi
  geri getir; `.tar.gz` extract + Windows kolon çakışması. Orta.
- **Görev 036 — opencode npm install drift fix:** package.json
  `^1.18.9` ama node_modules 1.18.8 (035 turunda not düşüldü). Küçük
  chore.
- **Görev 032.4 — `atlas doctor --strict --json` şema versiyonu:**
  JSON çıktısına `schema_version` alanı; CI tüketicileri şema
  değişiminde uyarabilsin. Küçük.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (58ab0b1 + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 2 commit (2026-07-30 16. tur):**
```
58ab0b1 chore(launcher): opencode+kilo thin shim (SPEC 035) - 6 launcher tam simetri
4a3a9c7 feat(032.3): _iter_scan_hits DRY yardimcisi + _cmd_scan/_check_scan_src refactor
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 676 passed, 12 skipped
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışı (bu turda):** yok — iç refactor + launcher
simetrisi.

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `_cmd_scan` çıktı sözleşmesi BİREBİR — stdout satır formatı +
  stderr uyarı + exit 0/1.
- `_check_scan_src` dönüş şeması BİREBİR + küçük iyileşme
  (sample_files unique explicit).
- 6 launcher CLI davranışı BİREBİR — kullanıcı `--version` çıktıları,
  alt-komutlar hepsi çalışıyor.
- `tools/agents/*.cmd` sarmalayıcıları hiç dokunulmadı (kurulum
  sihirbazı üretiyor).
- Ana Python kod tabanı: 676 aynen; hiçbir Python davranışı
  değişikliği yok.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **13 giriş bloğu** (kümülatif);
   2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 676 test yeşil (bu turun baseline'ı 670 → +6; oturum başı 319 → +357)
- 2 lineer commit main'e alındı, uzağa push edildi, 2 feature branch
  silindi (kullanıcı `onayla` ile)
- Yeni env YOK, yeni exit kodu YOK, yeni CLI davranışı YOK — bu tur
  **temizlik odaklı**: DRY refactor + launcher simetrisi
- Uncommitted değişiklik yok, working tree temiz
- 6 kök launcher tam simetri: opencode / kilo / claudecode / goose /
  cline / kimi (claudecode istisna — Claude Code taşınabilirlik
  istisnası, tools/agents/'da wrapper yok)
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-30 altında **13 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** birikti (toplam 52+)
- Not düşülen küçük drift (036 adayı): opencode `package.json` `^1.18.9`
  ama `node_modules` 1.18.8 — `npm install` çalıştırılmamış.
