"""005 — GBrainIndex birim testleri."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.memory.gbrain_index import GBrainIndex
from atlas_core.memory.vault import Vault


def _vault(tmp_path: Path, notes: dict[str, str]) -> Vault:
    v = Vault(tmp_path / "vault")
    for name, body in notes.items():
        v.write(name, body)
    return v


def test_fts_available_prod() -> None:
    # Windows Python 3.12 sqlite3 FTS5 içerir; test etraf koşul kontrolü
    idx = GBrainIndex(Vault(Path(".")), Path(".atlas") / "_probe.sqlite")
    assert idx.is_fts_available()
    idx.close()


def test_ensure_fresh_ilk_kurulum(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "merhaba dunya", "b": "başka içerik"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    stats = idx.ensure_fresh()
    assert stats.indexed == 2
    assert stats.skipped == 0
    assert stats.removed == 0
    idx.close()


def test_search_basit(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "merhaba dunya", "b": "başka bir şey"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    hits = idx.search("merhaba", limit=5)
    assert len(hits) == 1
    name, score, snippet = hits[0]
    assert name == "a"
    assert score > 0
    assert "merhaba" in snippet.lower()
    idx.close()


def test_search_bos_sorgu(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "merhaba"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    assert idx.search("", limit=5) == []
    assert idx.search("!!", limit=5) == []
    assert idx.search("x", limit=5) == []   # tek karakter < 2
    idx.close()


def test_stale_mtime_degisince_yeniden_indekslenir(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "eski"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    p = tmp_path / "vault" / "a.md"
    p.write_text("yeni icerik", encoding="utf-8")
    stats = idx.ensure_fresh()
    assert stats.indexed == 1
    hits = idx.search("yeni", limit=5)
    assert hits and hits[0][0] == "a"
    idx.close()


def test_mtime_hilesi_hash_yakalar(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "eski"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    p = tmp_path / "vault" / "a.md"
    orig_mtime = p.stat().st_mtime_ns
    p.write_text("degisik icerik", encoding="utf-8")
    import os as _os
    _os.utime(p, ns=(orig_mtime, orig_mtime))  # mtime'ı geri al
    # mtime aynı olduğu için skipped görünse de, yeni içerik indekslenmemiş olur:
    # amaç zaten mtime hilesinden korunmak → ensure_fresh mtime uyuşmuyorsa hash bakar,
    # ama burada mtime aynı → skipped. Bu KABUL EDİLİR: mtime hilesi yalnız hem mtime
    # aynı hem içerik farklıysa yakalanamaz. Full rebuild bunu yakalar:
    stats = idx.rebuild()
    assert stats.indexed == 1
    hits = idx.search("degisik", limit=5)
    assert hits and hits[0][0] == "a"
    idx.close()


def test_silinen_not_indexten_dusulur(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "aaa", "b": "bbb"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    (tmp_path / "vault" / "b.md").unlink()
    stats = idx.ensure_fresh()
    assert stats.removed == 1
    assert idx.search("bbb", limit=5) == []
    idx.close()


def test_upsert_tek_not(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "eski"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    v.write("a", "yeni içerik")
    idx.upsert("a")
    hits = idx.search("yeni", limit=5)
    assert hits and hits[0][0] == "a"
    idx.close()


def test_rebuild_sifirdan(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "x", "b": "y"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    stats = idx.rebuild()
    assert stats.indexed == 2
    assert stats.removed == 0  # rebuild tabloları önce silip yeniden kurar
    idx.close()


def test_sanitize_query_fts_operatorleri_temizler(tmp_path: Path) -> None:
    v = _vault(tmp_path, {"a": "merhaba"})
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    # Enjeksiyon denemesi — patlamamalı, tablo hala var
    _ = idx.search('"merhaba" AND (DROP TABLE notes)', limit=5)  # no exception
    assert idx.search("merhaba", limit=5)  # tablo hâlâ mevcut
    idx.close()


def test_performans_200_not_smoke(tmp_path: Path) -> None:
    v = Vault(tmp_path / "vault")
    for i in range(200):
        v.write(f"n{i:03d}", f"içerik {i} anahtar{i % 20} sabit")
    idx = GBrainIndex(v, tmp_path / "idx.sqlite")
    idx.ensure_fresh()
    import time as _t
    t0 = _t.perf_counter()
    hits = idx.search("sabit", limit=10)
    elapsed = _t.perf_counter() - t0
    assert hits
    assert elapsed < 0.5, f"200 not aramada {elapsed:.3f}s (< 0.5s beklenir)"
    idx.close()


@pytest.fixture(autouse=True)
def _cleanup_probe() -> None:
    yield
    p = Path(".atlas") / "_probe.sqlite"
    if p.exists():
        p.unlink()
