# Güvenlik Politikası

## Zafiyet bildirimi
Bir güvenlik açığı bulursan **herkese açık issue AÇMA**. Bunun yerine depo
sahibiyle özel iletişime geç (GitHub Security Advisory: repo → Security →
Report a vulnerability). Makul sürede (hedef: 90 gün) düzeltme + koordineli
açıklama yapılır.

## Kapsam
- **Çekirdek kütüphane** (`src/sections`, `src/atlas_core`): sayısal doğruluk,
  girdi doğrulama, denetim izi bütünlüğü.
- **Platform** (`atlas_core.security`): hash-zincirli `AuditLog` (oynama tespiti),
  `scan_secrets` sır tarayıcı.

Kapsam **dışı** (ayrı uygulamalar, kendi güvenlik süreçleri): Juggler çekirdeği
(AGPL-3.0), yedek AI CLI'ları (OpenCode/Kilo/Cline/Kimi/Goose) ve Claude Code.

## Sır yönetimi
- Sırlar **asla koda gömülmez**; `.env` kullanılır ve `.env` commit edilmez
  (`.gitignore`).
- `atlas scan <yol>` bilinen sır kalıplarını tarar; CI'da `src` üzerinde
  otomatik çalışır (bulgu → başarısız).
- AI CLI kimlik anahtarları proje-yerel config dizinlerinde tutulur, repoya
  girmez (bkz `docs/AI-CLI.md`).

## Denetim izi
Kritik eylemler `AuditLog`'a hash zinciriyle yazılır; `atlas audit-verify`
zincir bütünlüğünü doğrular (oynanmışsa `BOZULMUŞ`).

## Bağımlılıklar
Çalışma bağımlılıkları `pyproject.toml`'da sabitli; gömülü çalışma-zamanı
bileşenlerinin lisans/sürümleri `docs/THIRD_PARTY_LICENSES.md`'de.
