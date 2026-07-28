# Başka bir bilgisayara taşıma

Kısa yol: **PAKETLE.cmd → klasörü RAR'la → karşı makinede aç → BASLAT.cmd.**
Kurulum sihirbazı, sürüm takibi, yol düzeltme yok.

## Gönderen tarafta

1. Paneli kapatın.
2. `PAKETLE.cmd` çift tık. Yaptığı üç şey:
   - çalışan ajan süreçlerini kapatır (kilitli dosya arşive yarım girer —
     ölçüldü: `cline.exe` yüzünden `npm install` EBUSY, `goose.exe` yüzünden
     klasör taşıma "Permission denied"),
   - makine parmak izini siler (karşı tarafta kendini uyarlasın diye),
   - neyin taşındığını ve toplam boyutu raporlar.
3. Klasörü sıkıştırın (`PAKETLE.cmd --arsiv D:\ATLAS.rar` derseniz WinRAR/7-Zip
   kuruluysa arşivi kendisi üretir).

### Boyut

Klasör bugün **~5,7 GB** (ölçüldü). İki küçültme seçeneği var:

| Seçenek | Kazanç | Ne kaybedersiniz |
|---|---|---|
| `--yagsiz` | ~271 MB | hiçbir şey (indirme arşivleri + derleme önbellekleri; yeniden üretilir) |
| `--bulut` | **1,8 GB** | yerel model çalıştırma (`tools/ollama/lib`) — bulut modelleriyle çalışırken gerekmez |

İkisi birlikte: ~3,7 GB'a iner.

`--bulut` **ölçümle** doğrulandı (2026-07-28): `tools/ollama/lib` tamamen
yokken ollama sunucusu açıldı, `*-cloud` modelini listeledi, `/api/generate`
yanıt üretti ve goose gerçek bir turu tamamladı. Yerel model (`ollama pull` ile
inen ağırlıklar) çalıştıracaksanız kullanmayın; kullandıysanız
`SETUP.cmd > Yerel AI` ile geri gelir.

Kullanımı:

```
PAKETLE.cmd --bulut --arsiv D:\ATLAS.rar   # haric tutmayi kendisi yapar (onerilen)
PAKETLE.cmd --bulut --sil                  # klasorden siler, elle sikistirirsiniz
PAKETLE.cmd --bulut                        # sadece raporlar + haric tutma listesi verir
```

`--bulut` tek başına **hiçbir şey silmez**: elle sıkıştıracaksanız listelenen
klasörü arşive almamanız gerekir (yoksa yine girer). Silmesini istiyorsanız
`--sil` ekleyin.

## Alan tarafta

1. Arşivi açın (yol fark etmez; `C:\ATLAS`, `D:\isler\ATLAS`, USB… hepsi olur).
2. **`BASLAT.cmd`** çift tık. Sırayla:
   - **uyarlar** — sarmalayıcılar, ACP kayıtları ve Juggler profili yeni yola
     göre yeniden üretilir (yalnız makine/yol değiştiyse; değişmediyse anında geçer),
   - **denetler** — eksik bir şey varsa tek satırla söyler, ama açılışı engellemez,
   - **günceller** — politikaya göre (aşağıya bakın),
   - **paneli açar** — `http://localhost:3939/`.

Başka hiçbir adım yok. `SETUP.cmd` yalnız sıfırdan kurulum içindir; taşınan
klasörde gerekmez.

## Neden bu klasör taşınabilir?

| Bileşen | Nerede | Not |
|---|---|---|
| Python | `runtime/python/` | gömülü yorumlayıcı, sistem Python'u gerekmez |
| node + npm | `tools/node/` | kilo/cline bunu kullanır (eskiden makinedeki node'a mutlak yol yazılıyordu) |
| git-bash | `tools/git/` | kimi'nin Shell aracı ister; MinGit |
| Ajanlar | `tools/ai-cli/`, `tools/goose/` | kurulumları ve hesap durumları klasör içinde |
| Panel | `tools/juggler/` | ikili + `juggler-profile/` (eklenti, komutlar, kimlik) |
| Yerel model ucu | `tools/ollama/` | bulut modelleri için yeterli |

Kural: **hiçbir üretilmiş dosyada makineye özgü mutlak yol kalmaz.**
Sarmalayıcılar `%ROOT%` göreli yazar; kalanları `BASLAT.cmd` yeniden üretir.

Depo içi kopya her zaman makinedekini yener (`tools/portable/runtimes.py`) —
taşındığında ayakta kalan tek şey odur.

## Güncellemeler

`atlas-portable.json`:

```json
{ "autoUpdate": "agents", "checkEveryHours": 24 }
```

- `agents` (varsayılan): açılışta günde bir kez denetler, npm/pip ajanlarını
  (opencode, kilo, cline, kimi) sessizce günceller.
- `notify`: hiçbir şey kurmaz, yalnız "şu güncellemeler var" der.
- `off`: denetim de yapmaz (ağa hiç çıkmaz).

Beklemeden bakmak için `GUNCELLE.cmd`.

**Panel ikilisi hiçbir ayarda otomatik güncellenmez.** Gerekçe ölçülmüş bir
olaydır: 2026-07-27'de panelin kendi güncelleyicisi çalışan ikiliyi değiştirdi,
içindeki yerel yamalar (ACP `authenticate`) yok oldu ve ajanlar bağlanamaz hâle
geldi. Panel için yalnız bildirim çıkar; kurulumu `DOCTOR.cmd`teki güvenli
sırayla yapılır: yedek → ayrı klasörde derle → `ext validate` → kopyala.

## Bulut modeli kimliği

`ollama signin` kimliği bir **anahtar çiftidir** ve normalde
`%USERPROFILE%\.ollama\id_ed25519` altında, yani deponun DIŞINDA durur.
Ölçüldü: bu anahtar olmadan bulut modeli ilk istekte `{"error":"Unauthorized"}`
döner — goose ve kimi çalışmaz.

Bu yüzden ollama sunucusunun ev dizini `tools/ollama/home`a çevrildi ve anahtar
ilk `BASLAT.cmd`te oraya bir kez kopyalanır. Taşınan arşivin anahtarı, açıldığı
makinenin anahtarıyla **ezilmez** (o makinede hiç hesap olmayabilir).

Yeni makinede bulut modeli hâlâ `Unauthorized` diyorsa: `BASLAT.cmd` çıktısında
`auth.ollama` satırına bakın; "yok" diyorsa bir kez `ollama signin` gerekir.

## Hesap bilgileri de taşınır

Ajan token'ları (`tools/ai-cli/home/…`), Juggler kimliği
(`juggler-profile/home/credentials.json`) ve ollama özel anahtarı
(`tools/ollama/home/.ollama/id_ed25519`) klasörün içindedir; yeni makinede
yeniden giriş yapmanız gerekmez. **Bunun sonucu:** arşivi başkasına verirseniz
hesaplarınızı da vermiş olursunuz. Paylaşacaksanız önce bu dosyaları silin
(sonra ilgili ajanda bir kez giriş yapılır).

## İnternet gerekiyor mu?

Hayır — açılış, ajanlar ve panel çevrimdışı çalışır. İnternet yalnız iki şey
için gerekir: bulut modelleri (`*-cloud`, hesap gerektirir) ve güncelleme
denetimi. İkisi de yoksa açılış yine tamamlanır, sadece o adımlar sessizce atlanır.

## Bilinen riskler (yeni makinede)

Bunlar ATLAS'ın hatası değil, Windows'un davranışıdır — ama taşırken canınızı
yakabilir:

1. **Uzun yol (260 karakter).** `node_modules` ağacı derindir. Arşivi
   `C:\ATLAS` gibi KISA bir yere açın; `C:\Users\...\Downloads\yeni\ATLAS-son\`
   gibi derin bir yer açarken dosyaları sessizce eksik bırakabilir.
   `BASLAT.cmd` bunu `path.length` satırında uyarır.
2. **Mark-of-the-Web / SmartScreen.** Arşivi internetten veya e-postayla
   aldıysanız Windows içindeki `.exe`leri "engellenmiş" işaretler ve ilk
   çalıştırmada uyarı çıkar. Açmadan önce: arşive sağ tık → Özellikler →
   **Engellemeyi kaldır** (Unblock). USB/yerel ağ ile taşırsanız bu olmaz.
3. **Antivirüs.** Ajan ikilileri imzasızdır; kurumsal antivirüs karantinaya
   alabilir. `BASLAT.cmd` eksik ikiliyi söyler, sessizce yutmaz.
4. **Mimari.** Paketteki ikililer **x64**; Windows on ARM makinede çalışmaz.

## Bir şey ters giderse

- `BASLAT.cmd --force-relocate` — uyarlamayı zorla tekrarlar.
- `DOCTOR.cmd` — 9 adımlı sağlık taraması; her bulguda kanıt, kök neden, çözüm
  ve çoğunda tek tıklık düzeltme.
- `python -m tools.portable.vendor` — node/git kopyaları eksikse yeniden indirir
  (internet gerekir).
