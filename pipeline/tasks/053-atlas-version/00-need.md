# Görev 053 — İhtiyaç

`atlas` root komutuna sürüm bilgisi bayrağı yok. Kullanıcı hangi build'i
çalıştırdığını anlayamıyor; issue bildiriminde "hangi sürüm" sorusu
manuel `pip show atlas` / `pyproject.toml` okumaya kalıyor.

## Kabul kriteri

- `atlas --version` (uzun) ve `atlas -V` (kısa) → `atlas <VERSION>` +
  exit 0.
- `<VERSION>` = `atlas_core.__version__` (paket sabiti; wheel/pip/portable
  kurulumların hepsinde çalışır).
- Alt-komut required=True olsa da `--version` argparse `action="version"`
  ile early exit; alt-komut gerektirmez.
- `atlas --help` çıktısında `--version` bayrağı listelenir.
- Drift kontrolü: `atlas_core.__version__` `pyproject.toml`'daki version
  ile bit-uyumlu — test zorlar (gelecekte drift ederse test kırılır).

## Riskli

- Bu bayrak subparsers yapısıyla çakışmaz çünkü argparse `--version`
  action'ı parse öncesi tetiklenir (kanıt: `--help` de aynı şekilde
  çalışıyor).
- Test `SystemExit` yakalayarak yapılır (argparse'ın early exit yolu).
