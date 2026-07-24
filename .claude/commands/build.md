Görev no: $ARGUMENTS
1. SPEC-XXX Durum: ONAYLI mı kontrol et; değilse DUR.
2. 03-plan TEMPLATE ile PLAN-XXX.md üret (en riskli WP ilk).
3. feat/task-XXX branch aç; WP'leri sırayla kodla,
   her WP = commit, BUILD-XXX.log.md'yi güncelle.
4. 05-test: FR<->test tablosuyla testleri yaz, tester subagent koştur,
   TEST-XXX.md raporla. Coverage>=90 + mypy strict şart.
5. 06-revise: reviewer subagent koştur, K/M bulguları düzelt,
   REVIEW-XXX.md doldur.
6. Bitince "/finish XXX ile sadeleştirme+teslime geç" de.
