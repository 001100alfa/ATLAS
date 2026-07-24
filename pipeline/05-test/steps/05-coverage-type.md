# 05 — Kapsam ve Tip  `/coverage-type`

**Amaç:** coverage>=90 + mypy strict + ruff kapılarını koşmak.

| | |
|---|---|
| **Girdi** | Tam test seti |
| **Çıktı** | Sayısal kapı çıktıları |

## Prosedür
1. pytest --cov, mypy --strict, ruff check koş, çıktıyı kaydet.
2. Kapsanmayan satırları incele: ölü kod mu, test eksiği mi?
3. Kapı altında kalan değer = aşama bitmez.

## Kapıya Katkısı
Gate: coverage/mypy şartı sağlanır.
