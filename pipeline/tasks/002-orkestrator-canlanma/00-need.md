# 002 — Orkestratörün Canlanması / İhtiyaç

## Bağlam
`atlas run` bugün yer tutucu (echo) plan/act/judge ile çalışıyor
(`src/atlas_core/cli.py:74` `_cmd_run` docstring: "Gerçek eylem yerine
yer tutucu (echo) kullanır"). Orkestratör iskeleti (`run_loop`, audit,
bütçe) sağlam ama **bugüne kadar tek bir gerçek görev sürmedi**.
CLAUDE.md "her görev 9 aşamadan geçer" diyor; fiili durum "hiçbir görev
geçmedi". Bu açık, projenin kendi kurallarına güveni aşındıran en
büyük teknik borç.

## İhtiyaç (tek cümle)
`atlas run` **bir** gerçek dış hedefi (dosya yaz, komut çalıştır, çıktı
doğrula) uçtan uca sürebilsin ve audit zinciri bu koşuyu kanıtlasın.

## Ölçülebilir Başarı
- **M1:** `goals/hello.yaml` hedefi → tek koşuda `done=True`, exit 0.
- **M2:** Koşu sonrası `atlas audit-verify` GEÇERLİ (exit 0).
- **M3:** Koşu sırasında audit'e en az 5 kayıt yazılır
  (plan/observe/plan/observe/done).
- **M4:** Sandbox dışına yazma denemesi (örn. `../` ile kaçış) reddedilir
  ve audit'e "denied" kaydı düşer.
- **M5:** Yeni pytest testleri yeşil; toplam coverage ≥ %90 korunur;
  mevcut `test_platform.py` regresyonsuz geçer.

## Kapsam DIŞI (bu görev değil)
- LLM entegrasyonu (Claude Code / ACP çağrısı) — Görev 003.
- Çoklu-ajan orkestrasyonu.
- WorkflowEngine handler kaydı (`pipeline.*`, `memory.archive`) — Görev 004.
- GBrain FTS indeksi — Görev 005.

## Kısıt
- `src/atlas_core/orchestrator/core.py` sözleşmesi (`Action`, `Judge`,
  `run_loop`) **değişmez** — mevcut testler kırılmayacak.
- Yıkıcı işlem yok: shell action'lar sandbox dizinine hapsedilir.

## Kaynak
- DECISIONS.md ilgili girdiler (2026-07-24 platform katmanı kararları)
- `src/atlas_core/orchestrator/core.py` (mevcut sözleşme)
- `src/atlas_core/security/audit.py` (hash zinciri)
