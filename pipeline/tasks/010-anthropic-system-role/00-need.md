# 010 — İhtiyaç: Anthropic system rolü ayrımı

## Bağlam
SPEC 003.2 `Goal.llm_prompt`'u tek "user" mesajının başına ekledi;
DECISIONS 2026-07-29'da not düşüldü: "rol ayrımı Görev 010+". Bu
görev o notu kapatır.

Anthropic Messages API'sinde `system` alanı üst-düzey opsiyonel bir
sistem promptudur: model onu **daha güçlü** izler ("assistant persona"
kilidi vs. sadece "user"'ın ilk cümlesi). ATLAS'ın kullanıcı
prompt'unun modelin çıktı sözleşmesini bozmasını engelleme hedefi
zaten var; system alanına taşımak bu hedefi kuvvetlendirir.

## İhtiyaç (tek cümle)
`goal.llm_prompt` set edilmişse **anthropic** backend request
gövdesindeki `system` alanına yazılsın; `messages[0].content` sadece
ATLAS'ın plan sözleşmesi + görev metni + context + geçmiş gözlemleri
taşısın (kullanıcı prompt'u ile karışmasın).

## Ölçülebilir Başarı
- **M1 — Anthropic gövdesi:** `goal.llm_prompt` set edildiyse gövde
  `{"model": ..., "max_tokens": ..., "system": <llm_prompt>,
  "messages": [{"role":"user","content": <ATLAS varsayılan gövdesi>}]}`.
  `llm_prompt` **artık** messages içinde geçmez.
- **M2 — Boş/None prompt:** `system` alanı gövdeye eklenmez
  (Anthropic API bunu tolerate eder ama gereksiz payload gönderilmez).
- **M3 — claude/acp değişmez:** iki backend `_format_prompt`'ın
  mevcut "prepend" davranışını korur — protokoller system field'ı
  yok/farklı; refactor kapsam DIŞI.
- **M4 — Yardımcı ayrımı:** `_format_prompt`'a `include_system: bool`
  parametresi eklenir. `True` (varsayılan): mevcut davranış.
  `False`: `goal.llm_prompt` **atlanır** — anthropic backend `False`
  geçer, system alanını ayrıca kendisi ekler.
- **M5 — Test:** +4 test — system alanında, messages'ta değil,
  boş prompt system yok, claude/acp regresyon.
- **M6 — DECISIONS:** [KARAR] neden system alanı; neden claude/acp
  hâlâ prepend.

## Kapsam DIŞI
- claude subprocess'a system rolü aktarımı (`claude --system-prompt`
  argümanı vs.) — Görev 010.1+.
- ACP protokolü system rolü (ACP'de session-level system prompt
  şu an alt-küme).
- `messages` çok-mesajlı geçmiş rolü.

## Kısıt
- `Planner`, `make_planner` imzaları korunur.
- `_format_prompt` imzasında yeni **default'lu opsiyonel** parametre.
- Türkçe hata; istisna adları `*Error` sonekli.
