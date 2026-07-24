# ATLAS Pipeline
**Needs -> Prompts -> Spec -> Plan -> Build -> Test -> Revise -> Simplify -> Ship**

9 aşama, 50 alt-beceri. Her alt-beceri = adlandırılmış slash komut.
Aşama atlanamaz; her aşamanın gate'i sağlanmadan sonrakine geçilmez.
Artefaktlar: pipeline/tasks/XXX/ altında toplanır.

## Zincir Haritası
```
BAŞLA: Dağınık Fikir
  │
  ▼
┌─ 00 NEEDS ──────────────────────────────────────────────┐
│ /dump → /grill-need → /scope → /measure → /prioritize   │
└──────────────────────── gate: ölçülebilir NEED ─────────┘
  ▼
┌─ 01 PROMPTS ────────────────────────────────────────────┐
│ /prompt-maker → /grill-me → /how-to → /optimize-prompt  │
│ → /domain-voice → /anti-hallucination → /write-a-skill  │
│ → /handoff                                              │
└──────────────────────── gate: belirsizliksiz yönerge ───┘
  ▼
┌─ 02 SPEC ───────────────────────────────────────────────┐
│ /fr-extract → /interface → /acceptance → /nonfunctional │
│ → /open-questions → /approve-spec ★KULLANICI ONAYI      │
└──────────────────────── gate: ONAYLI şartname ──────────┘
  ▼
┌─ 03 PLAN ───────────────────────────────────────────────┐
│ /wbs → /risk → /sequence → /adr → /publish-plan         │
└──────────────────────── gate: riskli WP ilk ────────────┘
  ▼
┌─ 04 BUILD ──────────────────────────────────────────────┐
│ /branch → /tdd-core → /execute-wp → /drift-check        │
│ → /close-build                                          │
└──────────────────────── gate: sapmasız, commit'li ──────┘
  ▼
┌─ 05 TEST ───────────────────────────────────────────────┐
│ /ref-test → /edge-hunt → /error-contract → /invariants  │
│ → /coverage-type → /trace                               │
└──────────────────────── gate: FR↔test izlenebilir ──────┘
  ▼
┌─ 06 REVISE ─────────────────────────────────────────────┐
│ /self-review → /agent-review → /classify → /fix-round   │
│ → /lessons                                              │
└──────────────────────── gate: K/M bulgular kapalı ──────┘
  ▼
┌─ 07 SIMPLIFY ───────────────────────────────────────────┐
│ /deadcode → /dedupe → /api-shrink → /doc-sync           │
│ → /prove-behavior                                       │
└──────────────────────── gate: testler değişmeden yeşil ─┘
  ▼
┌─ 08 SHIP ───────────────────────────────────────────────┐
│ /version → /changelog → /release → /evidence → /retro   │
└──────────────────────── gate: ölçüt KANITLA kapandı ────┘
  ▼
BİTİŞ: Sürümlenmiş, kanıtlı, dokümante teslimat
```

## Sürücü komutlar (aşama düzeyi — zinciri otomatik yürütür)
/need "istek" → /spec N → /build N → /finish N
Alt-beceri komutları ince kontrol içindir; sürücüler zinciri sırayla koşar.

## Hızlandırılmış mod
Küçük iş (<50 satır): 01 ve 07 zincirleri kısaltılabilir.
02 onayı ve 05 zinciri HİÇBİR ZAMAN atlanamaz. Karar DECISIONS'a.
