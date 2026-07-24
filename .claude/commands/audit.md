Depoda öz-denetim turu yap, hiçbir şeyi sormadan düzeltme —
önce raporla:
1. `ruff check .` ve `pytest -q` çıktıları.
2. Sır taraması: grep ile API key/şifre kalıpları ara.
3. Sayısal modüllerde birim tutarlılığı kontrolü.
4. requirements.txt vs gerçek importlar farkı.
5. Bulguları önem sırasıyla listele; düzeltme için onay iste.
