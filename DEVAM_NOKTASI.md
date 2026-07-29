# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (10. tur — 028 + 029 + merge/push)
**Branch:** `main` (origin/main ile senkron — `bdda0ce` + docs commit)
**Working tree:** temiz
**Durum:** 2 küçük görev tamamlandı, 2 lineer commit main'e ff-merge
+ push edildi (`c6d9b3d..bdda0ce`), 2 feature branch silindi. 557/557
test yeşil, coverage %91.35, mypy strict + ruff + scan temiz.
Bilinen flaky yok.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 10. tur)

Zincirleme iki iş (`028 → 029`), her biri kendi branch'inde tek
commit; sonrasında main'e lineer ff-merge + push + branch temizlik.

1. **Görev 028** — `atlas replay --list` (`c627d95`)
   - `_extract_goal_from_yaml`, `_collect_replay_runs`,
     `_cmd_replay_list` eklendi.
   - `_cmd_replay` `--list` dallanır; positional `run_id nargs='?'`;
     ne `--list` ne `run_id` verilirse `SPEC HATASI + exit 2`.
   - Parser `--list`, `--json`, `--limit N` (varsayılan 20) alır.
   - `.atlas/runs/*.yaml` mtime desc; yalnız `.yaml` uzantısı; `.yml`
     bile listelenmez. Boş klasör = `(hiç kayıt yok)` + exit 0.
   - Goal metni ilk `^goal:` satırından ≤60 char.
   - +6 test (12 toplam).

2. **Görev 029** — `atlas metrics --alert` + yeni exit 8 (`bdda0ce`)
   - `_cmd_metrics --alert PCT` (float 0-100); cache-hit oranı eşik
     altındaysa `stderr UYARI + exit 8`.
   - `--alert 0` alarmı kapatır (sıfır eşik = devre dışı).
   - Kayıtsız + pozitif eşik = alarm ("veri yok = uyarıdır").
   - `--json` ile birleşir: JSON stdout, UYARI stderr, exit kodu
     kurala tabi.
   - Geçersiz eşik (< 0 veya > 100) → `SPEC HATASI + exit 2`.
   - Mevcut insan/JSON çıktısı **birebir korundu**.
   - +6 test (13 toplam).

3. **Merge + push + temizlik**
   - `git merge --ff-only feat/028 && git merge --ff-only feat/029` →
     2 commit lineer main'e (`bdda0ce`), merge commit YOK.
   - `git push origin main` → `c6d9b3d..bdda0ce` uzağa gitti.
   - 2 feature branch silindi (`feat/028-replay-list`,
     `feat/029-metrics-alert`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Kalan adaylar:

- **Görev 018.2 — LLM ile gerçek gözlem özetleme:** opt-in
  `Goal.obs_summarize`, ekstra LLM çağrısı. Orta scope.
- **Görev 026.1 — Unix `resource` limits:** RLIMIT_CPU, RLIMIT_AS
  opt-in. Unix-only, Windows CI'de kanıt eksik kalır.
- **Görev 026.2 — Windows Job Objects:** memory + process limits
  (`ctypes` + `SetInformationJobObject`). Bu makinede canlı
  doğrulanabilir; 026 açık ucunu kapatır.
- **Görev 030 — Multi-goal batch:** `atlas run --goal-file A.yaml
  B.yaml C.yaml` — sıralı çalıştırma, ortak hata politikası. Büyük.

Ya da başka bir öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (bdda0ce + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 2 commit (2026-07-29 10. tur):**
```
bdda0ce feat(029): atlas metrics --alert + yeni exit 8
c627d95 feat(028): atlas replay --list + --json + --limit
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 557 passed
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışı (bu turda):**
- `atlas replay --list [--json] [--limit N]` (028)
- `atlas metrics --alert PCT` (029)

**Env sözleşmesi:** değişmedi (turun eklediği yeni env değişkeni
YOK; 027'nin `ATLAS_RUNS_DIR`'i 028'de aynen kullanılır).

**Exit kodları (kümülatif, yeni ★):**
| Kod | Anlam |
|---|---|
| 0 | Başarılı |
| 1 | Sır bulundu (scan) |
| 2 | SPEC HATASI (input/config) |
| 3 | GBrain/workflow başarısız |
| 4 | Run bitmedi (done=False) |
| 5 | Action denied |
| 6 | archive-all bir görevde başarısız |
| 7 | Env / archive age parse hatası |
| **8** ★ | **029 — `atlas metrics --alert` eşik altı** |

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py`, `orchestrator/goals.py`, `AuditLog` —
  dokunulmadı.
- `_cmd_replay` sözleşmesi korundu (`atlas replay <run-id>` birebir
  çalışır; `--list` yeni bayrak, positional nargs='?' geriye uyumlu).
- `_cmd_metrics` insan formatı ve `--json` çıktısı birebir korundu;
  alarm yalnız EKLENDİ, alarm yoksa exit her zaman 0.
- `atlas run --goal-file X --run-id ID` mevcut arg akışı korunur.

**Bilinen flaky:** yok.

**Docker YASAK (kullanıcı direktifi 026'da):** portable stdlib-only
sandbox iyileştirmesi tercih edildi. Docker/container yerine env
whitelist + PATH kısıt + timeout + `shell=False` + `_jail` uyumu.
Fork bomb / OOM için Unix `resource` (026.1) ve Windows Job Objects
(026.2) opt-in olarak açık — bu turda ele alınmadı.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-29 altında **35 giriş bloğu** (+028, +029)
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 557 test yeşil (bu turun baseline'ı 545 → +12; oturum başı 319 → +238)
- 2 lineer commit main'e alındı, uzağa push edildi, 2 feature branch
  silindi (kullanıcı açık onayıyla)
- Yeni exit kodu **8** = alarm eşiği geçilemedi (`atlas metrics
  --alert` özel)
- Uncommitted değişiklik yok, working tree temiz
- Docker YASAK yürürlükte (026 kullanıcı direktifi)
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB) —
  yenilenmedi (kapsam dışı)
- DECISIONS.md 2026-07-29 altında **35 giriş bloğu** birikti
