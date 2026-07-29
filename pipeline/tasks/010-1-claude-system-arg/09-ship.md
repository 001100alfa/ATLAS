# 010.1 — Ship

## Sonuç
claude subprocess `--append-system-prompt <text>` argümanı kullanmaya
başladı. `goal.llm_prompt` set edildiğinde system promptu doğrudan
CLI argümanı olarak verilir; stdin'e beslenen gövde `include_system=
False` kalıbıyla üretilir (anthropic backend'i ile birebir simetri).

Bu, kullanıcı persona promptunun **stdin gövdesine karışmadan** claude'un
kendi sistem rolü yoluna aktarılmasını sağlar — model system'i user'dan
daha güçlü izler.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: _call_claude system keyword,
                                            _claude_planner include_system=False +
                                            system bind)
tests/test_planner_llm.py                 (edit: 003.2 testi 010.1 kalıbına
                                            dönüştü; +2 yeni test)
pipeline/tasks/010-1-claude-system-arg/*.md  (5 artefakt)
```

## Sözleşme değişmezliği
- `_call_claude` yeni parametre **keyword-only + default None** → eski
  çağrılar etkilenmez.
- `_claude_planner(goal, context=None)` imzası korundu.
- `Planner`, `make_planner`, `LLMPlannerError` — dokunulmadı.
- ACP backend değişmez — protokolde native `--append-system-prompt`
  yok, prepend korundu.

## Kalite kapıları
- pytest: **420 passed** (419 → +1 net)
- mypy strict + ruff: temiz

## Branch
`feat/010.1-claude-system-arg` — 013 üstünde tek commit.

## Kullanım örneği
```yaml
# YAML aynı — kullanıcı fark etmez, yalnız arka planda argv değişir
goal: "kesit hesabı yap"
plan_kind: llm
llm_prompt: |
  Sen EN 1993'e hakim yapı mühendisisin.
  Kararlarını sınır durum kontrolleriyle gerekçelendir.
```

## Bekleyen
- ACP session-level system prompt — Görev 010.2 (ACP genişleyince).
