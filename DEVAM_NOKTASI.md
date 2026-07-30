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

**Son çalışma:** 2026-07-30 (17. tur — 036 + 032.4)
**Branch:** `main` (origin/main ile senkron — `6a9c34c` + docs)
**Working tree:** temiz (kapanış öncesi son doğrulama)
**Durum:** 17. tur tamamlandı; 2 lineer commit main'e ff-merge + push
edildi (`ae11fe5..6a9c34c`), 2 feature branch silindi. **680/680
test yeşil** (+12 platform skip), coverage %91.17, mypy strict +
ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-30 — 17. tur)

Zincirleme iki iş (`036 → 032.4`), her biri kendi branch'inde tek
commit; sonrasında main'e lineer ff-merge + docs + push + branch
temizlik.

1. **chore/036** — `tools/ai-cli/` opencode npm drift fix (`7ec5156`)
   - 035 turunda not düşülen drift: `package.json ^1.18.8` semver
     1.18.9'u kapsıyor ama node_modules 1.18.8 kalmıştı (auto-update
     package-lock'a yansımamıştı).
   - `npm update opencode-ai --prefix tools/ai-cli` (portable npm)
     → package-lock 1.18.9'a senkron.
   - Smoke: `opencode_Run.cmd --version` 1.18.8 → **1.18.9**.
   - Bulgu: `790c9da` commit mesajı gerçek diff ile senkron değildi
     (mesaj "opencode 1.18.9" diyor, diff aslında cline bump'ı).
     Auto-update mesaj disiplini not düşüldü.

2. **Görev 032.4** — `atlas doctor` JSON `schema_version` (`6a9c34c`)
   - `_DOCTOR_SCHEMA_VERSION = "1"` modül sabiti.
   - `_collect_doctor_report`'a en üst alan `"schema_version": "1"`.
   - İnsan format başlığı `=== ATLAS doctor — env sağlık kontrolü
     (şema v1) ===`.
   - Bump kuralları: alan ekleme = aynı; kaldırma/rename/tip = major
     bump.
   - Bit-uyumluluk: mevcut JSON alanları BİREBİR (yalnız EKLEMELER).
   - +4 test (JSON alan, JSON regresyon, insan format, modül sabiti).

3. **Merge + push + temizlik**
   - `git merge --ff-only feat/036 && feat/032.4` → 2 commit lineer
     main'e (`6a9c34c`), merge commit YOK.
   - `git push origin main` → `ae11fe5..6a9c34c` uzağa gitti.
   - 2 feature branch silindi (`feat/036-opencode-npm-install`,
     `feat/032.4-doctor-schema-version`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 031 — Batch paralel `--jobs N`:** 030'un doğal uzantısı;
  **en büyük scope + risk** (2-3 saat); ThreadPool + sandbox path
  çakışması + LLM rate limit + exit agregasyon. Tek turluk.
- **Görev 033 — `atlas archive --restore <id>`:** arşivlenen görevi
  geri getir; `.tar.gz` extract + Windows kolon çakışması. Orta.
- **Görev 037 — auto-update commit mesaj disiplini:** 036 turunda
  bulunan hata: `atlas-portable.json` auto-update commit mesajları
  gerçek diff ile senkron değil. Küçük fix (msg template düzelt).
- **Görev 032.5 — `atlas doctor --json --pretty`:** JSON çıktısını
  girintili bas (CI/insan hibrit tüketim). Çok küçük.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (6a9c34c + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 2 commit (2026-07-30 17. tur):**
```
6a9c34c feat(032.4): atlas doctor JSON schema_version alani (v1)
7ec5156 chore(ai-cli): opencode-ai node_modules 1.18.8 -> 1.18.9 (035 drift fix)
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 680 passed, 12 skipped
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışı (bu turda):**
- `atlas doctor` çıktısında `schema_version` alanı + başlıkta "(şema v1)"
  (032.4).
- opencode 1.18.9 (chore/036).

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `_cmd_doctor` mevcut çıktı BİREBİR + `schema_version` alanı yeni
  eklendi.
- `_collect_doctor_report` şeması EKLEMELER (backend/retry/storage/
  warnings/quality aynen, ilk alan `schema_version`).
- Diğer CLI komutları dokunulmadı.
- opencode CLI davranışı (`--version` dışında) değişmedi.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **15 giriş bloğu** (kümülatif);
   2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 680 test yeşil (bu turun baseline'ı 676 → +4; oturum başı 319 → +361)
- 2 lineer commit main'e alındı, uzağa push edildi, 2 feature branch
  silindi (kullanıcı `onayla` ile)
- Yeni env YOK, yeni exit kodu YOK — bu tur da temizlik + iyileştirme
- Uncommitted değişiklik yok, working tree temiz
- opencode 1.18.9 hizalı (035 drift kapandı)
- `atlas doctor` şeması artık `schema_version` alanıyla evrimi
  disipline aldı
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-30 altında **15 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** birikti (toplam 54+)
- Bulgu (037 adayı): `atlas-portable.json` auto-update commit
  mesajları gerçek diff ile senkron değil (790c9da mesaj cline yerine
  opencode diyordu). Küçük iş.
