# 037 — İhtiyaç: `atlas ai-cli diff-summary` (auto-update commit disiplin)

## Bağlam
17. tur bulgu (`790c9da`): auto-update sonrası `tools/ai-cli/
package-lock.json` değiştiğinde ben elle commit atarken mesajı
gerçek diff ile senkron yazmayı unutabildim (mesaj "opencode 1.18.9"
diyordu, gerçek diff cline bump'ıydı).

Auto-update mekanizması (`tools/portable/autoupdate.py`) commit
üretmez — sadece `npm install/update` çalıştırır. Kullanıcı sonradan
elle commit atar. Bu sırada **hangi paket bump edildi doğrulamak**
manuel iş; `git diff` bakmayı unutunca mesaj yanlış olur.

Çözüm: `atlas ai-cli diff-summary` alt-komutu — `tools/ai-cli/
package-lock.json` git diff'ini parse eder, hangi paketin sürümü
değişti tek satırlık özet basar. Kullanıcı bunu commit mesajı olarak
kullanır (`git commit -m "$(atlas ai-cli diff-summary)"`).

## İhtiyaç (tek cümle)
`atlas ai-cli diff-summary` `tools/ai-cli/package-lock.json`'un git
staged/working diff'ini parse etsin ve `chore(ai-cli): opencode-ai
1.18.8 → 1.18.9` gibi öneri commit mesajı bassın.

## Ölçülebilir Başarı
- **M1 — Yeni alt-komut:** `atlas ai-cli diff-summary` — `ai-cli`
  alt-komut grubu (`ai-cli sub`), `diff-summary` içi. Gelecekte
  `ai-cli update` / `ai-cli list` gibi eklenebilir.
- **M2 — Git diff:** `git diff --unified=0 tools/ai-cli/
  package-lock.json` çalıştırılır (staged + working — HEAD ile
  karşılaştırma). Subprocess `shell=False`, timeout 10 sn.
- **M3 — Parse:** `"version": "X.Y.Z"` satırlarının önündeki `-/+`
  işaretine bakılır; aynı paketin (bir üstteki `"name": "..."`
  satırı) eski + yeni sürümü toplar.
- **M4 — Çıktı formatı:**
  - Değişiklik yok: `(diff yok)` + exit 0.
  - Tek paket: `chore(ai-cli): opencode-ai 1.18.8 → 1.18.9` + exit 0.
  - Birden çok paket: `chore(ai-cli): opencode-ai 1.18.8→1.18.9;
    cline 3.0.46→3.0.47` (noktalı virgülle ayrılmış).
- **M5 — Fail-safe:** `git` yoksa / repo değil / dosya yok →
  `(diff okunamadı: <sebep>)` + exit 0 (uyarı, hata değil; commit
  mesajını kullanıcı elle yazar).
- **M6 — Test:** +5 test — diff yok, tek paket, birden fazla paket,
  git yok fail-safe, monkeypatch fake diff çıktısı.
- **M7 — DECISIONS:** [KARAR] neden ayrı komut (`atlas commit-msg`
  yerine `ai-cli diff-summary`); neden `→` (unicode ok işareti,
  git commit mesajlarında güzel); neden `chore(ai-cli):` prefix
  (auto-update kalıbı).

## Kapsam DIŞI
- Otomatik commit atma — kullanıcı elle `git commit`.
- `opencode/cline/kilo/kimi` dışındaki paketler — bunlar sabit
  liste.
- YAML/JSON çıktı — düz metin (commit mesajı bir string).
- Interaktif seçim — YAGNI.

## Kısıt
- Yeni CLI komutu (`ai-cli` alt-grubu) mevcut komutları etkilemez.
- Yeni env DEĞİL, yeni exit kodu YOK.
- Git subprocess yok/patlarsa fail-safe (uyarı + exit 0).
- Türkçe uyarı; commit mesaj İngilizce (git commit sözleşmesi).
