# 009 — İhtiyaç: `Goal.llm_model` opsiyonel alanı

## Bağlam
SPEC 003.1 anthropic backend'i `ATLAS_LLM_MODEL` env değişkeniyle
model seçiyor. Bu, aynı proseste çalışan **her görev** için tek model
demek — bir görev için "opus", diğeri için "haiku" istemek env
takasını gerektiriyor. 003.2 kalıbıyla simetrik olacak şekilde
`Goal.llm_model` opsiyonel alanı YAML'a taşınmalı: görev bazında
model kararı.

## İhtiyaç (tek cümle)
`Goal.llm_model: str | None = None` alanı ile YAML'da model bildirilebilsin;
anthropic backend'i `goal.llm_model` verilmişse onu, verilmediyse
mevcut env (`ATLAS_LLM_MODEL`) yolunu kullansın; claude/acp backend'ler
alanı yok saysın (bugünlük — tam model tabanlı seçim onların protokolüne
bağlı).

## Ölçülebilir Başarı
- **M1 — Alan opsiyonel:** `Goal` `llm_model: str | None = None`; eski
  YAML'lar hiç değişmeden yüklenir.
- **M2 — YAML doğrulama:** `str` veya `None` yalnız; başka tip →
  `SpecError("llm_model string olmalı, gelen: <tip>")`. Boş string →
  `None` (003.2 kalıbıyla simetrik sessiz fallback).
- **M3 — Anthropic backend:** `goal.llm_model` set edilmişse
  request gövdesindeki `model` alanı onunla dolar; env yolu ihmal
  edilir.
- **M4 — Öncelik:** goal.llm_model > `ATLAS_LLM_MODEL` env >
  `_DEFAULT_ANTHROPIC_MODEL` sabiti.
- **M5 — claude/acp uyum:** alan sözleşme değişmezi; her iki
  backend uygulamada yok sayar (mevcut env yolları bozulmaz).
- **M6 — Test:** +5 test — alan yok/geçerli/boş/tip hatası + anthropic
  gövdede model doğrulama.
- **M7 — DECISIONS:** [KARAR] öncelik zinciri + neden claude/acp
  şimdilik yok say.

## Kapsam DIŞI
- claude backend'e `--model` argümanı geçme (Görev 010+).
- ACP protokolü model bildirme (agent'a bağlı, protokol dışı).
- Model bilinip bilinmediğini doğrulama (Anthropic listesi
  değişken — env override zaten var).

## Kısıt
- `Goal` sözleşmesi genişleyebilir ama **yeni alan opsiyonel
  default'lu** (003.2 kalıbı) — eski YAML'lar SpecError almaz.
- Backend `_call_anthropic` imzasında `model` zaten var; yalnız
  hangi kaynaktan geldiği değişir.
- Türkçe hata; istisna adları `*Error` sonekli.
