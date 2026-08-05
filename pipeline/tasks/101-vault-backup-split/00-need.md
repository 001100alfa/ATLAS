# Görev 101 — İhtiyaç

SPEC 041 `vault backup` tek büyük `.tar.gz` üretir. GB'lık vault'lar
için cloud upload / e-posta / USB stick pratik değil. Parçalı yedek
(multi-volume) gerek.

## Kabul

- `atlas vault backup --split SIZE_MB [--out PATH]`.
- `SIZE_MB` int, `>= 1`. `<= 0` → SPEC HATASI exit 2.
- Backup normal akışta yazılır → `--split` ile fixed-size parçalara
  bölünür: `<name>.tar.gz.001`, `<name>.tar.gz.002`, ...
- Orjinal `.tar.gz` silinir (space tasarrufu; parçalardan birleştirme
  `cat *.tar.gz.* > full.tar.gz` mantığı).
- `--split` + `--encrypt`/`--recipient` → SPEC HATASI exit 2
  (encrypted split karmaşıklığı YAGNI; ayrı SPEC).
- `--out PATH` ile ORTOGONAL: PATH'e yazıldıktan sonra oradan parçalanır.
- Retention (`--keep N`) split'ten ÖNCE çalışır (parçalar dahil edilmez).
- `--split` VERİLMEZSE SPEC 041 BİT-UYUMLU.
