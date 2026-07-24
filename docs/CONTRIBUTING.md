# Katkı Kuralları

## Yerel geliştirme (uv)
Paket yöneticisi **uv**, Python **3.12**. Ortamı kur, kapıları çalıştır:
```bash
uv sync --extra dev          # .venv (3.12) + dev bağımlılıkları
uv run ruff check src tests  # lint
uv run mypy src              # tip (strict)
uv run pytest                # test
```
uv yoksa `pip install -e ".[dev]"` (Python 3.12'lik bir venv içinde).

## Kurallar
- Branch: `feat/issue-N` veya `fix/issue-N`; main'e doğrudan commit yok.
- Her PR: test zorunlu; sayısal kod referans değerle doğrulanır,
  referansın kaynağı (el hesabı/katalog/standart) test docstring'ine yazılır.
- Birimler: SI-mm iç sistem; dönüşüm sadece fonksiyon sınırında.
- Kalite kapıları (CI'da zorunlu): ruff temiz, mypy --strict temiz,
  pytest yeşil, coverage düşüşü yok.
- Commit mesajı Türkçe kısa özet; gövdede gerekçe.
