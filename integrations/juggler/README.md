# ATLAS Engineering — Juggler Extension

ATLAS'ın doğrulanmış mühendislik ve hafıza yeteneklerini
[Juggler](https://github.com/juggler-ai/juggler) ajan workbench'ine açan
eklenti. Juggler'ın web UI ve masaüstü GUI'si, ATLAS'ın Claude Code çekirdeğine
ön-yüz olur; bu eklenti de ATLAS araçlarını o arayüz içinde kullanılabilir kılar.

**Lisans:** Apache-2.0 (Juggler'ın Extension SDK'sıyla aynı). Juggler uygulama
çekirdeği AGPL-3.0'dır; ayrı bir uygulamadır ve bu eklentiye/ATLAS'a copyleft
yükümlülüğü taşımaz.

## Yetenekler

| Yetenek | Tür | ATLAS köprüsü |
|---|---|---|
| `atlas_section` | Context Item (LLM aracı) | `atlas-sections <i\|box> … --json` |
| `atlas_recall` | Context Item (LLM aracı) | `atlas context <topic>` (GBrain) |
| `/atlas-section` | Command (slash) | `atlas-sections … --json` |
| system-prompt | Prompt katkısı | etkin araçları modele tanıtır |

- **`atlas_section`** — çelik kesit özellikleri (A, Iy, Iz, Wel, Wpl, kg/m;
  EN 1993, SI-mm). Deterministik, yan etkisiz (`category: read`).
- **`atlas_recall`** — bir konu için ATLAS GBrain hafızasından önceki
  kararları/bağlamı getirir.
- **`/atlas-section`** — LLM'siz hızlı hesap: `/atlas-section i 1000 300 12 20`.

## Gereksinim: ATLAS PATH'te olmalı
Eklenti `atlas` ve `atlas-sections` launcher'larını **PATH üzerinden** çağırır.
ATLAS dizinini (veya taşınabilir bundle'ı) PATH'e ekle. Doğrula:
```bash
atlas-sections i --h 1000 --b 300 --tw 12 --tf 20 --json
```
`shell.exec` izni bu yüzden gereklidir (manifest'te bildirilir).

## Kurulum (Juggler tarafı)
```bash
juggler ext validate <atlas>/integrations/juggler   # admission check
juggler ext link     <atlas>/integrations/juggler   # ~/.juggler/extensions'a symlink + hot-reload
```
Juggler'ı başlat/yeniden bağlan; Ayarlar → Extensions altında "ATLAS Engineering"
görünür. Ayrıntı ve derleme: ATLAS `docs/JUGGLER.md`.
