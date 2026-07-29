# SKILL — Prompt Engineering (ATLAS mühendislik görevleri)

> Bu rehber, `plan_kind: llm` görevlerinde LLM'e verilecek prompt'un
> nasıl yazılacağını gösterir. Görev-tipi bazlı kalıplar, ATLAS-özel
> sözleşmeler, sık yapılan hatalar ve karşı örnekler bir aradadır.

**Ön okuma:** `pipeline/tasks/003-llm-planner/02-spec.md`,
`pipeline/tasks/003-2-llm-prompt/02-spec.md`,
`pipeline/tasks/010-anthropic-system-role/00-need.md`.

---

## 1. Sistem promptu vs kullanıcı promptu

ATLAS'ta iki katman vardır:

| Katman | YAML alanı | LLM'de karşılığı |
|---|---|---|
| **Sistem promptu** | `Goal.llm_prompt` | Anthropic body.system / Claude `--append-system-prompt` |
| **Kullanıcı görevi** | `Goal.goal` | Anthropic messages[0].content içinde "Görev:" satırı |

**Kural:** persona/rol/uzun kurallar → `llm_prompt`. Tek cümlelik
hedef → `goal`. Bunu tersine çevirmek modeli karıştırır.

**Örnek — doğru:**
```yaml
goal: "yay çelik kesitini EN 1993'e göre doğrula"
llm_prompt: |
  Sen ATLAS'ın yapı mühendisi planlayıcısısın.
  - Tüm hesapları EN 1993-1-1'e göre yap.
  - Birim: mm, N, MPa (karışım = hata).
  - Sınır durumu SLU (ULS) öncelikli.
  - Şüpheliyse önce OKU (`read:...`), sonra YAZ.
```

**Örnek — yanlış (rol goal'a sızmış):**
```yaml
goal: "Sen yapı mühendisisin. EN 1993 uygula. Kesiti doğrula."
llm_prompt: null
```

---

## 2. Görev-tipi kalıpları

### 2.1 Kod yazma

**Kalıp:**
```yaml
goal: "src/foo.py'da bar() fonksiyonunu yaz — girdi list[int], çıktı max int"
plan_kind: llm
action_allowlist: [write, read]
judge_kind: file_exists
judge_arg: "src/foo.py"
llm_prompt: |
  Sen Python 3.12 geliştiricisisin.
  - Tip ipuçları zorunlu (from __future__ import annotations kullan).
  - Docstring Türkçe.
  - Kenar durumlar: boş liste, negatif sayı.
  - Kısıtsız tekli plan: write:<dosya>:<içerik>.
```

**Dikkat:** `action_allowlist`'e `read` eklemek, LLM'in mevcut kodu
kontrol edip birlikte-var-olan biçimi (imports, docstring stili)
öğrenmesini sağlar.

### 2.2 Test yazma

**Kalıp:**
```yaml
goal: "tests/test_foo.py — src/foo.py::bar için 4+ test yaz"
plan_kind: llm
action_allowlist: [write, read]
judge_kind: file_exists
judge_arg: "tests/test_foo.py"
llm_prompt: |
  Sen pytest test yazarısın.
  Kapsama listesi:
  - Happy path (tipik girdi).
  - Boş / minimum girdi.
  - Maksimum / sınır girdi.
  - Yanlış tip → TypeError beklentisi.
  Türkçe test isimleri: def test_bos_liste_reddedilir(): ...
```

### 2.3 DXF üret

**Kalıp:**
```yaml
goal: "kanat_profili.dxf — 100x50 dikdörtgen kesit, EN 1993 sınıf 1"
plan_kind: llm
action_allowlist: [write]
judge_kind: file_exists
judge_arg: "kanat_profili.dxf"
llm_prompt: |
  Sen ezdxf ile DXF üreten bir mühendissin.
  Sözleşme:
  - Birim: mm (asla inch, m, cm).
  - Katman "KESIT" (üstteki büyük harf).
  - Renk: 7 (varsayılan siyah).
  - Kapalı polyline; başlangıç = bitiş.
  Plan formatı: shell:python -c "ezdxf ile üret".
```

### 2.4 EN 1993 doğrulama

**Kalıp:**
```yaml
goal: "kanit.md — kolon N_Ed=200 kN, L=3m, IPE160 için burkulma kontrol"
plan_kind: llm
action_allowlist: [write, read]
judge_kind: file_exists
judge_arg: "kanit.md"
llm_prompt: |
  Sen EN 1993-1-1 uzmanısın.
  Zorunlu:
  - Kesit seçimini justifie et (Iy, iy).
  - Burkulma boyu Lcr belirt.
  - λ_bar hesabı adım adım.
  - χ interpolasyonu Şekil 6.4'ten.
  - Emniyet: N_Ed / (χ · A · fy / γ_M1) < 1.0.
  Çıktı: kanit.md — Markdown, tablo + tek satır sonuç.
```

---

## 3. ATLAS-özel: plan çıktı sözleşmesi

`plan_kind: llm` görevlerde ATLAS **tek satır plan komutu** bekler:
```
fiil:arg1[:arg2...]
```

- `write:<yol>:<içerik>` — dosya yaz (sandbox içi).
- `read:<yol>` — dosya oku.
- `shell:<komut>` — shell çalıştır (`shell_allow_regex` sınırlı).

`llm_prompt`'ta bunu tekrar etmene gerek yok — ATLAS otomatik
ekler. Yalnız görev-özel kısıtları yaz.

**Yanlış:** `llm_prompt: "Cevabında write:x veya read:y kullan"`
— tekrarlı ve LLM'i şaşırtır.

**Doğru:** `llm_prompt` yalnız rol/kural; ATLAS çıktı formatını
kendi ekler.

---

## 4. Karşı örnekler

### 4.1 Çok geniş prompt

**Kötü:**
```yaml
goal: "kod yaz"
llm_prompt: "Sen iyi bir programcısın."
```

Modelin ne yapacağı belirsiz. Dosya adı yok, dil yok, sınıf/fonksiyon
yok.

### 4.2 Birim eksik

**Kötü:**
```yaml
goal: "kolonu doğrula (yük 200)"
```

200 ne? kN? N? MPa? Ölçek hatasına gider. Her sayı bir birimle
eşleşmeli.

### 4.3 Çıktı formatı belirsiz

**Kötü:**
```yaml
goal: "IPE profil analizi yap"
```

Dosya mı? Konsol mu? Format?

**İyi:** "rapor.md — IPE160 için Iy, iy, Wel_y hesabı (tablo)".

### 4.4 Sistem promptu çıktı formatını bozar

**Kötü:**
```yaml
llm_prompt: |
  Konuşkanca cevap ver. Her adımı uzun uzun açıkla.
```

ATLAS **tek satır** bekler. Uzun-uzun cevap → LLMPlannerError
(çok satırlı yanıt ilk satırı alınır ama işlemin ilk niyeti
bozulur).

**İyi:** "Kısa ve öz. Tek plan satırı, açıklama sonda gelirse
görmezden geliriz."

---

## 5. Prompt caching (SPEC 015)

`prompt_cache: true` **ne zaman?**
- `llm_prompt` uzun (> 1000 karakter).
- Aynı görevi peş peşe çok kez çalıştırıyorsan (retry, debug).
- Aynı persona farklı görevlerde tekrarlanıyor.

**Kâr:**
- Cache-read: normal fiyatın %10'u (SPEC 015.1).
- 5 dk ephemeral (Anthropic sözleşmesi).

**Kâr YOK:**
- `llm_prompt` kısa (< 200 karakter) → cache overhead > kâr.
- Görev tek seferlik → cache 5 dk bekler, kullanılmaz.

**Örnek:**
```yaml
llm_prompt: |
  # <uzun EN 1993 kural listesi, 3000 karakter>
prompt_cache: true
```

---

## 6. Model seçimi (SPEC 009)

`Goal.llm_model` — görev başına model.

| Görev tipi | Öneri |
|---|---|
| Basit kod yaz | `claude-3-5-haiku-latest` (hızlı, ucuz) |
| Karmaşık analiz | `claude-3-5-sonnet-latest` (varsayılan) |
| Ağır muhakeme | `claude-3-opus-latest` (yavaş, pahalı) |

**Kural:** default sonnet yeter; opus'a yalnız muhakemeli
görevlerde geç.

---

## 7. Streaming (SPEC 019)

`Goal.stream: true` — algılanan gecikme düşer.

**Ne zaman?**
- Kullanıcı canlı görsün istiyorsun (log tail gibi).
- Uzun response beklenen görev.

**Kâr YOK:**
- Kısa yanıtlar (< 100 char); SSE overhead > kâr.
- CI/batch senaryolar; tam response beklemek daha basit.

---

## 8. Retry & jitter (SPEC 008 + 014)

```bash
export ATLAS_LLM_RETRIES=3      # geçici hata → 3 retry
export ATLAS_LLM_BACKOFF=1.0    # üstel taban
export ATLAS_LLM_JITTER=0.5     # thundering herd önle
```

429 alırsan (rate limit), `Retry-After` header'ı otomatik saygı
görür (SPEC 014). Retry sözleşmesi kaç deneme yapıldığını
`ATLAS_LLM_TRACE=1` ile stderr'a bastırır.

---

## 9. Cost izleme (SPEC 011 + 013 + 023)

```bash
export ATLAS_LLM_PRICE_IN=3      # Sonnet
export ATLAS_LLM_PRICE_OUT=15
export ATLAS_LLM_TRACE=1

atlas run --goal-file gorevler/rapor.yaml
# stderr:
#   [llm] anthropic tokens: in=1234 (cache=0 r=500) out=456 cost≈$0.010680

atlas metrics
# 20 çağrı özeti, cache-hit oranı %, toplam cost

atlas dashboard
# Son 10 run — hangi görev, kaç adım, ne kadar cost
```

---

## 10. Öz-denetim kontrolü (görevi başlatmadan önce)

1. `atlas doctor` — backend/key/model doğru mu?
2. `atlas doctor --ping` — Anthropic gerçekten erişilebilir mi?
3. `atlas run --goal-file X --dry-run` — plan makul mü?
4. Cost tahmini > bütçe mi? YAML'ı revize et.
5. `atlas run --goal-file X` — gerçek çalıştır.
6. `atlas metrics` — cache oranı beklendiği gibi mi?

---

## Ek: Prompt caching + head+tail keep etkileşimi

`ATLAS_LLM_OBS_CHARS=500` + `head+tail=100+100` (SPEC 018 + 018.1):
- Uzun stderr'ın **son 100 char'ı** (genelde hata mesajı) LLM'e ulaşır.
- Ortadaki 200-N char atlanır: `[... N char atlandı ...]`.
- LLM plan üretmede son satırdaki hataya odaklanabilir.

## Yararlanılan belgeler
- `DECISIONS.md` — 27 giriş bloğu (2026-07-29): backend, retry, cache,
  metrics.
- `pipeline/tasks/*` — her görevin 00-need + 02-spec + 09-ship.
- Anthropic Messages API — <https://docs.anthropic.com/>.
- ACP (Agent Client Protocol) — protokol referansı.
