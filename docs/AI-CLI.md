# Yedek AI Kodlama CLI'ları (OpenCode + Kilo)

Claude Code CLI limit aşımında veya kullanıcı tercihine göre proje içinde
kullanılabilen iki taşınabilir yedek AI kodlama ajanı. Config/data **proje
içine** hapsedilir; kullanıcının home dizinine dokunulmaz.

| CLI | Paket | Çalıştırma | Runtime |
|---|---|---|---|
| OpenCode | `opencode-ai` | `opencode_Run.cmd` | Kendi kendine yeten ikili (Node gerekmez) |
| Kilo | `@kilocode/cli` | `kilo_Run.cmd` | Node CLI (Node gerekir) |

## Kurulum (bir kez, internet gerekir)
Node + npm gerekir (kurulum aşamasında; OpenCode çalışırken Node istemez).
```bat
setup-ai-cli.cmd
```
Proje-yerel npm kurulumu yapar (global değil) → `tools\ai-cli\node_modules`.
OpenCode'un platforma özel ikilisi (ör. `opencode-windows-x64`) otomatik iner.

## Kullanım
```bat
opencode_Run.cmd            :: OpenCode TUI (proje = ATLAS)
opencode_Run.cmd run "..."  :: tek mesajla çalıştır
kilo_Run.cmd                :: Kilo TUI
kilo_Run.cmd run "..."      :: tek mesaj
```
Başlatıcılar ATLAS'ı PATH'e ekler; her iki CLI de `atlas` / `atlas-sections`
araçlarını kabuktan çağırabilir.

## Taşınabilirlik — config/data nereye yazılır
Her şey `tools\ai-cli\home\` altında kalır (git'te tutulmaz):

| CLI | Mekanizma | Konum |
|---|---|---|
| OpenCode | `XDG_*` (4'lü: config/data/state/cache) | `tools\ai-cli\home\{config,data,state,cache}` |
| Kilo | `HOME`/`USERPROFILE` override | `tools\ai-cli\home\kilo-home\.config\kilo` vb. |

**Neden farklı:** OpenCode Windows'ta da `XDG_*` değişkenlerini onurlandırır.
Kilo (Node) Windows'ta `XDG_*` yerine `$HOME` köklü yollar (`~/.config/kilo`)
kullanır; bu yüzden `kilo_Run.cmd` `HOME`/`USERPROFILE`'ı proje-yerele yönlendirir
(npm `.cmd` shim'i override'ı yuttuğu için node doğrudan çağrılır). *nix'te her
iki CLI de `XDG_*` ile taşınabilirdir. Bkz `DECISIONS.md` 2026-07-24.

## API anahtarları
Her CLI kendi kimlik akışını kullanır (`opencode auth`, Kilo ilk çalıştırmada
sorar). Anahtarlar **repoya girmez**; proje-yerel config dizinlerinde (yukarıda)
tutulur. Anahtar girişi kullanıcı tarafından yapılır.

## Git / taşıma
`tools\ai-cli\node_modules` (platforma özel, büyük) ve `tools\ai-cli\home`
(çalışma-zamanı verisi) git'te tutulmaz; `package.json` + `package-lock.json`
tutulur. Başka makinede: `setup-ai-cli.cmd` yeniden kurar.
