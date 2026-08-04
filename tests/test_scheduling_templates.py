"""SPEC 048 — tools/scheduling/ şablon bütünlük testleri.

Kod DEĞİL, deployment artefaktları. Test amacı: şablonların doğru
placeholder'ları içerdiğinden ve XML'in geçerli olduğundan emin ol.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCHED = _REPO / "tools" / "scheduling"


# ═════════════════════════════════════════════════════════════════════
# Dosya varlığı
# ═════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("name", [
    "README.md",
    "atlas-vault-backup.service",
    "atlas-vault-backup.timer",
    "atlas-vault-backup.xml",
    "install-linux.sh",
    "install-windows.ps1",
])
def test_048_sablon_dosyalari_mevcut(name: str) -> None:
    p = _SCHED / name
    assert p.is_file(), f"eksik şablon: {p}"


# ═════════════════════════════════════════════════════════════════════
# Linux: systemd
# ═════════════════════════════════════════════════════════════════════


def test_048_service_dosyasi_placeholderlar_iceriyor() -> None:
    """systemd .service dosyası tüm sed placeholder'larını taşımalı."""
    text = (_SCHED / "atlas-vault-backup.service").read_text(encoding="utf-8")
    # install-linux.sh bunları sed ile doldurur — hepsi mevcut olmalı
    for placeholder in ("%I%", "%P%", "%R%", "%K%"):
        assert placeholder in text, f"eksik placeholder: {placeholder}"
    # ATLAS komutu doğru şekilde çağrılmalı
    assert "vault backup --auto" in text
    assert "--archive-root %R%" in text
    assert "--keep %K%" in text
    # Idempotent oneshot
    assert "Type=oneshot" in text


def test_048_timer_dosyasi_gunluk_03_utc() -> None:
    text = (_SCHED / "atlas-vault-backup.timer").read_text(encoding="utf-8")
    assert "OnCalendar=*-*-* 03:00:00" in text
    assert "Persistent=true" in text  # kaçırılan çalıştırma açılışta koşar
    assert "RandomizedDelaySec=" in text  # jitter — thundering herd önleme
    assert "Requires=atlas-vault-backup.service" in text


def test_048_install_linux_sh_shebang_ve_set() -> None:
    text = (_SCHED / "install-linux.sh").read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env sh"), "shebang eksik"
    assert "set -eu" in text
    # sed doldurma — 4 placeholder
    for ph in ("%I%", "%P%", "%R%", "%K%"):
        assert f'"s|{ph}|' in text, f"install-linux sed eksik: {ph}"
    assert "systemctl --user daemon-reload" in text
    assert "systemctl --user enable --now atlas-vault-backup.timer" in text


# ═════════════════════════════════════════════════════════════════════
# Windows: Task Scheduler XML
# ═════════════════════════════════════════════════════════════════════


def test_048_xml_gecerli_ve_placeholderlar_iceriyor() -> None:
    """XML valid + install-windows.ps1'in doldurduğu 4 placeholder mevcut."""
    xml_path = _SCHED / "atlas-vault-backup.xml"
    text = xml_path.read_text(encoding="utf-8")

    # 1) XML valid parse
    tree = ET.fromstring(text)  # ParseError → test fail
    assert tree.tag.endswith("Task"), "kök element Task olmalı"

    # 2) Placeholder'lar (4 tane)
    for ph in ("__ATLAS_BIN__", "__ARCHIVE_ROOT__", "__REPO_ROOT__", "__KEEP__"):
        assert ph in text, f"eksik placeholder: {ph}"

    # 3) ATLAS komutu şeması
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    exec_elem = tree.find(".//t:Exec", ns)
    assert exec_elem is not None, "Exec elementi bulunamadı"
    cmd = exec_elem.find("t:Command", ns)
    args = exec_elem.find("t:Arguments", ns)
    wd = exec_elem.find("t:WorkingDirectory", ns)
    assert cmd is not None and cmd.text == "__ATLAS_BIN__"
    assert args is not None and "vault backup --auto" in (args.text or "")
    assert wd is not None and wd.text == "__REPO_ROOT__"


def test_048_xml_gunluk_tetikleyici() -> None:
    """XML günlük 03:00 tetikleyici + 10dk jitter."""
    xml_path = _SCHED / "atlas-vault-backup.xml"
    text = xml_path.read_text(encoding="utf-8")
    tree = ET.fromstring(text)
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}

    cal = tree.find(".//t:CalendarTrigger", ns)
    assert cal is not None
    start = cal.find("t:StartBoundary", ns)
    assert start is not None and "T03:00:00" in (start.text or "")
    days = cal.find(".//t:DaysInterval", ns)
    assert days is not None and days.text == "1"
    random_delay = cal.find("t:RandomDelay", ns)
    assert random_delay is not None and random_delay.text == "PT10M"


def test_048_install_windows_ps1_placeholder_replace() -> None:
    """PowerShell betiği 4 placeholder'ı sırayla replace ediyor."""
    text = (_SCHED / "install-windows.ps1").read_text(encoding="utf-8")
    assert "[CmdletBinding()]" in text  # CmdletBinding güvenilir param
    assert "param(" in text
    for ph in ("__ATLAS_BIN__", "__ARCHIVE_ROOT__", "__REPO_ROOT__", "__KEEP__"):
        assert f'"{ph}"' in text, f"install-windows Replace eksik: {ph}"
    assert 'schtasks /Create /TN "ATLAS Vault Backup"' in text
    assert 'schtasks /Delete /TN "ATLAS Vault Backup"' in text  # idempotent


# ═════════════════════════════════════════════════════════════════════
# README
# ═════════════════════════════════════════════════════════════════════


def test_048_readme_platformlari_dokumante_ediyor() -> None:
    text = (_SCHED / "README.md").read_text(encoding="utf-8")
    assert "Linux (systemd)" in text
    assert "Windows (Task Scheduler)" in text
    assert "atlas vault backup --auto --keep N" in text
    # SPEC referansları
    assert "SPEC 041" in text
    assert "SPEC 041.1" in text
    assert "SPEC 048" in text
