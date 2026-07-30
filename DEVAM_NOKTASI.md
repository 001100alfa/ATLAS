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

**Son çalışma:** 2026-07-30 (18. tur — 032.5 + 037)
**Branch:** `main` (origin/main ile senkron — `4b6c066` + docs)
**Working tree:** temiz (kapanış öncesi son doğrulama)
**Durum:** 18. tur tamamlandı; 2 lineer commit main'e ff-merge + push
edildi (`1da4e0f..4b6c066`), 2 feature branch silindi. **693/693
test yeşil** (+12 platform skip), coverage %91.10, mypy strict +
ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-30 — 18. tur)

Zincirleme iki iş (`032.5 → 037`), her biri kendi branch'inde tek
commit; sonrasında main'e lineer ff-merge + docs + push + branch
temizlik.

1. **Görev 032.5** — `atlas doctor --json --pretty` (`3c44c65`)
   - Yeni bayrak `--pretty` — `json.dumps(indent=2)` girintili
     çıktı. CI + insan hibrit kullanım.
   - Bit-uyumluluk: bayrak yoksa mevcut tek satır.
   - Strict davranışı bayraktan bağımsız (`--pretty + --strict +
     drift = exit 9` hala).
   - +3 test.

2. **Görev 037** — `atlas ai-cli diff-summary` (`4b6c066`)
   - Yeni `ai-cli` alt-grubu; ilk komut `diff-summary`.
   - `git diff --unified=0 tools/ai-cli/package-lock.json` parse
     eder, hangi paketin sürümü değişti tek satır commit mesaj
     önerisi basar: `chore(ai-cli): opencode-ai 1.18.8 → 1.18.9`.
   - `node_modules/` prefix strip; birden çok paket noktalı
     virgülle ayrılır.
   - Fail-safe: git yok / dosya yok / patlarsa `(diff okunamadı:
     ...)` + exit 0.
   - Kullanım: `git commit -m "$(atlas ai-cli diff-summary)"`.
   - 17. tur bulgusuna (`790c9da` yanlış commit mesajı) çözüm.
   - +10 test.

3. **Merge + push + temizlik**
   - `git merge --ff-only feat/032.5 && feat/037` → 2 commit lineer
     main'e (`4b6c066`), merge commit YOK.
   - `git push origin main` → `1da4e0f..4b6c066` uzağa gitti.
   - 2 feature branch silindi (`feat/032.5-doctor-pretty`,
     `feat/037-ai-cli-diff-summary`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 031 — Batch paralel `--jobs N`:** 030'un doğal uzantısı;
  **en büyük scope + risk** (2-3 saat); ThreadPool + sandbox path
  çakışması + LLM rate limit + exit agregasyon. Tek turluk.
- **Görev 033 — `atlas archive --restore <id>`:** arşivlenen görevi
  geri getir; `.tar.gz` extract + Windows kolon çakışması. Orta.
- **Görev 037.1 — `ai-cli update` alt-komutu:** `atlas ai-cli update`
  → portable npm çağırır (autoupdate.py wrap). Kullanıcı manuel
  `tools\node\npm.cmd update` yerine tek komut. Küçük.
- **Görev 038 — `atlas doctor --scan-src` unique/duplicate
  hesabı:** 032.3'te `sample_files` unique oldu ama `total`
  ham bulgu sayısı. Kullanıcı unique-hit sayısı isteyebilir. Çok
  küçük — opsiyonel.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (4b6c066 + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 2 commit (2026-07-30 18. tur):**
```
4b6c066 feat(037): atlas ai-cli diff-summary (auto-update commit disiplin)
3c44c65 feat(032.5): atlas doctor --json --pretty girintili cikti
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 693 passed, 12 skipped
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas doctor --json --pretty` (032.5)
- `atlas ai-cli diff-summary` (037; yeni alt-grup)

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `_cmd_doctor` mevcut JSON tek satır davranışı BİREBİR (yalnız
  `--pretty` iken indent=2).
- Yeni CLI alt-grubu (`ai-cli`); mevcut komutlar dokunulmadı.
- `_cmd_scan`, `_cmd_hooks_*` dokunulmadı.
- `subprocess` import genelde repository'de vardı — `cli.py`'de yeni
  eklendi (037 için `git diff` çağrısı).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **17 giriş bloğu**;
   2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 693 test yeşil (bu turun baseline'ı 683 → +10; oturum başı 319 → +374)
- 2 lineer commit main'e alındı, uzağa push edildi, 2 feature branch
  silindi (kullanıcı `onayla` ile)
- Yeni env YOK, yeni exit kodu YOK
- Uncommitted değişiklik yok, working tree temiz
- Yeni CLI komut: `atlas ai-cli diff-summary` — commit disiplin
  yardımcısı
- `atlas doctor` şeması + biçim seçenekleri gelişti (`schema_version`
  17. turdan, `--pretty` bu turdan)
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-30 altında **17 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** birikti (toplam 56+)
