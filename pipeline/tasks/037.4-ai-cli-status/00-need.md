# Görev 037.4 — İhtiyaç

037/037.1/037.2/037.3 dört komutu tamamladı: `diff-summary`, `update`,
`list`, `exec`. Ama kullanıcı bir paket için `exec --version` çalıştırmadan
şu üç şeyi öğrenemez:
- kurulu sürüm nedir, package.json'da beklenen nedir, uyuşuyor mu?
- diskte ne kadar yer kaplıyor?
- bin çözünürlüğü hangi shim'e düşüyor (Windows `.cmd` mi, Unix çıplak mı)?

Bu sorular ayrı ayrı `list --json | jq`, `du`, `ls .bin/` gerektiriyor.

## Kabul kriteri

- `atlas ai-cli status <name> [--json]`
- JSON şeması:
  ```json
  {
    "name": "opencode-ai",
    "installed_version": "1.18.9",
    "declared_version": "^1.18.9",
    "up_to_date": true,
    "install_dir": "tools/ai-cli/node_modules/opencode-ai",
    "size_bytes": 1234567,
    "size_human": "1.2 MB",
    "bin_path": "tools/ai-cli/node_modules/.bin/opencode.cmd"
  }
  ```
- İnsan çıktısı: 6-7 satır insanca okunur — sürüm/güncel mi/boyut/bin.
- Exit kodları:
  - 0: paket kurulu (rapor içinde `up_to_date` bilgisi)
  - 2: `tools/ai-cli/` yok VEYA paket dependencies'te yok VEYA kurulu değil
    → SPEC HATASI + kullanıcıya `atlas ai-cli list` veya `update` önerisi
- Exec çalıştırılmaz — sürüm bilgisi `node_modules/<name>/package.json`
  version alanından okunur (037.2 mevcut yardımcı `_read_installed_version`).
- Boyut: `node_modules/<name>/**/*` toplam byte (symlink izlenmez, OSError skip).

## Riskli

- `up_to_date` semver-lite: declared'daki `^`, `~`, `>=`, boşluk sıyırılıp
  installed ile string eşitliği kontrol edilir. `^1.18.9` + installed
  `1.18.10` → `False` gösterir (aslında semver-uyumlu). Bu SPEC'te
  kasıtlı — kullanıcının niyeti "kurulu tam beklenen mi" değil, "aynı
  sürüm mü". Gerçek semver çözümü için ayrı komut (`atlas ai-cli list`
  zaten beklenen vs kurulu karşılaştırıyor).
- Boyut hesabı büyük paketlerde (100k+ dosya) yavaşlar. Ölçüm yapılıp
  gerekirse gelecekte `os.scandir`'a düşülür (YAGNI).
