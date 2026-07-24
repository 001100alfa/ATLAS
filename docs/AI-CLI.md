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

## Juggler "ACP Agents" olarak kullanım
Her iki CLI de ACP (Agent Client Protocol) sunucusu olabilir (`... acp`) ve
Juggler'ın **ACP Agents** panelinden model olarak sürülebilir. Config'i üret:
```bat
setup-acp-agents.cmd
```
Bu, `<project>\.juggler\acp.json` yazar (Juggler global config'in üstüne alır) ve
`kilo` + `opencode` ajanlarını kaydeder. Juggler'ı başlat; model seçicide
**ACP Agents → kilo / opencode** görünür.

**Neden generator gerekiyor (yaygın hata):** Juggler ACP ajanını
`exec.LookPath(command)` + doğrudan `exec` ile spawn eder — kabuk yok.
- `command: "kilo"` → kilo **proje-yerel**, PATH'te yok → *"not found on PATH"*.
- `kilo.cmd` shim'i PE ikili olmadığından Go `exec` ile çalışmaz.

Doğru kayıt (generator bunu yazar):
- **Kilo** (Node CLI): `command:"node"`, `args:[<kilo bin>, "acp"]`,
  `env` HOME/USERPROFILE → proje-yerel.
- **OpenCode** (derlenmiş ikili): `command:<opencode.exe mutlak yolu>`,
  `args:["acp"]`, `env` XDG_* (4'lü) → proje-yerel.

`.juggler/acp.json` makineye özel mutlak yollar içerir; git'te tutulmaz —
generator (`setup-acp-agents.cmd`) tutulur. Başka makinede yeniden çalıştır.

## API anahtarları
Her CLI kendi kimlik akışını kullanır (`opencode auth`, Kilo ilk çalıştırmada
sorar). Anahtarlar **repoya girmez**; proje-yerel config dizinlerinde (yukarıda)
tutulur. Anahtar girişi kullanıcı tarafından yapılır.

## Git / taşıma
`tools\ai-cli\node_modules` (platforma özel, büyük) ve `tools\ai-cli\home`
(çalışma-zamanı verisi) git'te tutulmaz; `package.json` + `package-lock.json`
tutulur. Başka makinede: `setup-ai-cli.cmd` yeniden kurar.
