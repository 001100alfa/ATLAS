# 003.2 — SPEC: Goal.llm_prompt opsiyonel alanı

## 1. Fonksiyonel Gereksinimler
- **FR1:** `Goal` dataclass'ına `llm_prompt: str | None = None` alanı
  eklenir; **son sıraya** (SPEC 006'nın `inject_context`/`context_limit`
  desenini takip eder). Alan opsiyonel default'lu; eski `Goal(...)`
  çağrıları etkilenmez.
- **FR2:** `load_goal` YAML'da `llm_prompt` alanını okur:
  - Yoksa: `None`.
  - `None`: `None`.
  - Boş string `""`: `None` (kullanıcı yanlışlıkla boş bıraktıysa
    sessiz fallback — mevcut sabit prompt kullanılır).
  - Non-empty string: `str` (strip'lenmez; kullanıcı formatını korur).
  - Diğer tip (bool/int/list/dict): `SpecError("llm_prompt string
    olmalı, gelen: <tip>")`.
- **FR3:** `_format_prompt(goal, history, context=None)` üretim mantığı:
  - `goal.llm_prompt` `None` ise: **mevcut sabit gövde** (bit-uyumlu).
  - `goal.llm_prompt` non-empty str ise: yeni şablon:
    ```
    <goal.llm_prompt>

    Görev: <goal.goal>

    [Önceden bilinen bağlam bloğu — mevcut mantık, context varsa]
    Sözleşme: TEK SATIRLIK plan komutu üret. İzin verilen fiiller: ...
    Biçim: fiil:arg1[:arg2]. Örnek: ...

    Son <=3 gözlem (varsa): ...

    Sadece plan satırını yaz, başka açıklama YOK.
    ```
  - Yani kullanıcı promptu **en üste** girer, mevcut kısıt+context
    blokları altına eklenir. Bu, kullanıcının "sistem rolü"nü tanımlarken
    ATLAS'ın plan sözleşmesini bozmasını engeller (kısıt satırı sonda).
- **FR4:** Üç backend (`claude`, `anthropic`, `acp`) değişmez —
  `_format_prompt` merkezi olduğu için otomatik uyumluluk.

## 2. Arayüz Sözleşmeleri
```
src/atlas_core/orchestrator/goals.py       (edit)
  # Goal alan sırasına: llm_prompt: str | None = None
  # load_goal: raw.get("llm_prompt"), validation kolu

src/atlas_core/orchestrator/planner.py     (edit: _format_prompt)
  # if goal.llm_prompt: prepend + include kısıt
  # else: mevcut şablon (bit-uyumlu)

tests/test_goals.py                        (edit: +3 test)
tests/test_planner_llm.py                  (edit: +1 test — özel prompt claude)
tests/test_planner_anthropic.py            (edit: +1 test — özel prompt anthropic gövdesi)
tests/test_planner_acp.py                  (edit: +1 test — özel prompt acp session/prompt)
tests/goals/llm_custom_prompt.yaml         (yeni fixture)
```

## 3. Kabul Kriterleri
- **AC1 — Alan yok:** `hello.yaml` (llm_prompt anahtarı yok) yüklenir,
  `goal.llm_prompt is None`.
- **AC2 — Alan None:** `llm_prompt: null` → `None`.
- **AC3 — Alan boş:** `llm_prompt: ""` → `None` (sessiz fallback).
- **AC4 — Alan geçerli:** `llm_prompt: "Sen kod eleştirmenisin..."` →
  string aynen `goal.llm_prompt`'ta.
- **AC5 — Tip hatası:** `llm_prompt: 42` → `SpecError` (mesaj "string
  olmalı" içerir).
- **AC6 — Format bit-uyumlu (None):** `_format_prompt` `llm_prompt=None`
  ile üretilen string mevcut testlerle regresyon vermez.
- **AC7 — Format yeni (str):** `llm_prompt="ROLE: mühendis"` verilirse
  üretilen prompt "ROLE: mühendis" ile başlar; ardından "Görev:" satırı;
  ardından mevcut context/sözleşme/history blokları.
- **AC8 — Claude backend:** `test_planner_llm.py` — özel prompt
  YAML'dan bind edilirse claude subprocess stdin'de görünür.
- **AC9 — Anthropic backend:** özel prompt request gövdesindeki
  `messages[0].content` içinde geçer.
- **AC10 — ACP backend:** özel prompt `session/prompt` request'inin
  `prompt[0].text` içinde geçer.
- **AC11 — Kalite kapıları:** ruff + mypy strict + pytest yeşil;
  coverage ≥ %90.

## 4. Q → Kararlar
- **Q1 — Neden strip yok?** Kullanıcı özel formatı (indent, blok
  komutları) korumak isteyebilir. Fazla strip düzenlemesi verimi düşürür.
- **Q2 — Neden anthropic'te system rolü değil?** Rol ayrımı (system vs
  user) daha büyük bir kararla (Görev 010+) beraber taşınacak. Şu an
  tek user mesajı yeterli.
- **Q3 — Neden boş string → None?** Kullanıcı yanlışlıkla `llm_prompt:` yazıp
  değer vermezse YAML `None` döner; `""` verirse aynı kabul (fallback).
  Bu, "yeni alan koyup mevcut davranışı bozma" ilkesiyle uyumlu.
