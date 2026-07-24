# Changelog
Format: Keep a Changelog / SemVer.

## [0.2.0] - 2026-04-16
### Eklendi
- GBrain: birleşik hafıza arayüzü (remember/recall/context_for;
  anahtar kelime + graf-komşuluğu skorlaması).
- atlas_core platformu: beyin (Obsidian vault + wikilink graf),
  arşiv, güvenlik (hash-zincirli audit + sır tarayıcı),
  orkestratör (registry + bütçeli çağrı + P-A-O-R döngüsü),
  YAML workflow motoru (gstack).
- security-auditor ve orchestrator subagent'ları; vault başlangıç grafı.

## [0.1.0] - 2026-04-16
### Eklendi
- `sections` paketi: kaynaklı I-kesit ve kutu kesit özellikleri
  (A, Iy, Iz, Wel, Wpl, kg/m), EN 1993 gösterimi, SI-mm.
- `atlas-sections` CLI.
- Ajan altyapısı: 5 komut, 3 subagent, 2 skill, hooks, CI.
