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

**Son çalışma:** 2026-07-30 (20. tur — 037.2 + 031.1 + 034.2 + 039)
**Branch:** `main` (4 lineer commit ff-merge, push bekliyor)
**Working tree:** temiz
**Durum:** 20. tur tamamlandı; 4 görev tek turluk zincirleme;
tümü main'e lineer ff-merge. **742/742 test yeşil** (+12 platform skip),
coverage %90.87, mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-30 — 20. tur)

Zincirleme **4 iş** — sıra: `037.2 → 031.1 → 034.2 → 039` (küçükten
büyüğe / bağımsızlığa göre).

1. **Görev 037.2** — `atlas ai-cli list` (`9339976`)
   - `tools/ai-cli/package.json` deps + `node_modules/<n>/package.json`
     version cross-check.
   - Şema: `{path, packages[{name, expected, installed}]}`.
   - `--json` bayrağı; hizalı sütunlar; `(kurulu değil)` etiketi.
   - Bozuk package.json → exit 2 SPEC HATASI.
   - +5 test.

2. **Görev 031.1** — batch `--dry-run` toplu step özeti (`5751d6d`)
   - Batch özet tablosundan sonra `=== ATLAS batch dry-run özeti ===`.
   - İçerik: `toplam step: N (plan=X, act=Y, observe=Z, reflect=W)` +
     ilk 5 act eylem.
   - Seri dal: `_Tee(sys.stdout, buf) + contextlib.redirect_stdout`
     (tek thread güvenli). Paralel dal: TLS-captured metinler.
   - `--dry-run` YOK → özet BASILMAZ (bit-uyumluluk).
   - +4 test.

3. **Görev 034.2** — pre-commit shim canlı regresyon (`991625c`)
   - `test_cli_hooks_regression.py`: shim subprocess ile shell
     üzerinden çalıştırılır (mock atlas + `_find_hook_shell()`).
   - Mock exit 0/9/2 → shim exit 0/1/1 doğrulandı.
   - Statik regresyon: şablon `atlas doctor --strict --scan-src` +
     `exit 1` + "commit engellendi" içerir.
   - Yerelde `tools/git/usr/bin/sh.exe` portable → 4 test canlı geçti.
   - Baremetal Windows sh yoksa `pytest.skip`.
   - +4 test.

4. **Görev 039** — LLM inflight metriği (`223154b`)
   - `planner.py`: `_INFLIGHT_COUNT + threading.Lock` module-global.
   - `_inflight_begin/end/snapshot` API — thread-safe.
   - `_call_anthropic` **wrapper/inner** ayrımı; wrapper `try/finally`
     ile `_inflight_end()` garanti.
   - `_write_metric_for_data(data, inflight: int | None = None)` —
     `inflight` opt-in (None → alan yazılmaz, bit-uyumlu).
   - Snapshot çağrıyı **dahil** sayar; end `max(0, N-1)` defensive.
   - +7 test.

5. **Merge + kalite kapıları**
   - Sıra: `037.2 → 031.1 → 034.2 → 039` (her biri main'e rebase +
     ff-merge + tam pytest/mypy/ruff/scan).
   - 4 commit lineer main'e: `9339976 → 5751d6d → 991625c → 223154b`.
   - Feature branch'ler push + temizlik onayı bekliyor.

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 037.3 — `atlas ai-cli exec <name> [args]`:** kurulu AI CLI'yı
  taşınabilir binary ile çalıştır (`tools/ai-cli/node_modules/.bin/<name>`).
  Tek komut launcher. Küçük.
- **Görev 023.2 — metrics `inflight` toplama:** `atlas metrics` çıktısına
  ortalama/pik inflight istatistiği ekle (SPEC 039'un tüketim tarafı).
  Küçük-orta.
- **Görev 040 — `atlas doctor --json --schema`:** doctor JSON şemasını
  ayrı komut olarak yayımla (v1 → v2 planı için hazırlık). Orta.
- **Görev 041 — Vault backup + restore:** `vault/` dizininin sıkıştırılmış
  yedeği; `atlas vault backup / restore` alt-komutları. Orta-büyük.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (745a007) ← main (223154b, 4 commit önde, PUSH bekliyor)
```
Kalan local feature branch'ler (silinecek): `feat/037.2-ai-cli-list`,
`feat/031.1-batch-dry-run-summary`, `feat/034.2-hook-regression`,
`feat/039-llm-inflight-metric`.
Önceki oturumların branchleri: `feat/paketleme-bulut-secenegi`,
`feat/tasinabilir-kurulum`, `fix/{arsivleyici-arama,
kimi-yeniden-etkinlestirme, ollama-kimligi-tasinabilir,
surum-etiketli-yedek}`.

**main'e giren 4 commit (2026-07-30 20. tur):**
```
223154b feat(039): LLM inflight metrigi (.atlas/metrics.jsonl)
991625c feat(034.2): pre-commit shim canli regresyon testi
5751d6d feat(031.1): batch --dry-run toplu step ozeti
9339976 feat(037.2): atlas ai-cli list — kurulu paketler + sürüm
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 742 passed, 12 skipped, cov 90.87%
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas ai-cli list [--json]` (yeni komut)
- `atlas run --goal-file A B --dry-run [--jobs N]` sonuna batch özet
- Pre-commit shim canlı regresyon testi (yalnız test)
- `.atlas/metrics.jsonl` satırlarına `inflight: int` alanı (opsiyonel)

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- SPEC 030/031 batch testleri (13 test) bit-uyumlu.
- `_cmd_run_goal` dokunulmadı.
- `_call_anthropic` public imzası aynı (inner param dış API'ye sızmaz).
- `_write_metric_for_data(data)` → `inflight` default None → mevcut
  SPEC 023 testleri BİT-UYUMLU.
- `ai-cli diff-summary` (037), `ai-cli update` (037.1) bit-uyumlu.
- Doctor JSON şema v1 korundu.
- `tools/hooks/pre-commit` şablon dokunulmadı.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **25 giriş bloğu** (bu tur 4
   yeni blok; toplam 21 → 25); 2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 742 test yeşil (bu turun baseline'ı 722 → +20; oturum başı 319 → +423)
- 4 lineer commit main'e; PUSH bekliyor
- 4 feature branch silinecek (kapanış temizliği)
- Yeni env YOK, yeni exit kodu YOK
- Yeni CLI komutu: `atlas ai-cli list`
- Yeni şema alanları: `.atlas/metrics.jsonl` → `inflight` (opt-in)
- Yeni test dosyaları: `test_cli_hooks_regression.py`, `test_llm_inflight.py`
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-30 altında **25 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** (toplam 64+)
- Platform sözleşmesi genişlemesi: `_call_anthropic` wrapper/inner
  ayrımı — future ek yan etkiler için desen (audit hook, tracing).
