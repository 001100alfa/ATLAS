# ATLAS Mimari

## Katmanlar
1. **Ajan katmanı** (`.claude/`): Claude Code'un davranışı.
   CLAUDE.md talimat, commands/ iş akışları, agents/ uzman roller,
   settings.json izin + deterministik hooks (lint/test otomatik).
2. **Bilgi katmanı** (`skills/`): alan kuralları. Ajan göreve
   başlamadan ilgili SKILL.md'yi okur — halüsinasyon yerine kayıtlı kural.
3. **Kod katmanı** (`src/`): üretilen kütüphaneler. src-layout,
   pyproject ile paketlenir, `atlas-sections` gibi CLI'lar üretir.
4. **Doğrulama katmanı** (`tests/` + CI): her sayısal fonksiyon
   el hesabı referans değeriyle test edilir (rel_tol=1e-9 analitik,
   katalog karşılaştırmalarında %2-3 tolerans + gerekçe).

## Veri akışı (bir görevin yaşamı)
GitHub issue → /gorev N → skill okuma → branch → kod+test →
tester subagent → reviewer subagent → PR → CI (ruff+mypy+pytest) → merge.

## Karar kaydı
Mimari kararlar DECISIONS.md'de [KARAR] etiketiyle tutulur;
büyük kararlar için docs/adr/ altına ADR dosyası açılır.
