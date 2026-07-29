# 010.1 — İhtiyaç: claude subprocess `--append-system-prompt` argümanı

## Bağlam
SPEC 010 anthropic backend'inde `goal.llm_prompt`'u API'nin native
`system` alanına taşıdı. claude backend'i (`--print` subprocess)
hâlâ **prepend** kalıbıyla çalışıyor — kullanıcı promptu gövdenin
başına ekleniyor, sonra `--print` stdin'e beslenir. Claude Code CLI
bunun için `--append-system-prompt <text>` argümanını destekler;
sistem promptu doğrudan iletilir, `messages` gövdesine karışmaz.

## İhtiyaç (tek cümle)
`goal.llm_prompt` set edildiğinde claude subprocess çağrısı
`--append-system-prompt <prompt>` argümanı ile başlatılsın; stdin'e
verilen prompt gövdesi anthropic backend'i gibi `include_system=False`
kalıbıyla üretilsin (llm_prompt gövdede geçmez).

## Ölçülebilir Başarı
- **M1 — Argüman geçilir:** `goal.llm_prompt` non-empty str →
  `argv = [bin, "--print", "--output-format", "text",
  "--append-system-prompt", <prompt>]`.
- **M2 — llm_prompt yoksa:** argv eskisi gibi (5 element, `--append-system-prompt`
  YOK) → geriye uyumlu.
- **M3 — Gövde:** `_format_prompt(..., include_system=False)` — llm_prompt
  gövdede geçmez (anthropic ile simetri).
- **M4 — Fabrika değişmez:** `_claude_planner(goal, context=None)`
  imzası korunur; kararlı closure.
- **M5 — ACP değişmez:** `--append-system-prompt` claude-özel;
  acp backend prepend kalıbını korur (protokolde ayrı yol).
- **M6 — Test:** +3 test — llm_prompt varsa argv'de, yoksa argv
  temiz, gövde llm_prompt içermez.
- **M7 — DECISIONS:** [KARAR] claude native system → anthropic ile
  simetri; 003.2 test kalıbı güncellendi.

## Kapsam DIŞI
- ACP session-level system prompt — Görev 010.2 (ACP genişleyince).
- claude backend'in başka özel argümanlarını (`--allowedTools`,
  `--dangerously-skip-permissions`) ATLAS'a taşıma — kapsam DIŞI.
- Model seçimi (`--model`) — Görev 009 anthropic'e uygulandı;
  claude subprocess kendi başında model seçimi yapar.

## Kısıt
- `_call_claude` imzası genişleyebilir ama **default'lu ve keyword-only**
  yeni parametre; mevcut çağrılar etkilenmez.
- Türkçe hata; istisna adları `*Error` sonekli.
