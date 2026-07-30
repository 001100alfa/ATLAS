"""SPEC 032 — atlas doctor --strict + DECISIONS drift denetimi."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from atlas_core import cli as cli_mod
from atlas_core.cli import (
    _check_decisions_drift,
    _last_decision_date,
    _read_strict_drift_days_env,
    main,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test ortamı temiz — env override, tmp dizinler."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_LLM", "stub")
    monkeypatch.delenv("ATLAS_STRICT_DRIFT_DAYS", raising=False)


# ─────────────────────────────────────────────────────────────────────
# _last_decision_date
# ─────────────────────────────────────────────────────────────────────


def test_032_last_date_yok_dosya(tmp_path: Path) -> None:
    """DECISIONS.md yoksa → None."""
    assert _last_decision_date(tmp_path / "yok.md") is None


def test_032_last_date_ilk_bulur(tmp_path: Path) -> None:
    """Dosyanın en üstteki `^## YYYY-MM-DD` başlığı alınır."""
    p = tmp_path / "d.md"
    p.write_text(
        "# ATLAS Karar Günlüğü\n\n"
        "## 2026-07-30 (X)\n- karar\n\n"
        "## 2026-07-29 (Y)\n- karar\n",
        encoding="utf-8",
    )
    assert _last_decision_date(p) == date(2026, 7, 30)


def test_032_last_date_bozuk_tarihi_atlar(tmp_path: Path) -> None:
    """Bozuk (mantık dışı) tarihe rağmen sonraki başlığa devam."""
    p = tmp_path / "d.md"
    p.write_text(
        "## 2026-13-45 (bozuk)\n"
        "## 2026-07-29 (sonraki)\n",
        encoding="utf-8",
    )
    assert _last_decision_date(p) == date(2026, 7, 29)


def test_032_last_date_bos_dosya(tmp_path: Path) -> None:
    """Tarih başlığı yoksa None."""
    p = tmp_path / "d.md"
    p.write_text("# Boş dosya\nsıradan yazı\n", encoding="utf-8")
    assert _last_decision_date(p) is None


# ─────────────────────────────────────────────────────────────────────
# _read_strict_drift_days_env
# ─────────────────────────────────────────────────────────────────────


def test_032_env_yok_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_STRICT_DRIFT_DAYS", raising=False)
    assert _read_strict_drift_days_env() == 7


def test_032_env_gecerli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_STRICT_DRIFT_DAYS", "14")
    assert _read_strict_drift_days_env() == 14


def test_032_env_parse_hata_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    for bad in ("abc", "-3", "0", "  "):
        monkeypatch.setenv("ATLAS_STRICT_DRIFT_DAYS", bad)
        assert _read_strict_drift_days_env() == 7, bad


# ─────────────────────────────────────────────────────────────────────
# _check_decisions_drift
# ─────────────────────────────────────────────────────────────────────


def _write_decisions(path: Path, iso_date: str) -> None:
    path.write_text(
        f"# ATLAS Karar Günlüğü\n\n## {iso_date} (test)\n- karar\n",
        encoding="utf-8",
    )


def test_032_drift_sifir_temiz(tmp_path: Path) -> None:
    """Aynı gün giriş varsa drift=0, uyarı yok."""
    p = tmp_path / "d.md"
    _write_decisions(p, "2026-07-30")
    r = _check_decisions_drift(p, today=date(2026, 7, 30))
    assert r["drift_days"] == 0
    assert r["warning"] is None
    assert r["last_date"] == "2026-07-30"
    assert r["threshold_days"] == 7


def test_032_drift_esikten_az_temiz(tmp_path: Path) -> None:
    """3 gün geçmişse (eşik 7) temiz."""
    p = tmp_path / "d.md"
    _write_decisions(p, "2026-07-27")
    r = _check_decisions_drift(p, today=date(2026, 7, 30))
    assert r["drift_days"] == 3
    assert r["warning"] is None


def test_032_drift_esik_asim_uyari(tmp_path: Path) -> None:
    """10 gün geçmişse (eşik 7) uyarı gövdesi dolar."""
    p = tmp_path / "d.md"
    _write_decisions(p, "2026-07-20")
    r = _check_decisions_drift(p, today=date(2026, 7, 30))
    assert r["drift_days"] == 10
    assert r["warning"] is not None
    assert "10 gün önce" in r["warning"]
    assert "eşik 7 gün" in r["warning"]


def test_032_drift_dosya_yok_uyari(tmp_path: Path) -> None:
    """DECISIONS yoksa uyarı."""
    r = _check_decisions_drift(tmp_path / "yok.md", today=date(2026, 7, 30))
    assert r["warning"] is not None
    assert "yok veya tarih parse edilemedi" in r["warning"]
    assert r["last_date"] is None


def test_032_drift_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ATLAS_STRICT_DRIFT_DAYS=3` iken 5 gün drift → uyarı."""
    monkeypatch.setenv("ATLAS_STRICT_DRIFT_DAYS", "3")
    p = tmp_path / "d.md"
    _write_decisions(p, "2026-07-25")
    r = _check_decisions_drift(p, today=date(2026, 7, 30))
    assert r["threshold_days"] == 3
    assert r["drift_days"] == 5
    assert r["warning"] is not None


# ─────────────────────────────────────────────────────────────────────
# _cmd_doctor + --strict entegrasyonu
# ─────────────────────────────────────────────────────────────────────


def test_032_doctor_strict_yok_exit_0_temiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--strict` yok + drift olsa da exit 0 (uyarı görünür, kesici değil)."""
    p = tmp_path / "d.md"
    _write_decisions(p, "2026-01-01")  # aşırı eski
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[Kalite kapıları]" in out
    assert "gün önce" in out  # drift bilgisi görünür


def test_032_doctor_strict_temiz_exit_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--strict` + drift yok + entry var + vault dolu → exit 0."""
    p = tmp_path / "d.md"
    # Bugün için giriş → drift=0, entry_count >= 1
    _write_decisions(p, date.today().isoformat())
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    # SPEC 032.1: vault sağlığı da temiz olmalı (>= 1 .md)
    vault = tmp_path / "v"
    vault.mkdir(exist_ok=True)
    (vault / "note.md").write_text("# not", encoding="utf-8")
    monkeypatch.setenv("ATLAS_VAULT", str(vault))
    rc = main(["doctor", "--strict"])
    assert rc == 0


def test_032_doctor_strict_drift_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--strict` + eşik aşımı drift → exit 9."""
    p = tmp_path / "d.md"
    _write_decisions(p, "2020-01-01")  # 6 yıl önce
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    rc = main(["doctor", "--strict"])
    assert rc == 9
    out = capsys.readouterr().out
    assert "gün önce" in out


def test_032_doctor_strict_decisions_yok_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--strict` + DECISIONS yok → exit 9."""
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", tmp_path / "yok.md")
    rc = main(["doctor", "--strict"])
    assert rc == 9


def test_032_doctor_json_quality_alani_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--json` çıktısında `quality.decisions_drift` alanı var."""
    p = tmp_path / "d.md"
    _write_decisions(p, "2026-07-30")
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "quality" in data
    assert "decisions_drift" in data["quality"]
    assert data["quality"]["decisions_drift"]["last_date"] == "2026-07-30"


def test_032_doctor_json_strict_drift_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--json --strict` + drift → JSON basılır + exit 9."""
    p = tmp_path / "d.md"
    _write_decisions(p, "2020-01-01")
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    rc = main(["doctor", "--json", "--strict"])
    assert rc == 9
    # JSON hâlâ basıldı (CI script dosyaya kaydeder)
    data = json.loads(capsys.readouterr().out.strip())
    assert data["quality"]["decisions_drift"]["warning"] is not None


# ═════════════════════════════════════════════════════════════════════
# SPEC 032.1 — entry_count + vault_health denetimleri
# ═════════════════════════════════════════════════════════════════════


def _write_multi_decisions(path: Path, iso_dates: list[str]) -> None:
    """Test yardımcısı: DECISIONS.md'de birden fazla giriş."""
    body = "# ATLAS Karar Günlüğü\n\n"
    for d in iso_dates:
        body += f"## {d} (test)\n- karar\n\n"
    path.write_text(body, encoding="utf-8")


def test_0321_entry_count_yeni_girisler(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Son 30 günde 3 giriş varsa → sayı 3, uyarı yok."""
    from atlas_core.cli import _count_recent_decisions

    p = tmp_path / "d.md"
    _write_multi_decisions(p, ["2026-07-30", "2026-07-25", "2026-07-15"])
    r = _count_recent_decisions(p, today=date(2026, 7, 30))
    assert r["count"] == 3
    assert r["warning"] is None
    assert r["threshold_days"] == 30
    assert r["min_entries"] == 1


def test_0321_entry_count_pencere_disi_uyari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Tüm girişler 40 gün önce → count=0 + uyarı."""
    from atlas_core.cli import _count_recent_decisions

    p = tmp_path / "d.md"
    _write_multi_decisions(p, ["2026-06-01", "2026-06-10"])
    r = _count_recent_decisions(p, today=date(2026, 7, 30))
    assert r["count"] == 0
    assert r["warning"] is not None
    assert "0 giriş" in r["warning"]


def test_0321_entry_count_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Env override: window=7 + min=2 → 3 girişten sadece 1'i pencere içi."""
    from atlas_core.cli import _count_recent_decisions

    monkeypatch.setenv("ATLAS_STRICT_ENTRY_WINDOW_DAYS", "7")
    monkeypatch.setenv("ATLAS_STRICT_MIN_ENTRIES", "2")
    p = tmp_path / "d.md"
    _write_multi_decisions(p, ["2026-07-30", "2026-07-20", "2026-07-10"])
    r = _count_recent_decisions(p, today=date(2026, 7, 30))
    assert r["threshold_days"] == 7
    assert r["min_entries"] == 2
    assert r["count"] == 1  # yalnız 07-30
    assert r["warning"] is not None
    assert "1 giriş" in r["warning"]
    assert "minimum 2" in r["warning"]


def test_0321_entry_count_dosya_yok_uyari(tmp_path: Path) -> None:
    """DECISIONS yoksa count=0 + uyarı."""
    from atlas_core.cli import _count_recent_decisions

    r = _count_recent_decisions(tmp_path / "yok.md", today=date(2026, 7, 30))
    assert r["count"] == 0
    assert r["warning"] is not None


def test_0321_vault_yok_uyari(tmp_path: Path) -> None:
    """Vault dizini yoksa uyarı."""
    from atlas_core.cli import _check_vault_health

    r = _check_vault_health(tmp_path / "olmayan-vault")
    assert r["exists"] is False
    assert r["note_count"] == 0
    assert r["warning"] is not None
    assert "vault yok" in r["warning"]


def test_0321_vault_bos_uyari(tmp_path: Path) -> None:
    """Vault dizini var + `.md` yok → uyarı."""
    from atlas_core.cli import _check_vault_health

    v = tmp_path / "v"
    v.mkdir()
    r = _check_vault_health(v)
    assert r["exists"] is True
    assert r["note_count"] == 0
    assert r["warning"] is not None
    assert "boş" in r["warning"]


def test_0321_vault_dolu_temiz(tmp_path: Path) -> None:
    """Vault + 1 `.md` → temiz."""
    from atlas_core.cli import _check_vault_health

    v = tmp_path / "v"
    v.mkdir()
    (v / "note.md").write_text("# not", encoding="utf-8")
    r = _check_vault_health(v)
    assert r["exists"] is True
    assert r["note_count"] == 1
    assert r["warning"] is None


def test_0321_doctor_strict_entry_count_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--strict` + drift yok ama entry_count 0 → exit 9 (tek kanal)."""
    from datetime import timedelta

    p = tmp_path / "d.md"
    # Bugün için drift denetimi temiz (aynı gün); ama window=30 dışında
    # tek giriş → count=0. Bunu yaratmak için ATLAS_STRICT_ENTRY_WINDOW_DAYS=5
    # + son giriş 10 gün önce
    monkeypatch.setenv("ATLAS_STRICT_DRIFT_DAYS", "365")  # drift uyarısı yok
    monkeypatch.setenv("ATLAS_STRICT_ENTRY_WINDOW_DAYS", "5")
    _write_decisions(p, (date.today() - timedelta(days=10)).isoformat())
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    rc = main(["doctor", "--strict"])
    assert rc == 9  # entry_count uyarısı üzerinden strict tetiklendi


def test_0321_doctor_strict_vault_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--strict` + vault yok → exit 9 (üçüncü kanal)."""
    p = tmp_path / "d.md"
    _write_decisions(p, date.today().isoformat())
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "vault-yok"))
    rc = main(["doctor", "--strict"])
    assert rc == 9


def test_0321_doctor_json_quality_alanlari_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """JSON çıktısında entry_count + vault_health alanları görünür."""
    p = tmp_path / "d.md"
    _write_decisions(p, "2026-07-30")
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "entry_count" in data["quality"]
    assert "vault_health" in data["quality"]
    assert "count" in data["quality"]["entry_count"]
    assert "note_count" in data["quality"]["vault_health"]


# ═════════════════════════════════════════════════════════════════════
# SPEC 032.2 — atlas doctor --scan-src birleşme
# ═════════════════════════════════════════════════════════════════════


def _prep_temiz_doctor_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ortak setup: DECISIONS bugün + vault dolu (drift/entry/vault temiz)."""
    p = tmp_path / "d.md"
    _write_decisions(p, date.today().isoformat())
    monkeypatch.setattr(cli_mod, "_DECISIONS_MD_DEFAULT", p)
    vault = tmp_path / "v"
    vault.mkdir(exist_ok=True)
    (vault / "note.md").write_text("# not", encoding="utf-8")
    monkeypatch.setenv("ATLAS_VAULT", str(vault))


def test_0322_scan_src_yoksa_alan_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--scan-src` verilmezse `quality.scan_src` alanı JSON'da YOK."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "scan_src" not in data["quality"]  # bit-uyumluluk


def test_0322_scan_src_bayrak_temiz_alan_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--scan-src` (bulgu yok) → alan var, warning None."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    src = tmp_path / "src-clean"
    src.mkdir()
    (src / "ok.py").write_text("x = 1\n", encoding="utf-8")
    rc = main(["doctor", "--scan-src", str(src), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "scan_src" in data["quality"]
    assert data["quality"]["scan_src"]["total"] == 0
    assert data["quality"]["scan_src"]["warning"] is None


def test_0322_scan_src_sir_bulundu_warning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--scan-src` bulgu > 0 → warning gövdesi + sample_files."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    src = tmp_path / "src-dirty"
    src.mkdir()
    # scan_secrets tanıdığı bir kalıp — Anthropic API key formatı
    (src / "config.py").write_text(
        'ANTHROPIC_API_KEY = "sk-ant-api03-abcdef1234567890ABCDEF1234567890"\n',
        encoding="utf-8",
    )
    rc = main(["doctor", "--scan-src", str(src), "--json"])
    assert rc == 0  # strict yok, uyarı bilgi
    data = json.loads(capsys.readouterr().out.strip())
    assert data["quality"]["scan_src"]["total"] >= 1
    assert data["quality"]["scan_src"]["warning"] is not None
    assert "config.py" in " ".join(data["quality"]["scan_src"]["sample_files"])


def test_0322_scan_src_strict_sir_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--scan-src --strict` + sır → exit 9 (tek kanal _has_quality_warning)."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    src = tmp_path / "src-dirty"
    src.mkdir()
    (src / "config.py").write_text(
        'ANTHROPIC_API_KEY = "sk-ant-api03-abcdef1234567890ABCDEF1234567890"\n',
        encoding="utf-8",
    )
    rc = main(["doctor", "--scan-src", str(src), "--strict"])
    assert rc == 9


def test_0322_scan_src_dizin_yok_warning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--scan-src <yok>` → warning ('scan hedefi yok')."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    rc = main(["doctor", "--scan-src", str(tmp_path / "olmayan-src"), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["quality"]["scan_src"]["warning"] is not None
    assert "yok" in data["quality"]["scan_src"]["warning"]


def test_0322_scan_src_insan_format(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--scan-src` insan format → '[Kalite kapıları]' altında 'sır taraması:' satırı."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    src = tmp_path / "src-clean"
    src.mkdir()
    rc = main(["doctor", "--scan-src", str(src)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "sır taraması:" in out
    assert "0 bulgu" in out


def test_0322_atlas_scan_komutu_korundu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas scan <path>` bağımsız komutu SÖZLEŞMESİ değişmez (regresyon)."""
    src = tmp_path / "src-clean"
    src.mkdir()
    (src / "ok.py").write_text("x = 1\n", encoding="utf-8")
    rc = main(["scan", str(src)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Sır bulunamadı." in out


# ═════════════════════════════════════════════════════════════════════
# SPEC 032.3 — `_iter_scan_hits` DRY yardımcısı
# ═════════════════════════════════════════════════════════════════════


def test_0323_iter_hits_dizin_yok_bos_liste(tmp_path: Path) -> None:
    """Var olmayan yol → boş liste (exception değil)."""
    from atlas_core.cli import _iter_scan_hits

    hits = _iter_scan_hits(tmp_path / "olmayan")
    assert hits == []


def test_0323_iter_hits_bir_bulgu_tek_dosya(tmp_path: Path) -> None:
    """Tek dosyada en az bir bulgu (`scan_secrets` çoklu kalıp yakalayabilir)."""
    from atlas_core.cli import _iter_scan_hits

    src = tmp_path / "src"
    src.mkdir()
    (src / "cfg.py").write_text(
        'ANTHROPIC_API_KEY = "sk-ant-api03-abcdef1234567890ABCDEF1234567890"\n',
        encoding="utf-8",
    )
    hits = _iter_scan_hits(src)
    assert len(hits) >= 1
    # Her tuple 3 elemanlı ve Path cfg.py'yi işaret ediyor
    for f, name, masked in hits:
        assert f.name == "cfg.py"
        assert name  # sır ismi dolu
        assert masked  # maskeli değer dolu


def test_0323_iter_hits_coklu_dosya_coklu_bulgu(tmp_path: Path) -> None:
    """İki dosyada bulgu → her ikisi de listede."""
    from atlas_core.cli import _iter_scan_hits

    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text(
        'K = "sk-ant-api03-aaaaaa1234567890AAAAAA1234567890"\n',
        encoding="utf-8",
    )
    (src / "b.py").write_text(
        'K = "sk-ant-api03-bbbbbb1234567890BBBBBB1234567890"\n',
        encoding="utf-8",
    )
    hits = _iter_scan_hits(src)
    file_names = {f.name for f, _n, _m in hits}
    assert file_names == {"a.py", "b.py"}
    assert len(hits) >= 2  # her dosyada en az 1 bulgu


def test_0323_iter_hits_tek_dosya_argumani(tmp_path: Path) -> None:
    """Path bir dosya (dizin değil) → o dosyayı tara."""
    from atlas_core.cli import _iter_scan_hits

    f = tmp_path / "single.py"
    f.write_text(
        'K = "sk-ant-api03-xxxxx1234567890XXXXXX1234567890"\n',
        encoding="utf-8",
    )
    hits = _iter_scan_hits(f)
    assert len(hits) >= 1
    for hit_f, _n, _m in hits:
        assert hit_f == f


def test_0323_iter_hits_okuma_hatasi_sessiz_atla(tmp_path: Path) -> None:
    """Binary/UnicodeDecodeError dosya sessiz atlanır (exception yok)."""
    from atlas_core.cli import _iter_scan_hits

    src = tmp_path / "src"
    src.mkdir()
    # Binary dosya — UnicodeDecodeError verecek
    (src / "binary.bin").write_bytes(b"\x00\x01\xff\xfe" * 100)
    # Ayrıca bir metin dosyası temiz
    (src / "ok.py").write_text("x = 1\n", encoding="utf-8")
    hits = _iter_scan_hits(src)
    # Binary atlanır, ok.py'de bulgu yok — toplam 0
    assert hits == []


# ═════════════════════════════════════════════════════════════════════
# SPEC 032.4 — `atlas doctor` JSON şema versiyonu
# ═════════════════════════════════════════════════════════════════════


def test_0324_json_schema_version_alani(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--json` çıktısında `schema_version` alanı sabit `"1"` döner."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data.get("schema_version") == "1"


def test_0324_json_regresyon_mevcut_alanlar_korundu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Yeni schema_version alanı EKLENDI; mevcut alanlar aynen."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    # Mevcut alanlar aynen (021 + 032 + 032.1)
    assert "backend" in data
    assert "retry_pricing" in data
    assert "storage" in data
    assert "warnings" in data
    assert "quality" in data
    # Quality alt-alanları (032 + 032.1)
    assert "decisions_drift" in data["quality"]
    assert "entry_count" in data["quality"]
    assert "vault_health" in data["quality"]


def test_0324_insan_format_sema_versiyonu_baslikta(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """İnsan format başlığında '(şema v1)' görünür."""
    _prep_temiz_doctor_env(monkeypatch, tmp_path)
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "şema v1" in out
    # Başlık formatı korundu (aynı '===' desenli)
    assert "=== ATLAS doctor" in out


def test_0324_schema_version_sabit_modul_seviyesinde() -> None:
    """`_DOCTOR_SCHEMA_VERSION` modül seviyesinde `"1"` sabit."""
    from atlas_core.cli import _DOCTOR_SCHEMA_VERSION

    assert _DOCTOR_SCHEMA_VERSION == "1"


def test_0323_check_scan_src_unique_sample_files(tmp_path: Path) -> None:
    """`_check_scan_src`: bir dosyada ÇOK bulgu → sample_files aynı
    dosyayı iki kez basmaz (unique)."""
    from atlas_core.cli import _check_scan_src

    src = tmp_path / "src"
    src.mkdir()
    # Aynı dosyada iki farklı sır kalıbı
    (src / "leaky.py").write_text(
        'A = "sk-ant-api03-aaaaaa1234567890AAAAAA1234567890"\n'
        'B = "sk-ant-api03-bbbbbb1234567890BBBBBB1234567890"\n',
        encoding="utf-8",
    )
    r = _check_scan_src(src)
    assert r["total"] == 2  # iki bulgu
    assert len(r["sample_files"]) == 1  # tek unique dosya
    assert r["sample_files"][0].endswith("leaky.py")
