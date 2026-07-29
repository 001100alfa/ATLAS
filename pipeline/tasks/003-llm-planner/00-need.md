# 003 — İhtiyaç: LLM planner entegrasyonu

## Bağlam
`orchestrator/planner.py` iki mod tanır: `static` (deterministik) ve
`llm` (yalnız `stub`). `ATLAS_LLM=stub` dışındaki her değer için
`NotImplementedError("Görev 003'te eklenecek")` fırlatır. Sonuç: `atlas
run --goal-file <llm.yaml>` gerçek bir görevi otonom sürüklemez —
plan sabittir. Görev 002 bu boşluğu bilerek bıraktı ve gerekçesini
DECISIONS 2026-07-24'te belgeledi: Windows subprocess/UTF-8 tuzağı
+ orkestratör yenidoğan; tek turda iki büyük risk tutulmaz.

## İhtiyaç (tek cümle)
`ATLAS_LLM=claude` verildiğinde planner `claude --print` subprocess'ini
güvenli, UTF-8 sabit ve timeout'lu şekilde çağırıp her adımın planını
gerçekten LLM'den alsın; stub yolu bozulmasın, sözleşme kırılmasın.

## Ölçülebilir Başarı
- **M1:** `ATLAS_LLM=claude` altında `make_planner(goal)` gerçek bir
  callable döner (NotImplementedError YOK); testte monkeypatch
  edilen subprocess çağrısı her tur bir plan üretir.
- **M2:** Subprocess Windows'ta `shell=False` + UTF-8 + timeout ile
  çağrılır; `.cmd`/`.exe` shim'lerine takılmaz (CVE-2024-4030 sonrası
  Python 3.12 kalıbıyla uyumlu).
- **M3:** Hata sınıfı `LLMPlannerError` yeni exit kodu **7** ile
  CLI'da yakalanır; kullanıcı asıl nedeni (`claude bulunamadı`,
  `timeout 60s`, `exit=1: <stderr ilk 200>`) görür.
- **M4:** `ATLAS_LLM=stub` davranışı bit-uyumlu korunur; mevcut
  `test_planner.py` yeşil kalır (test tek satır güncellenebilir).
- **M5:** Yeni test dosyası + `test_cli_direct.py` genişlemesi ile
  hem birim (planner factory) hem in-process CLI kapsamı gezilir;
  coverage ≥ %90 korunur (mevcut %95).
- **M6:** DECISIONS 2026-07-24 UTF-8 kalıbı + yeni Windows `.cmd`
  çözümü DECISIONS 2026-07-29 girdisine yazılır.

## Kapsam DIŞI
- `ATLAS_LLM=acp` ve `ATLAS_LLM=anthropic` — açık `NotImplementedError`
  ile bırakılır (mesajda "Görev 003.1" işaret edilir); bu görev claude
  subprocess'iyle sınırlı.
- Prompt engineering: sistem promptu **sabit ve kısa**. Sofistike
  şablonlama, tool-use, streaming Görev 010+.
- Cost tracking / token metrikleri — CallBudget mevcut soyut kredi
  modeliyle yeterli; gerçek token maliyeti Görev 011.
- Retry / backoff: 1 çağrı, 1 timeout, 1 hata. Yeniden deneme
  planner sözleşmesi üstünde değil, run_loop dışında düşünülür.

## Kısıt
- `Planner` sözleşmesi (`Callable[[str, list[tuple[StepKind, str]]], str]`)
  ve `run_loop` imzası **değişmez**.
- `Goal` sözleşmesi genişleyebilir ama eski YAML'lar (`plan_kind: llm`
  varsayılan alan yok) `SpecError` almamalı — yeni alanlar opsiyonel
  varsayılanlı.
- stdlib-only: `subprocess`, `shutil`, `os`, `shlex`. Yeni bağımlılık yok.
- İstisna adı `*Error` sonekli (proje N818 standardı).
- Türkçe log/hata mesajları; teknik terimler orijinal.
