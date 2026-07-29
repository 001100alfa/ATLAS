# 020 — İhtiyaç: `atlas run --dry-run` rehearsal modu

## Bağlam
`atlas run --goal-file <yaml>` planner'ı çağırıp gerçek action'ı
yürütüyor: dosya yazma, shell komutu, tümü. Kullanıcı **plan
görmek** istiyor ama disk/sistem üzerinde iz bırakmak istemiyorsa
(YAML'ı test etmek, prompt'u kontrol etmek) elinde tek yol var —
tam çalıştır ve sonuçları temizle. Bu yıkıcı ve pahalı.

## İhtiyaç (tek cümle)
`atlas run --goal-file <yaml> --dry-run` verildiğinde planner tek
kez çağrılsın (gerçek LLM + gerçek cost); action yerine
`"[dry-run] eylem yürütülmedi: <plan>"` stub'ı dönsün; yargıç
tek adımda tamamlar; disk/sandbox yıkıcı iş YOK.

## Ölçülebilir Başarı
- **M1 — Bayrak:** `atlas run --goal-file X --dry-run [+ --run-id ID]`
  argparser'a eklenir.
- **M2 — Action stub:** `--dry-run` verilirse mevcut `make_action`
  yerine `_dry_run_action` — `(_p) -> ("[dry-run] eylem yürütülmedi:
  <p>", 0.0)`.
- **M3 — Judge her zaman done:** `_dry_run_judge` sabit `True` döner
  — döngü ilk adımdan sonra çıkar.
- **M4 — Planner gerçek:** `make_planner(...)` çağrısı **normal** —
  LLM gerçek fiyata çağrılır, retry/backoff çalışır, cost audit'e
  yazılır (kullanıcı prompt maliyetini gerçekten görsün).
- **M5 — stdout mesajı:** `Bağlam:` başlığından sonra
  `MOD: dry-run — action yürütme kapalı` satırı; her plan
  `plan: <text>` satırıyla; her observe `observe: [dry-run] ...`
  satırıyla.
- **M6 — Exit 0:** dry-run tamamlanınca exit 0 (görev başarıyla
  simüle edildi). `LLMPlannerError` yolları hâlâ exit 7.
- **M7 — Audit:** normal `atlas-run` kayıtları + ayrıca ilk plan
  öncesi `("atlas-run", "dry_run", <goal-name>)` işareti.
- **M8 — Test:** +4 test — dry-run happy exit 0, action yürütülmedi
  (dosya yok), plan görünür, LLM hata hâlâ exit 7.
- **M9 — DECISIONS:** [KARAR] neden tek adım; neden action stub.

## Kapsam DIŞI
- Çok-adımlı rehearsal (planner N kez çağır) — YAGNI (ilk adım
  yeter; kullanıcı tam koşuyu yapacaksa `--dry-run` çıkarır).
- Cost simülasyonu — gerçek LLM çağrılır zaten (011/013 gerçek fiyat).
- İnteraktif mod (`y/N` prompt) — kapsam dışı.

## Kısıt
- `run_loop`, `make_planner`, `Goal` — dokunulmadı.
- Yeni exit kodu YOK — 0 (başarı).
- Türkçe stdout.
