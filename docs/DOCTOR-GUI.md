# Sağlık & Güncelleme Ajanı (GUI)

```
DOCTOR.cmd   ← çift tıklayın
```

Tarayıcıda tek ekran açılır. Ajan sırayla ölçer, her bulgunun **kanıtını**,
**kaynağını** ve **çözümünü** yazar; düzeltilebilenleri tek tıkla düzeltir ve
sonunda gerçekten çalıştığını **canlı bağlantı testiyle** doğrular.

Kurulum sihirbazı (`SETUP.cmd`) *ilk kurulum* içindir. Bu ekran *kurulumdan
sonra* içindir: bir şey güncellendiğinde neyin bozulduğunu bulur.

## Neden ayrı bir araç

Bu projede çalışan parçalar birbirinden bağımsız güncellenir: Juggler paneli,
beş ACP ajanı (opencode/kilo/cline/kimi/goose), Python çekirdeği, Ollama, ATLAS
eklentisi. Herhangi biri güncellendiğinde arıza **başka** bir yerde görünür —
panelde ajan açılmaz, araç çağrısı hata verir. Ajan bu zinciri baştan sona
ölçtüğü için "ne değişti, ne bozuldu" sorusu tahmin işi olmaktan çıkar.

## Adımlar

| Adım | Ne ölçer |
|---|---|
| Çalışma zamanları | Python (gömülü/venv), `atlas_core` gerçekten import ediliyor mu, Node, npm |
| Juggler paneli | İkililer, sürüm ↔ üstakım, **ikilinin parmak izi**, yedek, eklenti kurulu mu, **eklenti ↔ panel uyumluluğu** |
| ACP ajanları | Her ajan kurulu mu, yerel sürüm ↔ kayıt defterindeki son sürüm (npm/PyPI/GitHub) |
| Yerel AI | Taşınabilir Ollama, sunucu yanıt veriyor mu, model var mı |
| Yapılandırma | `acp.json` okunabilir mi, **kayıtlı ajan yolları hâlâ var mı**, `atlas-sections --json` köprüsü |
| Sürüm izi | Son sağlıklı kayıttan bu yana hangi bileşen değişti |
| Canlı sağlık | Panelin yaptığı GERÇEK el sıkışma: `initialize` + `session/new` |

Her adım bağımsızdır: biri çökse bile tarama sürer, çöken adım bir bulguya
dönüşür.

## Bu araç neyi yakalar (tasarım gerekçesi)

**1. Panelin kendi kendini güncellemesi.** Juggler'da yerleşik bir
güncelleyici vardır (`internal/updatecheck` + `updateapply`): çalışan `.exe`'yi
yeniden adlandırıp yerine indirdiğini koyar. ATLAS paneli
`tools/juggler/juggler.exe` üzerinden çalıştırdığı için bu, **ATLAS'ın
kullandığı ikilinin habersiz değişmesi** demektir. İndirilen sürümde yerel
düzeltmeler bulunmaz ve ajanlar bağlanamaz hâle gelir.

Ajan bunu **SHA-256 parmak iziyle** yakalar: "Sağlıklı hâli kaydet" dediğinizde
ikilinin özeti saklanır; sonraki taramada dosya değiştiyse ekran bunu söyler ve
"Yedekten geri al" düğmesini gösterir.

**2. Eklenti ↔ panel uyumsuzluğu.** ATLAS eklentisi
`"engineApi": "^1.0.0"` bildirir. Panel motor API'sini büyüttüğünde eklenti
**sessizce** yüklenmez — hata verilmez, araçlar sadece kaybolur. Ajan gerçek
`juggler ext validate` komutunu çalıştırıp sonucu gösterir. Panel güncellemesini
kabul etmeden önce bakılacak tek denetim budur.

**3. Güncelleme sonrası kırılan yollar.** Bir CLI güncellendiğinde paket yolu
değişebilir; `acp.json` eski yolu göstermeye devam eder. Panelde ajan görünür
ama başlamaz. Ajan her kayıtlı yolu dosya sisteminde doğrular, "Yolları tazele"
kaydı mevcut kuruluma göre yeniden yazar.

**4. Kurulu ≠ çalışıyor.** Son adım ajanı gerçekten başlatır ve panelin yaptığı
iki JSON-RPC çağrısını yapar. Yeşil rozet, panelde de çalışacağı anlamına gelir.

## Düzeltme eylemleri

Hepsi **idempotent**tir; hiçbiri kullanıcı verisi silmez.

| Eylem | Ne yapar |
|---|---|
| Şimdi yedek al | `tools/juggler/*.exe` → `.atlas/doctor/juggler-backup/` (+ sürüm notu) |
| Yedekten geri al | Yedeği geri yazar — bozuk güncellemeden tek tıkla dönüş |
| Eklentiyi kur / tazele | profil kaynağı → `juggler-profile/home/extensions/` |
| Profili kur / tazele | ATLAS'ın Juggler'a kattığı her şeyi senkronlar, kayıtları ATLAS'a çevirir |
| Ajanları kaydet / Yolları tazele | `acp.json` + `tools/agents/` sarmalayıcılarını yeniden üretir |
| Sunucuyu başlat | Taşınabilir Ollama'yı `127.0.0.1:11435`'te kaldırır |
| Güncelle (ajan) | `npm install <paket>@latest --prefix tools/ai-cli` veya `pip install -U kimi-cli` |
| Çekirdeği yeniden kur | `setup-portable.cmd` (canlı log) |
| Sağlıklı hâli kaydet | Sürümleri + panel parmak izini `.atlas/doctor/baseline.json`'a yazar |

**Panel ikilisi otomatik indirilmez.** Juggler AGPL lisanslı ayrı bir
uygulamadır ve kaynaktan derlenir; ajan yalnız güvenli sırayı gösterir
(yedek → ayrı klasörde derle → uyumluluk denetimi → ancak sonra kopyala).
Ayrıntı: [JUGGLER.md](JUGGLER.md).

## Rapor

"Rapor oluştur" → `.atlas/doctor/reports/saglik-<tarih>.md`. Ekrandaki üçlünün
aynısını taşır (ölçülen / kaynağı / çözüm) artı kurulu-sürüm tablosu. Bir arıza
kaydına eklenebilir; iki rapor karşılaştırılarak "ne değişti" görülür.
`.atlas/` git'te tutulmaz.

## Çevrimdışı davranış

Güncelleme denetimi npm, PyPI ve GitHub'a sorar. İnternet yoksa tarama
**durmaz**: sürüm satırları "sorgulanamadı" der, kurulum ve bağlantı
denetimlerinin tamamı yapılır. Uzak sorgular 6 saniyede kesilir ve süreç
boyunca önbelleklenir.

## Güvenlik

Sunucu yalnız `127.0.0.1`'e bağlanır ve her istek oturum jetonu ister
(makinedeki başka bir uygulama arayüzü süremez). Hiçbir kimlik bilgisi
işlenmez; giriş gerektiren ajanlar için ajan yalnız doğru komutu gösterir,
giriş `SETUP.cmd` → "Ajanları bağla" ekranından kullanıcının kendi
tarayıcısında/terminalinde yapılır.

## Komut satırından

```bash
python -m tools.doctor_gui.checks
```

Tüm adımları koşup JSON basar (CI veya betik için). `ATLAS_DOCTOR_PORT` ile
sunucu portu sabitlenebilir.
