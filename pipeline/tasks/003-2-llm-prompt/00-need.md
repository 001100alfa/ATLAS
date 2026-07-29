# 003.2 — İhtiyaç: YAML'da `Goal.llm_prompt` opsiyonel alanı

## Bağlam
Görev 003 + 003.1 üç LLM backend'ini (claude, anthropic, acp) canlandırdı.
Prompt hâlâ `_format_prompt(goal, history, context)` içinde **sabit ve
tek**. Farklı görevler (kod yaz, kural doğrula, DXF üret) aynı gövdeyi
paylaşıyor; görev-başına özelleştirme YAML'a taşınamıyor. Sonuç:
`Goal` YAML'ında kullanıcı bir "sistem promptu" bildiremez, sadece
`goal` cümlesinden ibaret.

## İhtiyaç (tek cümle)
`Goal.llm_prompt` opsiyonel alanı (str veya None) ile kullanıcı, LLM
backend'lerin (claude/anthropic/acp) kullandığı sistem prompt'unu
YAML'dan özelleştirebilsin; alan yoksa/None ise mevcut sabit prompt
kullanılır (bit-uyumlu).

## Ölçülebilir Başarı
- **M1 — Alan opsiyonel:** `Goal` `llm_prompt: str | None = None` alır;
  mevcut YAML'lar (`llm_prompt` yok) hiç değişmeden yüklenir.
- **M2 — YAML doğrulama:** `llm_prompt` verilirse **string** olmalı;
  bool/int/list gelirse `SpecError("llm_prompt string olmalı")`;
  boş string (`""`) → `None` sayılır (kullanıcı yanlışlıkla boş
  bırakmasın diye erken uyarı yok, sabit fallback).
- **M3 — Prompt override:** `llm_prompt` set edilmişse `_format_prompt`
  çıktısı **onunla başlar**; ardından mevcut yardımcı bloklar
  (context/history/kısıtlar) eklenir. Kullanıcı bloğu şu şablonda
  görünür:
  ```
  <goal.llm_prompt>

  Görev: <goal.goal>

  [<mevcut context bloğu, varsa>]
  [<mevcut sözleşme + son gözlem bloğu>]
  ```
- **M4 — Backend genelliği:** Değişiklik `_format_prompt` içinde;
  üç backend (claude, anthropic, acp) yeniden derlenmeden aynı
  şekilde davranır.
- **M5 — Test kapsamı:** `test_goals.py`'de 3 yeni test (opsiyonel
  yükleme, tip yanlış, boş string → None); `test_planner_llm.py`'de
  1 test (custom prompt gövdede görünür); `test_planner_anthropic.py`
  ve `test_planner_acp.py`'de sırasıyla 1 test daha (backend uyumu).
  Toplam +6 test. Coverage ≥ %90.
- **M6 — DECISIONS:** [KARAR] tek maddede — nedenler (görev-başına
  özelleştirme neden gerekli; sabit fallback niye korunuyor).

## Kapsam DIŞI
- LLM'e sistem/user rol ayrımı — anthropic API tek "user" mesajı
  ile devam ediyor; sistem promptu YAML kullanıcıdan içeriye tek
  gövde olarak akıyor. Rol ayrımı Görev 010+.
- Prompt caching (Anthropic) — Görev 011 token cost ile birlikte.
- Prompt versiyonlama / template motoru — Görev 015+.

## Kısıt
- `Goal` sözleşmesi genişleyebilir ama **yeni alanlar opsiyonel**
  default'lu (SPEC 006'nın kalıbı) — eski YAML'lar SpecError almaz.
- `_format_prompt` imzası (`goal, history, context=None`) korunur.
- Türkçe hata mesajı, teknik terim korunabilir.
- İstisna adları `*Error` sonekli (mevcut standard).
