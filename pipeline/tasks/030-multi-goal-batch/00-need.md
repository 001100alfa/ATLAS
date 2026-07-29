# 030 — İhtiyaç: Multi-goal batch (`--goal-file A.yaml B.yaml C.yaml`)

## Bağlam
`atlas run --goal-file X.yaml` tek görev çalıştırır. Regresyon
matrisi, CI, gecelik iş için birden fazla goal'i sırayla koşmak
elle for-loop olur — exit kodu birleştirme, run-id çakışması,
sonuç raporu kullanıcının işi. Batch mekanizması bunu araca alır.

## İhtiyaç (tek cümle)
`atlas run --goal-file A.yaml B.yaml C.yaml` sırayla çalıştırsın,
her run için bağımsız goal-id/run-id üretsin, fail-fast (varsayılan)
ya da `--continue-on-error` politikasıyla sürsün, sonda özet tablo
ve tek exit kodu dönsün.

## Ölçülebilir Başarı
- **M1 — CLI:** `--goal-file` `nargs='+'` alır (`nargs=1` verildiği
  duruma birebir uyumlu — tek dosya çağrısı 027 davranışı).
- **M2 — Sıralı yürütme:** goal dosyaları verilen sırayla koşar.
- **M3 — Run-id çakışma çözümü:**
  - `--run-id X` verildi + `N > 1` → her goal'e `X_1`, `X_2`,
    ... `X_N` verilir (çakışma önleme).
  - `--run-id` yok → her goal timestamp `<TS>_<i>`; timestamp bir
    kez alınır (aynı saniyede çakışma yok).
  - Tek dosya (N=1) → hem `--run-id X` hem timestamp mevcut 027
    davranışıyla eş (suffix YOK, geriye uyumlu).
- **M4 — Fail-fast (varsayılan):** ilk `_cmd_run_goal` başarısızlığı
  (rc != 0) → sonraki goal'ler `[ATLANDI]` işaretlenir ve
  çalıştırılmaz.
- **M5 — Continue-on-error:** `--continue-on-error` bayrağı → tüm
  goal'ler çalışır, hataları özet tabloda görünür.
- **M6 — Özet tablosu (stdout):** son satırda:
  ```
  === ATLAS batch — 3 goal ===
    1. A.yaml       ✓ done   (steps=3, run_id=A-20260729-...)
    2. B.yaml       ✗ exit=4 (steps=8, run_id=B-20260729-...)
    3. C.yaml       - atlandı (fail-fast)
  batch exit: 4
  ```
- **M7 — Exit kodu:** hepsi 0 → 0; **en yüksek** hata kodu döner
  (`max(rc for rc in codes if rc != 0)`), fail-fast'te ilk hata.
  Kural: exit 0 = hepsi başarılı; != 0 = en az bir başarısızlık.
- **M8 — Tek dosya bit-uyumlu:** `atlas run --goal-file X.yaml`
  (nargs=1) çağrısı 027 davranışı; özet tablo BASILMAZ (bir
  goal için tablo görsel gürültü).
- **M9 — --dry-run + batch:** her goal `--dry-run` alır (tek bir
  bayrak, hepsine uygulanır).
- **M10 — Test:** +8 test.
- **M11 — DECISIONS:** [KARAR] fail-fast neden varsayılan;
  neden `--run-id X` için `_1/_2` sonek yerine `_<sırı>`.

## Kapsam DIŞI
- Paralel çalıştırma (`--jobs 4`) — YAGNI, sandbox paylaşımı zor;
  ayrı iş.
- Goal-file glob (`--goal-file 'goals/*.yaml'`) — shell zaten
  genişletir; batch bunu görür.
- İnteraktif seçme (fzf-vari) — YAGNI, CI için.
- Batch içi shared state (bir goal'in çıktısı diğerinin girdisi)
  — workflow YAML'ın işi (SPEC 004), goal seviyesi değil.
- JSON batch raporu — YAGNI; stdout tablo yeter.

## Kısıt
- `_cmd_run_goal` sözleşmesi korunur — batch onu N kez çağırır.
- `_cmd_run` mevcut echo demo yolu korunur (goal_file yok +
  goal var → 027 öncesi eski demo).
- Tek `--goal-file X` çağrısı bit-uyumlu (özet tablo YOK).
- Türkçe çıktı; `[ATLANDI]` ve `✓/✗/-` işaretler.
