# 05-test alt-beceri zinciri

01. **Referans Doğrulama** `/ref-test` — Her FR'yi kaynaklı referans değerle test etmek.
02. **Kenar Avcısı** `/edge-hunt` — Sıfır, negatif, sınır, taşma senaryolarını taramak.
03. **Hata Sözleşmesi** `/error-contract` — Doğru exception + doğru mesaj garantisi.
04. **Fizik Invariantları** `/invariants` — Alan bilgisinden gelen değişmezleri test etmek.
05. **Kapsam ve Tip** `/coverage-type` — coverage>=90 + mypy strict + ruff kapılarını koşmak.
06. **İzlenebilirlik Matrisi** `/trace` — FR <-> test eşlemesini kanıtlamak + tester subagent koşusu.
