# 006 — İhtiyaç: Otomatik context injection

## Bağlam
Görev 005 GBrain'e SQLite FTS5 önbelleği getirdi — `context_for(topic)`
artık ölçekli çalışıyor. Ama ATLAS ajanı hâlâ **hiçbir görev başlangıcında
GBrain'e sormuyor**: `cli.py::_cmd_run_goal` yalnız goal.goal metnini
`run_loop`'a geçiriyor. Sonuç: LLM planner (Görev 003 ile canlandı) her
turda kör başlıyor — vault'ta duran ilgili notları görmüyor.

CLAUDE.md açık: "GBrain: her göreve başlarken context_for(konu) çağrılır
— ajan geçmiş bilgiyle başlar". Şu an bu satır yerine getirilmiyor.

## İhtiyaç (tek cümle)
`atlas run --goal-file <yaml>` başlarken GBrain.context_for(goal.goal) bir kez
çağrılsın; sonuç LLM planner'ın prompt'una **otomatik** eklensin; static planner
kırılmasın, LLM devre dışıyken sıfır maliyet olsun.

## Ölçülebilir Başarı
- **M1:** `atlas run --goal-file <llm.yaml>` çalışırken planner'a
  giden prompt'ta GBrain context bloğu (`## GBrain bağlamı:`) yer alır;
  vault'ta ilgili not varsa `[[wikilink]]` satırı da eklenir.
- **M2:** `plan_kind: static` görevler **hiç etkilenmez** — context
  hesaplanmaz (fazladan disk/CPU maliyeti yok).
- **M3:** GBrain kayıt bulamazsa (`(kayıt yok)`) prompt'a hiçbir şey
  eklenmez veya sabit "(bağlam yok)" satırı eklenir; planner ne olursa
  olsun çalışır (kırılmama).
- **M4:** Enjeksiyon opsiyonel kapatılabilir: `ATLAS_CONTEXT=off` env veya
  `Goal.inject_context: false` YAML alanı — kullanıcı üzerinde kontrol.
- **M5:** Testler: injection açıkken/kapalıyken prompt farkı; static
  görevde çağrı yok; boş vault'ta hata yok. Coverage ≥ %90 korunur.
- **M6:** Sözleşme değişmez: `run_loop`, `Planner`, `make_planner`,
  `GBrain.recall/remember/context_for` imzaları korunur. Yeni **opsiyonel**
  parametre / arayüz eklenir.

## Kapsam DIŞI
- Context uzunluk kırpma: LLM token budget yönetimi — ileri görev.
- Semantic search / embedding: 005 fallback + FTS yeterli.
- Context'in Judge'a veya Action'a enjeksiyonu — bu görev yalnız planner.
- Rerank / MMR: `recall()` mevcut sıralaması kullanılır.

## Kısıt
- `Planner` sözleşmesi (`Callable[[str, list[tuple[StepKind, str]]], str]`)
  **değişmez**. Enjeksiyon planner **dışında**, planner fabrikasında
  closure'a bind edilerek yapılır.
- `Goal` genişlerse yeni alan **opsiyonel varsayılanlı** olmalı — eski
  YAML'lar SpecError almaz.
- stdlib-only; yeni bağımlılık yok. GBrain zaten import ediliyor.
- Türkçe mesajlar, `*Error` sonekli istisnalar.
