# ATLAS Juggler Profili

ATLAS'ın Juggler'a kattığı **her şey** bu klasörde toplanır: eklentiler,
ACP ajanları, MCP sunucuları, komutlar, skills. Juggler'ın kendi klasörünün
(program ağacı veya `~/.juggler`) içinde ATLAS'a ait hiçbir şey durmaz.

Amaç tek cümlede: **Juggler klasörünü silip yerine güncel sürümü kurduğunda
hiçbir şey kaybolmasın.** Yeni Juggler bu profili okur ve kaldığı yerden çalışır.

## Nasıl çalışıyor

Juggler kullanıcı durumunu normalde `~/.juggler` altında tutar, ama
`JUGGLER_CONFIG_DIR` ortam değişkeni bu konumu **tamamen** taşır (kaynakta
`internal/userpaths`; kurulu ikilide de doğrulandı). ATLAS başlatıcıları bu
değişkeni `juggler-profile/home/` klasörüne çevirir:

```
juggler-profile/
  profile.json                    manifest — neyin nereye kurulacağı
  extensions/
    atlas-engineering/            ATLAS eklentisi (Apache-2.0)
  commands/                       global slash komutları
  skills/                         Juggler skill paketleri
  mcp/servers.json                MCP sunucu tanımları (şablon)
  home/                           ← JUGGLER_CONFIG_DIR hedefi (çalışma durumu)
```

`home/` **üretilen** dizindir ve git'te tutulmaz (kimlik bilgisi içerir).
Üstündeki her şey kaynaktır ve git'tedir. Senkron tek yönlüdür:
kaynak → `home/`.

## Kullanım

Başlatıcılar (`juggler-webui_Run.bat`, `juggler-desktop_Run.bat`) her açılışta
senkronu kendiliğinden çalıştırır. Elle onarmak için:

```
juggler-profile_Sync.cmd
```

Komut satırından:

```bash
python -m tools.juggler_profile.sync            # kur/tazele
python -m tools.juggler_profile.sync --verify   # yalnız denetle, yazma
```

Senkron **idempotent**tir ve yabancı kayıtları korur: profil dışından eklenmiş
bir ACP ajanı veya MCP sunucusu silinmez, yalnız ATLAS'ınkiler tazelenir.

## İlk kurulumda taşıma

`home/` ilk kez oluşturulurken, mevcut `~/.juggler` içindeki taşınabilir
kullanıcı durumu (kimlik bilgileri, varsayılan model, skill kayıt defterleri,
çalışma alanı) kopyalanır — panelde yeniden giriş yapmak gerekmez. Kaynak
dizine dokunulmaz; `~/.juggler` olduğu gibi kalır ve ATLAS dışı kullanımda
Juggler'ın varsayılanı olmayı sürdürür.

## Neyin nereye kurulduğu

| Kaynak | Hedef | Kapsam |
|---|---|---|
| `extensions/*` | `home/extensions/*` | kullanıcı |
| `commands/*` | `home/commands/*` | kullanıcı |
| `skills/*` | `home/skills/*` | kullanıcı |
| `mcp/servers.json` | `home/mcp.json` | kullanıcı |
| ACP ajanları (üretilir) | `home/acp.json` + `<proje>/.juggler/acp.json` | kullanıcı + proje |

ACP ajanları şablondan değil, kurulumun **gerçek** durumundan üretilir
(`tools/setup_gui/detect.py` → `tools/agents/*.cmd` sarmalayıcıları). Böylece
yollar her zaman bu makinedeki kuruluma uyar; şablonla gerçek arasında sapma
olmaz.

## Lisans

Eklenti ve profil içeriği **Apache-2.0** (Juggler Extension SDK ile aynı).
Juggler uygulama çekirdeği AGPL-3.0'dır, ayrı derlenir ve ayrı çalışır — bu
klasördeki hiçbir şey ona bağlanmaz. Bkz. [`docs/JUGGLER.md`](../docs/JUGGLER.md).
