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

Boyut: klasör bugün **~5,7 GB** (ölçüldü). `PAKETLE.cmd --yagsiz` yeniden
indirilebilir kurulum arşivlerini ve derleme önbelleklerini atar (~271 MB;
`tools/.cache`). Daha fazlasını atmak isterseniz en büyük kalem
`tools/ollama/lib` (1,8 GB GPU çalıştırıcıları) — yalnız YEREL model
çalıştıracaksanız gerekir, bulut modelleriyle çalışırken gereksizdir.

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

## Hesap bilgileri de taşınır

Ajan token'ları (`tools/ai-cli/home/…`) ve Juggler kimliği
(`juggler-profile/home/credentials.json`) klasörün içindedir; yeni makinede
yeniden giriş yapmanız gerekmez. **Bunun sonucu:** arşivi başkasına verirseniz
hesaplarınızı da vermiş olursunuz. Paylaşacaksanız önce bu dosyaları silin
(sonra ilgili ajanda bir kez giriş yapılır).

## İnternet gerekiyor mu?

Hayır — açılış, ajanlar ve panel çevrimdışı çalışır. İnternet yalnız iki şey
için gerekir: bulut modelleri (`*-cloud`, hesap gerektirir) ve güncelleme
denetimi. İkisi de yoksa açılış yine tamamlanır, sadece o adımlar sessizce atlanır.

## Bir şey ters giderse

- `BASLAT.cmd --force-relocate` — uyarlamayı zorla tekrarlar.
- `DOCTOR.cmd` — 9 adımlı sağlık taraması; her bulguda kanıt, kök neden, çözüm
  ve çoğunda tek tıklık düzeltme.
- `python -m tools.portable.vendor` — node/git kopyaları eksikse yeniden indirir
  (internet gerekir).
