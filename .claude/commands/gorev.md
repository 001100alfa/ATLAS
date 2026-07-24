GitHub issue numarası: $ARGUMENTS
1. `gh issue view $ARGUMENTS` ile görevi oku.
2. skills/ altında konuyla ilgili SKILL.md var mı bak, varsa oku.
3. `git checkout -b feat/issue-$ARGUMENTS`
4. CLAUDE.md Zorunlu Döngü'yü uygula.
5. tester subagent'ını çalıştır; kırmızı test varsa düzelt.
6. reviewer subagent'ını çalıştır; kritik bulguları düzelt.
7. `gh pr create --fill --body "Closes #$ARGUMENTS"` ile PR aç.
8. DECISIONS.md'ye görev özetini ekle, commit'e dahil et.
