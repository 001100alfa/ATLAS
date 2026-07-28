# 004 — İhtiyaç: WorkflowEngine handler kaydı & gerçek yürütme

## Bağlam
`src/atlas_core/workflows/engine.py` sağlam bir motor: YAML'daki adımı
kayıtlı handler'a bağlar, bilinmeyen adım = hata, her adım audit'e
yazılır. Ama `WorkflowEngine.register()` **hiçbir yerde çağrılmıyor**;
`workflows/gorev-tam-tur.yaml` çalıştırılırsa 1. adımda `WorkflowError`
atar. CLI'da `atlas workflow` komutu yok.

## İhtiyaç (tek cümle)
`atlas workflow run <yaml>` gerçek handler'larla çalışsın; en az 3
handler (`pipeline.gate`, `pipeline.test`, `memory.archive`) uçtan uca
yürüsün ve audit'te iz bıraksın.

## Ölçülebilir Başarı
- **M1:** `atlas workflow run <mini.yaml>` — üç kanıt handler'ının tümü
  sırayla çalışır, exit 0.
- **M2:** Bilinmeyen handler → `WorkflowError`, exit 6, audit'te
  `workflow_error` kaydı.
- **M3:** Bir handler başarısız olursa (örn. `pipeline.gate` dosya yok)
  → sonrakiler çalışmaz, exit 6.
- **M4:** `atlas audit-verify` koşu sonrası GEÇERLİ.
- **M5:** Coverage ≥ %90 korunur; mevcut testler regresyonsuz.

## Kapsam DIŞI
- 10 pipeline handler'ının tamamı (needs/prompts/spec/plan/revise/
  simplify/ship) — LLM veya operatör etkileşimi gerektirir, Görev 005+.
- `requires_approval:true` interaktif akış — Görev 006.
- LLM entegrasyonu — Görev 003.

## Kısıt
- `WorkflowEngine.register()` / `run()` sözleşmesi **değişmez**.
- `atlas run` (Görev 002) dokunulmaz.
- Yıkıcı işlem yok: handler'lar sandbox dışında etkili olabilir
  (pytest, archive) ama `--dry-run` bayrağı ile no-op koşabilir.
