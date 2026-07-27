# Kurulum Sihirbazı (GUI)

Yeni bir kullanıcının ATLAS'ı denemek için tek yapması gereken:

```
SETUP.cmd   ← çift tıklayın
```

Tarayıcıda adım adım bir kurulum ekranı açılır. **Önceden hiçbir şey kurmanız
gerekmez** — sihirbaz depoya gömülü Python ile çalışır.

## Akış

| Adım | Ne yapar |
|---|---|
| 1. Kontrol | Python / Node / npm / çekirdek durumunu gösterir; eksikse ne olacağını açıklar |
| 2. ATLAS kur | `setup-portable.cmd` (çevrimdışı, `vendor/wheels`'ten) — canlı log |
| 3. AI CLI kur | `setup-ai-cli.cmd` (npm + pip + goose ikilisi) — internet gerekir |
| 4. Yerel AI | Çalışan bir Ollama var mı; varsa anahtarsız ajanlar için kullanılır |
| 5. Ajanları bağla | **Asıl ekran** — her ajanı gerçekten sınar, sorunları tek tıkla çözer |
| 6. Bitti | Özet + **▶ Projeyi Çalıştır** |

Adımlar atlanabilir; sihirbaz her açılışta gerçek durumu yeniden tespit eder,
yani yarım kalan kurulumu kaldığı yerden sürdürebilirsiniz.

## 5. adım neden önemli

"Kurulu" olmak, ajanın panelde çalışacağı anlamına gelmez. Sihirbaz her ajan için
Juggler'ın yaptığı **gerçek ACP el sıkışmasını** yapar (`initialize` +
`session/new`, kabuksuz spawn) ve sonucu dürüstçe gösterir:

| Rozet | Anlamı | Tek tıkla çözüm |
|---|---|---|
| ✓ Hazır | Panelde çalışır | — |
| Giriş gerekli | Ajan hesap kimliği istiyor | **Giriş yap** |
| Model gerekli | Sağlayıcı ayarlı değil | **Yerel modele bağla** |
| Kurulu değil | İkili yok | 3. adıma dönün |

**Giriş yap** düğmesi kimlik bilgisi işlemez; yalnız doğru komutu sizin adınıza
başlatır:
- **Cline** — cihaz-kodu akışı: sihirbaz URL'yi ve kodu ekranda gösterir, siz
  tarayıcıda giriş yaparsınız, sihirbaz tamamlanmasını bekleyip yeniden sınar.
- **Diğerleri** — kendi giriş komutu gerçek bir konsol penceresinde açılır.

Parola/kod her zaman sizde kalır; sihirbaz hiçbir kimlik bilgisini görmez veya saklamaz.

## Anahtarsız (hesapsız) kullanım

### Yerel modeli sihirbaz indirsin (4. adım)
Bilgisayarınızda hiç yerel model yoksa **"İndir ve kur"** düğmesi her şeyi yapar:

- Resmi Ollama arşivini indirir (**~1,4 GB**) — *yönetici hakkı gerekmez, sisteme
  kurulum yapılmaz*; her şey `tools/ollama/` altına iner ve proje klasörüyle taşınır.
- `127.0.0.1:11435`'te sunucuyu başlatır — sistemde kurulu bir Ollama varsa onun
  `11434` portuna dokunmaz.
- Seçtiğiniz modeli proje-yerel depoya indirir:

| Model | Boyut | Uygun |
|---|---|---|
| `llama3.2:1b` | ~1,3 GB | En hızlı, en az yer |
| `llama3.2:3b` | ~2 GB | Dengeli (varsayılan) |
| `qwen2.5-coder:7b` | ~4,7 GB | Kod için en iyi |

İndirme yüzde, hız ve tahmini kalan süreyle canlı gösterilir; yavaş bağlantıda
uzun sürer. Yarım kalırsa düğmeye tekrar basmak yeterlidir (yarım dosya bırakmaz).
Kurulu ama kapalıysa 4. adımda **"Sunucuyu başlat"** düğmesi çıkar.

Elle kurmayı tercih ederseniz [ollama.com](https://ollama.com/download) da olur;
sihirbaz onu da bulur.

### Bağlama
Bilgisayarınızda çalışan bir Ollama varsa **Goose**
hesap açmadan kullanılabilir. "Yerel modele bağla" düğmesi:
- çalışan Ollama'yı bulur (önce `127.0.0.1:11435`, sonra `11434`),
- sunucudaki modelleri sorup araç kullanımına uygun olanı seçer,
- `GOOSE_PROVIDER` / `GOOSE_MODEL` / `OLLAMA_HOST` değerlerini ajanın
  `acp.json` kaydına yazar (sarmalayıcı script gerekmez — Juggler config env'ini
  üst süreç env'inin üstüne bindirir).

**Kimi anahtarsız çalışmaz:** ATLAS'ın pip `kimi-cli` paketi ACP'de
`_check_auth()`'u koşulsuz çağırır — Kimi hesabı şarttır (ölçüldü:
`kimi_cli/acp/server.py`). Yerel model ayarı yalnız doğrudan `kimi` kullanımında
geçerlidir. **Cline** de ACP'de yalnız bulut girişini kabul eder.

## Kayıt ve sarmalayıcılar

**"ATLAS'a bağla"** iki iş yapar:

1. `tools/agents/<ajan>.cmd` sarmalayıcılarını üretir,
2. `<proje>/.juggler/acp.json`'a bu sarmalayıcıları yazar (Juggler proje kaydını
   global kaydın üstüne alır).

Ajanı doğrudan çağırmak yerine ince bir `.cmd` üzerinden çağırmak üç sorunu çözer:

| Sorun | Sarmalayıcı çözümü |
|---|---|
| Ortam ayarı `acp.json`'a gömülüydü, değiştirmek için kaydı yeniden yazmak gerekiyordu | Ortam tek bir okunur `.cmd`'de toplandı |
| **goose ayarlarını kullanıcının gerçek `%APPDATA%\Block\goose` dizinine yazıyordu** (ölçüldü — goose Windows'ta XDG'yi yok sayar, kökünü `%APPDATA%`'dan çözer) | Sarmalayıcı `APPDATA`'yı da proje içine çevirir |
| Yerel model sunucusu kapalıysa (ör. makine yeniden başladı) goose sessizce başarısız oluyordu | Sarmalayıcı önce `ensure-ollama.cmd` çağırır; sunucu gerekiyorsa kendiliğinden kalkar |

Üretilen dosyalar:

```
tools/agents/ensure-ollama.cmd   yerel model sunucusunu gerekiyorsa başlatır
tools/agents/local-model.cmd     seçtiğiniz model (sihirbaz yazar)
tools/agents/<ajan>.cmd          ajan başına ortam + çalıştırma
```

Sarmalayıcılar **saf ASCII + CRLF**'tir (cmd.exe konsol kod sayfasında Türkçe
karakterleri bozar) ve üretilmiş dosyalardır — elle düzenlemeyin, sihirbaz
yeniden üretir. Eski davranışı isteyenler için `register_agents(use_wrappers=False)`
ortamı doğrudan kayda gömer.

## Birden fazla kurulum

Aynı makinede birden fazla kurulum olabilir (ör. ATLAS'ın kendi `tools/ai-cli`'si
ve ayrı bir Juggler deposunun `.toolchain`'i). Panel her ajan için **tek** bir
kaynağı çalıştırır, bu yüzden sihirbaz 5. adımda:

- tespit ettiği tüm kurulumları listeler,
- her ajan kartında **hangi kurulumdan geldiğini** gösterir (ATLAS dışı kaynak
  vurgulanır),
- "ATLAS'a bağla" ile ATLAS sürümüne geçirir.

Diğer kurulum **silinmez**, dokunulmadan durur; proje kaydı global kaydı ezdiği
için ATLAS sürümü devreye girer. Geri dönmek isterseniz proje
`.juggler/acp.json`'ından ilgili girdiyi silmek yeterlidir.

## Projeyi çalıştırma (6. adım)

Kurulum bitince **▶ Projeyi Çalıştır** düğmesi projeyi doğrudan açar. Sihirbaz
neyin gerçekten kullanılabilir olduğuna bakar ve en uygun yolu öne alır:

| Seçenek | Gereken | Açıklama |
|---|---|---|
| Masaüstü paneli | `tools/juggler/juggler.exe` + `juggler-app.exe` | Ayrı pencere, tarayıcı gerekmez |
| Web arayüzü | `tools/juggler/juggler.exe` | Sunucu başlar, adres konsolda yazar |
| Komut satırı | `atlas-shell.cmd` | Komut yazabileceğiniz açık konsol |

Panel ikilileri depoda tutulmaz (AGPL + büyük; `docs/JUGGLER.md`'ye göre kaynaktan
üretilir). Yoksa düğme bunu **söyler** ve komut satırı seçeneğini önerir — sessizce
başarısız olmaz.

Güvenlik: arayüzden gelen hedef adı doğrudan çalıştırılmaz; yalnız
`detect.LAUNCHERS` beyaz listesindeki betiğe eşlenir (yol geçişi ve rastgele
komut reddedilir, testle sabitlenmiştir).

**Neden `atlas.cmd` değil:** `atlas.cmd` argparse ile alt komut bekler
(`atlas scan …`). Argümansız çağrılırsa kullanım hatası basıp **anında kapanır** —
kullanıcıya "CLI çalışmıyor" gibi görünür. Bu yüzden CLI hedefi
`atlas-shell.cmd`'dir: projeyi PATH'e ekler, UTF-8 kod sayfasına geçer
(mm² / mm⁴ çıktısı için), komut örneklerini yazar ve `cmd /k` ile **açık kalır**.
Bu tuzak `tests/test_setup_gui.py` ile sabitlendi.

## Teknik notlar

- `tools/setup_gui/` — `detect.py` (durum + kaynak sınıflandırma), `acp_probe.py`
  (gerçek test), `connect.py` (kayıt/anahtarsız/kimlik), `wrappers.py`
  (`tools/agents/*.cmd` üretimi), `install_ollama.py` (taşınabilir yerel model
  sunucusu), `server.py` (yerel HTTP), `ui.html` (arayüz).
- Test, spec'ten değil **kayıtlı `acp.json` girdisinden** çalışır
  (`acp_probe.effective_entry`) — yani panelin gerçekten çalıştıracağı şeyi sınar.
- Ollama sürümü `install_ollama.py` içinde sabitlenir (`OLLAMA_VERSION`); model
  adları argv'ye doğrudan gider, bu yüzden dar bir kalıpla (`MODEL_RE`) doğrulanır.
- Yalnız **stdlib**; ek bağımlılık yok. Sunucu yalnız `127.0.0.1`'e bağlanır ve
  her istek oturum jetonu ister (adres çubuğundaki `?t=…`), böylece makinedeki
  başka bir uygulama arayüzü süremez.
- Ajan yolları `tools/gen-acp-config.js` ile aynıdır; parite
  `tests/test_setup_gui.py::test_parity_with_js_generator` ile sabitlenir.
- Komut satırını tercih edenler için eski akış aynen çalışır:
  `setup-portable.cmd` → `setup-ai-cli.cmd` → `setup-acp-agents.cmd`.
