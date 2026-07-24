"""GBrain: ATLAS'ın birleşik beyni.

Vault (notlar) + graf (ilişkiler) + günlük (zaman) tek arayüzde:
- remember(): yeni bilgiyi doğru yere, linkleriyle yazar
- recall():   anahtar kelime + graf-komşuluğu skorlamasıyla geri çağırır
- context_for(): bir görev/konu için çalışma bağlamı paketi üretir

Tasarım ilkesi: GBrain ayrı veri tutmaz — vault tek gerçek kaynaktır.
GBrain sadece OKUMA stratejisi ve YAZMA disiplinidir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from atlas_core.memory.vault import Vault

_WORD = re.compile(r"[\wçğıöşüÇĞİÖŞÜ]{3,}")

# Skor ağırlıkları: doğrudan eşleşme > başlık eşleşmesi > graf komşuluğu
W_BODY, W_TITLE, W_NEIGHBOR = 1.0, 3.0, 0.5


@dataclass(frozen=True, slots=True)
class Recall:
    """Tek geri çağırma sonucu."""

    name: str
    score: float
    snippet: str  # eşleşen ilk satır — hızlı gözden geçirme için


class GBrain:
    """Vault üzerinde birleşik hatırlama/geri çağırma arayüzü."""

    def __init__(self, vault_root: Path) -> None:
        self.vault = Vault(vault_root)

    # ---------- YAZMA DİSİPLİNİ ----------

    def remember(
        self,
        name: str,
        content: str,
        links: tuple[str, ...] = (),
        tags: tuple[str, ...] = (),
        folder: str = "entities",
    ) -> Path:
        """Bilgiyi vault'a, ilişkileri wikilink olarak gömerek yazar.

        Var olan nota yazılırsa içerik EKLENİR (üzerine yazılmaz) —
        hafıza silinmez, birikir.
        """
        link_line = " ".join(f"[[{ln}]]" for ln in links)
        tag_line = " ".join(f"#{t}" for t in tags)
        block = f"\n{content}\n{link_line} {tag_line}".rstrip() + "\n"
        try:
            self.vault.read(name, folder=folder)
            return self.vault.append(name, block, folder=folder)
        except Exception:
            return self.vault.write(name, f"# {name}\n{block}", folder=folder)

    def log_event(self, entry: str) -> Path:
        """Zaman eksenli hafıza: bugünün günlük notuna kayıt düşer."""
        return self.vault.daily(entry)

    # ---------- OKUMA STRATEJİSİ ----------

    def recall(self, query: str, limit: int = 5) -> list[Recall]:
        """Anahtar kelime + graf komşuluğu skorlamasıyla geri çağırma.

        1. Sorgu kelimeleri not gövdesi/başlığında aranır (birincil skor).
        2. Eşleşen notların graf komşuları küçük skorla dahil edilir —
           doğrudan geçmese de İLİŞKİLİ bilgi yüzeye çıkar.
        """
        words = {w.lower() for w in _WORD.findall(query)}
        if not words:
            return []
        g = self.vault.graph()
        scores: dict[str, float] = {}
        snippets: dict[str, str] = {}

        for name, note in g.nodes.items():
            text = note.path.read_text(encoding="utf-8")
            low = text.lower()
            s = sum(W_BODY * low.count(w) for w in words)
            s += sum(W_TITLE for w in words if w in name.lower())
            if s > 0:
                scores[name] = s
                for line in text.splitlines():
                    if any(w in line.lower() for w in words):
                        snippets[name] = line.strip()[:120]
                        break

        for name in list(scores):
            for nb in g.neighbors(name):
                if nb not in scores:
                    scores[nb] = 0.0
                    snippets.setdefault(nb, "(graf komşusu)")
                scores[nb] += W_NEIGHBOR

        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [
            Recall(name=n, score=round(s, 2), snippet=snippets.get(n, ""))
            for n, s in ranked[:limit]
        ]

    def context_for(self, topic: str, limit: int = 5) -> str:
        """Bir görev için hazır bağlam paketi (prompt'a eklenecek metin).

        Görev başlarken çağrılır: ilgili notların özeti tek blokta döner —
        ajan geçmişi 'hatırlayarak' başlar.
        """
        hits = self.recall(topic, limit=limit)
        if not hits:
            return f"(GBrain: '{topic}' için kayıtlı bağlam yok)"
        lines = [f"## GBrain bağlamı: {topic}"]
        for h in hits:
            lines.append(f"- [[{h.name}]] (skor {h.score}): {h.snippet}")
        return "\n".join(lines)
