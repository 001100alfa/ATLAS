"""GBrain SQLite-FTS5 indeksi — vault'a önbellek katmanı.

Vault gerçek kaynak; bu modül yalnız arama hızı için indeks tutar.
- ensure_fresh(): partial reindex (mtime + sha256)
- rebuild(): tam yeniden kurulum
- upsert(): tek notu yazar (remember yolunda)
- search(): bm25 + snippet döner
- is_fts_available(): sqlite/fts5 kontrolü — yoksa GBrain fallback'e düşer
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from atlas_core.memory.vault import Vault

SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class IndexStats:
    indexed: int
    skipped: int
    removed: int
    elapsed_s: float


class GBrainIndex:
    """SQLite FTS5 tabanlı GBrain önbelleği."""

    def __init__(self, vault: Vault, db_path: Path) -> None:
        self.vault = vault
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._fts_checked = False
        self._fts_ok = False

    # ---------- bağlantı ----------

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._ensure_schema(self._conn)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5(
                name UNINDEXED, body,
                tokenize='unicode61 remove_diacritics 2'
            );
            CREATE TABLE IF NOT EXISTS meta(
                name TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS state(k TEXT PRIMARY KEY, v TEXT NOT NULL);
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO state(k,v) VALUES('schema_version', ?)",
            (SCHEMA_VERSION,),
        )
        conn.commit()

    def is_fts_available(self) -> bool:
        """SQLite FTS5 kullanılabilir mi (yoksa GBrain fallback'e düşer)."""
        if self._fts_checked:
            return self._fts_ok
        self._fts_checked = True
        try:
            probe = sqlite3.connect(":memory:")
            probe.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
            probe.close()
            self._fts_ok = True
        except sqlite3.OperationalError:
            self._fts_ok = False
        return self._fts_ok

    # ---------- reindex ----------

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def ensure_fresh(self) -> IndexStats:
        """Partial reindex: yalnız değişen/yeni/silinen notları dokunur."""
        t0 = time.perf_counter()
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT name, mtime_ns, sha256 FROM meta")
        meta = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

        indexed = skipped = removed = 0
        current: set[str] = set()

        for p in sorted(self.vault.root.rglob("*.md")):
            name = p.stem
            current.add(name)
            mtime_ns = p.stat().st_mtime_ns
            prev = meta.get(name)
            if prev is not None and prev[0] == mtime_ns:
                skipped += 1
                continue
            text = p.read_text(encoding="utf-8")
            digest = self._hash(text)
            if prev is not None and prev[1] == digest:
                # İçerik aynı ama mtime kaymış; meta güncelle, FTS'e dokunma.
                cur.execute(
                    "UPDATE meta SET mtime_ns=? WHERE name=?", (mtime_ns, name)
                )
                skipped += 1
                continue
            self._upsert_row(cur, name, p, mtime_ns, digest, text)
            indexed += 1

        stale = set(meta) - current
        for name in stale:
            cur.execute("DELETE FROM notes WHERE name=?", (name,))
            cur.execute("DELETE FROM meta WHERE name=?", (name,))
            removed += 1

        conn.commit()
        return IndexStats(indexed, skipped, removed, time.perf_counter() - t0)

    def rebuild(self) -> IndexStats:
        """Tam yeniden kurulum: mevcut indeks silinir, sıfırdan kurulur."""
        conn = self._connect()
        conn.execute("DELETE FROM notes")
        conn.execute("DELETE FROM meta")
        conn.commit()
        return self.ensure_fresh()

    def upsert(self, name: str) -> None:
        """Tek notu yazma yolunda deterministik olarak indeksler."""
        for p in self.vault.root.rglob(f"{name}.md"):
            text = p.read_text(encoding="utf-8")
            conn = self._connect()
            cur = conn.cursor()
            self._upsert_row(
                cur, p.stem, p, p.stat().st_mtime_ns, self._hash(text), text
            )
            conn.commit()
            return

    @staticmethod
    def _upsert_row(
        cur: sqlite3.Cursor, name: str, p: Path, mtime_ns: int, digest: str, text: str
    ) -> None:
        cur.execute("DELETE FROM notes WHERE name=?", (name,))
        cur.execute("INSERT INTO notes(name, body) VALUES(?, ?)", (name, text))
        cur.execute(
            "INSERT INTO meta(name, path, mtime_ns, sha256) VALUES(?,?,?,?)"
            " ON CONFLICT(name) DO UPDATE SET path=excluded.path,"
            " mtime_ns=excluded.mtime_ns, sha256=excluded.sha256",
            (name, str(p), mtime_ns, digest),
        )

    # ---------- arama ----------

    def search(self, query: str, limit: int = 5) -> list[tuple[str, float, str]]:
        """FTS bm25 + snippet döner. Query güvenliği: MATCH ' " ' quote."""
        conn = self._connect()
        cur = conn.cursor()
        safe_query = self._sanitize_query(query)
        if not safe_query:
            return []
        try:
            cur.execute(
                "SELECT name, bm25(notes), snippet(notes, 1, '', '', ' ... ', 20) "
                "FROM notes WHERE notes MATCH ? "
                "ORDER BY bm25(notes) LIMIT ?",
                (safe_query, limit),
            )
        except sqlite3.OperationalError:
            return []
        rows = cur.fetchall()
        # bm25 küçük = iyi. 1/(1+bm25) ile 0..1 aralığına normalize.
        return [
            (name, 1.0 / (1.0 + float(rank)), snippet)
            for name, rank, snippet in rows
        ]

    @staticmethod
    def _sanitize_query(q: str) -> str:
        """Kullanıcı sorgusundan FTS operatörlerini temizler + tırnaklar."""
        cleaned = "".join(c if c.isalnum() or c in " çğıöşüÇĞİÖŞÜ-" else " " for c in q)
        tokens = [t for t in cleaned.split() if len(t) >= 2]
        if not tokens:
            return ""
        return " ".join(f'"{t}"' for t in tokens)
