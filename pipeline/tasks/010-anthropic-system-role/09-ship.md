# 010 — Ship

## Sonuç
Anthropic Messages API'sinde `system` alanı devreye girdi.
`Goal.llm_prompt` artık request gövdesinin `system` alanına yazılıyor
(assistant persona kilidi güçlü); `messages[0].content` sadece ATLAS'ın
varsayılan gövdesi (kısıt + görev + context + gözlem) taşıyor.

- `_format_prompt`'a `include_system: bool = True` opsiyonel keyword;
  anthropic backend `False` geçirir (llm_prompt gövdeden atlanır).
- `_call_anthropic`'e `system: str | None = None` keyword; None/boş →
  alan gövdeye eklenmez (temiz payload).
- claude/acp backend'ler değişmez (prepend davranışı korundu — Görev
  010.1+ ayrı iş).

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: _format_prompt include_system,
                                            _call_anthropic system, _anthropic_planner)
tests/test_planner_anthropic.py           (edit: SPEC 003.2 testi 010 ile
                                            değiştirildi; +2 yeni test — system
                                            alanı doğrulaması)
pipeline/tasks/010-anthropic-system-role/*.md  (5 artefakt)
```

## Sözleşme değişmezliği
- `Planner`, `make_planner`, `Goal` — dokunulmadı.
- `_format_prompt` yeni parametre **keyword-only + default'lu** →
  eski çağrılar (unit test) etkilenmez.
- `_call_anthropic` yeni parametre **keyword-only + default'lu** →
  aynı garanti.

## Kalite kapıları
- pytest: **397 passed** (395 → +2 net)
- mypy strict + ruff: temiz

## Branch
`feat/010-anthropic-system-role` — 009 üstünde tek commit.

## Not
Anthropic Messages API `system` alanı `role` ayrımı verir; model
sistem promptunu **user mesajından daha güçlü** izler. ATLAS'ın
plan sözleşmesi (`TEK SATIRLIK yaz`) `messages[0].content` içinde
kalarak öncelik dengesi doğal: kullanıcı persona `system`, çıktı
kuralı `user`.

## Bekleyen
- claude subprocess `--system` argümanı — Görev 010.1
- ACP oturum-level system prompt — Görev 010.2 (ACP genişleyince)
