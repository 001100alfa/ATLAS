# 036 — İhtiyaç: `tools/ai-cli/` npm install drift fix

## Bağlam
035 turunda not düşülen drift: `tools/ai-cli/package.json` `opencode-ai:
^1.18.8` ama `tools/ai-cli/node_modules/opencode-ai/bin/opencode.exe
--version` → **1.18.8** (üstü kurulmamış). Semver `^` prefix'i 1.18.x
aralığında en yeniyi kabul eder — upstream 1.18.9 çıktığında proje-yerel
kurulum aynen kalmış. `npm install` çalıştırılınca node_modules senkron
olacak.

Ek gözlem: `790c9da` commit mesajı "opencode 1.18.8 -> 1.18.9" diyor
ama gerçek diff **cline 3.0.46 -> ^3.0.47** bump'ı — mesajla gerçek
diff karışmış (auto-update'in başka bir mekanizması olabilir). Yani
opencode `^1.18.8` hep aynıydı; drift `node_modules`'ün 1.18.9'a
yükselmemiş olmasından.

## İhtiyaç (tek cümle)
`tools/ai-cli/` altında `npm install` çalıştır; `node_modules/
opencode-ai/bin/opencode.exe` 1.18.9'a yükselsin; `package-lock.json`
değişirse commit'e kat.

## Ölçülebilir Başarı
- **M1 — npm install:** proje-yerel `tools/node/npm.cmd --prefix
  tools/ai-cli install` (portable npm; makine bağımsız). Global
  npm yoksa da çalışır.
- **M2 — Sürüm doğrulama:** `opencode_Run.cmd --version` → **1.18.9**
  (035 turunda 1.18.8 idi).
- **M3 — package-lock diff:** `tools/ai-cli/package-lock.json`
  güncellenmesi bekleniyor (1.18.8 → 1.18.9 entry). Commit'e kat.
- **M4 — package.json aynen:** `^1.18.8` semver aralığı zaten
  1.18.9'u kapsıyor; DEĞİŞMİYOR (035 kalıbı: package.json'u da
  bump etmek breaking, ekstra iş — semver zaten kabul ediyor).
- **M5 — Regresyon:** Ana repo pytest kalite kapısı üstten koşar
  (676 aynen kalmalı; Python kod dokunulmadı).
- **M6 — 5 diğer launcher smoke:** cline/kimi/goose/kilo etkilenmedi
  (bu turda dokunulmadı ama kontrol).
- **M7 — DECISIONS:** [KARAR] `^` semver semantiği — package.json
  değişmeden node_modules yükselir; auto-update politikasının
  boşluğu; commit mesaj disiplini.

## Kapsam DIŞI
- `package.json` opencode/cline/kilo bump — kullanıcı yeni major/minor
  isterse ayrı iş.
- Global npm çağrısı — portable npm tercih edilir.
- Auto-update politikasının değişimi (`atlas-portable.json`) — YAGNI.
- Diğer paketlere fresh install — yalnız opencode drift'i.

## Kısıt
- `tools/node/npm.cmd` var olmalı (portable node/npm 2026-07-28
  taşınabilir kurulumla depoda).
- Ağ bağlantısı gerekli (npm registry).
- `package.json` DEĞİŞMEZ (semver aralığı 1.18.9'u kapsıyor);
  `package-lock.json` DEĞİŞİR.
- `node_modules/` gitignore'da (git'e girmez); binary dosyalar
  local olarak yükseltilir.
