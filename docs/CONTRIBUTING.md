# Katkı Kuralları

- Branch: `feat/issue-N` veya `fix/issue-N`; main'e doğrudan commit yok.
- Her PR: test zorunlu; sayısal kod referans değerle doğrulanır,
  referansın kaynağı (el hesabı/katalog/standart) test docstring'ine yazılır.
- Birimler: SI-mm iç sistem; dönüşüm sadece fonksiyon sınırında.
- Kalite kapıları (CI'da zorunlu): ruff temiz, mypy --strict temiz,
  pytest yeşil, coverage düşüşü yok.
- Commit mesajı Türkçe kısa özet; gövdede gerekçe.
