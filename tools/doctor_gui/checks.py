"""Sağlık denetimleri — her biri "ne gördüm / nedeni / çözümü" üretir.

Tasarım kuralı: bir denetim ASLA yalnız "hata" demez. Üç şeyi birden söyler —
**kanıt** (ölçülen gerçek: yol, sürüm, komut çıktısı), **kaynak** (neden böyle
oldu) ve **çözüm** (ne yapılacak, otomatik düzeltilebiliyorsa hangi eylem).
Arayüz bu üçlüyü olduğu gibi gösterir; kullanıcı ekranda kök nedeni görür.

Denetimler altı adıma bölünmüştür (`STEPS`); arayüz adım adım ilerletir, böylece
uzun süren canlı el sıkışması testi hızlı dosya denetimlerini bekletmez.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

from tools.juggler_profile import sync as profile_sync
from tools.setup_gui import connect as connect_mod
from tools.setup_gui.acp_probe import effective_entry, probe_all
from tools.setup_gui.detect import (
    IS_WIN,
    _exe,
    acp_config_paths,
    agent_specs,
    detect_ollama,
    detect_runtimes,
    project_root,
)

from . import processes, versions

# --- bulgu modeli -------------------------------------------------------------

OK, WARN, FAIL, INFO = "ok", "warn", "fail", "info"


@dataclass
class Finding:
    id: str
    area: str
    title: str
    status: str  # ok | warn | fail | info
    detail: str  # ÖLÇÜLEN gerçek (kanıt)
    cause: str = ""  # kök neden
    remedy: str = ""  # çözüm yolu (insan diliyle)
    fix: str | None = None  # otomatik düzeltme eylemi (fixes.ACTIONS anahtarı)
    fix_label: str | None = None
    evidence: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _f(**kw) -> Finding:
    return Finding(**kw)


# --- yardımcılar --------------------------------------------------------------


def baseline_path(root: Path) -> Path:
    """Son 'her şey yeşildi' anındaki sürümlerin kaydı (.atlas/ git'te yok)."""
    return root / ".atlas" / "doctor" / "baseline.json"


def read_baseline(root: Path) -> dict:
    p = baseline_path(root)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_baseline(root: Path, versions_map: dict[str, str | None]) -> Path:
    p = baseline_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            {"versions": versions_map, "juggler_sha256": sha256_file(juggler_exe(root))},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return p


def sha256_file(path: Path, chunk: int = 1 << 20) -> str | None:
    """Dosyanın parmak izi (yoksa None). Panel ikilisinin sessizce değişip
    değişmediğini anlamak için kullanılır."""
    if not path.is_file():
        return None
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            for block in iter(lambda: fh.read(chunk), b""):
                h.update(block)
    except OSError:
        return None
    return h.hexdigest()


def _run(argv: list[str], timeout: float = 30.0, cwd: Path | None = None) -> tuple[int, str]:
    """Komutu kabuksuz çalıştırır → (çıkış kodu, birleşik çıktı)."""
    try:
        out = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return 124, "zaman aşımı"
    except OSError as exc:
        return 127, str(exc)
    return out.returncode, ((out.stdout or "") + (out.stderr or "")).strip()


def ext_source_dir(root: Path) -> Path:
    return root / "juggler-profile" / "extensions" / "atlas-engineering"


def ext_installed_dir(root: Path | None = None) -> Path:
    """Eklentinin kurulu kopyası — profil çalışma dizini varsa orada.

    Profil kullanılmadığında (başlatıcılar dışından açılmış bir Juggler)
    Juggler hâlâ `~/.juggler`a bakar; denetim de oraya düşer.
    """
    if root is not None:
        home = profile_sync.home_dir(root)
        if home.is_dir():
            return home / "extensions" / "atlas-engineering"
    return Path.home() / ".juggler" / "extensions" / "atlas-engineering"


def juggler_exe(root: Path) -> Path:
    return root / "tools" / "juggler" / _exe("juggler")


def backup_dir(root: Path) -> Path:
    """Panel ikililerinin geri dönüş kopyası (güncelleme öncesi alınır)."""
    return root / ".atlas" / "doctor" / "juggler-backup"


# --- 1) çalışma zamanları -----------------------------------------------------


def check_runtime(root: Path) -> list[Finding]:
    r = detect_runtimes(root)
    out: list[Finding] = []

    py = r["python_embedded"] or r["venv"] or r["python_running"]
    out.append(
        _f(
            id="py.present",
            area="Çalışma zamanı",
            title="Python",
            status=OK if py else FAIL,
            detail=str(py or "bulunamadı"),
            cause="" if py else "Ne gömülü çalışma zamanı ne de sanal ortam var.",
            remedy="" if py else "SETUP.cmd → '2. ATLAS kur' adımını çalıştırın.",
        )
    )

    venv = r["venv"]
    out.append(
        _f(
            id="py.venv",
            area="Çalışma zamanı",
            title="ATLAS çekirdeği (sanal ortam)",
            status=OK if venv else WARN,
            detail=str(venv or "kurulu değil"),
            cause="" if venv else "setup-portable.cmd henüz çalıştırılmamış.",
            remedy="" if venv else "SETUP.cmd → 'ATLAS kur'.",
        )
    )

    # Çekirdek gerçekten import edilebiliyor mu (kurulu olmak yetmez).
    # Makinede birden fazla ortam olabilir (taşınabilir runtime/venv ve geliştirme
    # .venv); BİRİ çalışıyorsa çekirdek sağlamdır — hangisi olduğunu da yazarız.
    candidates = [
        p
        for p in (r["venv"], root / ".venv" / ("Scripts" if IS_WIN else "bin") / _exe("python"))
        if p
    ]
    working, failures = None, []
    for cand in candidates:
        if not Path(cand).is_file():
            continue
        code, blob = _run(
            [str(cand), "-c", "import atlas_core, sys; print(sys.version.split()[0])"]
        )
        if code == 0:
            working = (str(cand), blob.strip())
            break
        failures.append(f"{cand}: {blob.splitlines()[-1][:160] if blob else 'hata'}")
    if candidates:
        out.append(
            _f(
                id="py.import",
                area="Çalışma zamanı",
                title="atlas_core içe aktarılıyor",
                status=OK if working else FAIL,
                detail=f"{working[0]} (Python {working[1]})"
                if working
                else "hiçbir ortamda import edilemedi",
                cause=""
                if working
                else "Sanal ortam var ama paket eksik/bozuk — çoğunlukla yarım kalmış "
                "kurulum veya bağımlılık güncellemesi sonrası uyumsuzluk.",
                remedy="" if working else "setup-portable.cmd'yi yeniden çalıştırın.",
                fix=None if working else "install-core",
                fix_label=None if working else "Çekirdeği yeniden kur",
                evidence=failures if not working else [],
            )
        )

    node_ok = bool(r["node"])
    out.append(
        _f(
            id="node.present",
            area="Çalışma zamanı",
            title="Node.js",
            status=OK if node_ok else WARN,
            detail=r["node_version"] or "bulunamadı",
            cause="" if node_ok else "Node kurulu değil veya PATH'te görünmüyor.",
            remedy=""
            if node_ok
            else "Kilo ve Cline ajanları Node ile çalışır; nodejs.org'dan kurun. "
            "Diğer ajanlar Node olmadan da çalışır.",
        )
    )
    out.append(
        _f(
            id="npm.present",
            area="Çalışma zamanı",
            title="npm",
            status=OK if r["npm"] else WARN,
            detail=r["npm_version"] or "bulunamadı",
            cause="" if r["npm"] else "npm yok — CLI güncellemeleri yapılamaz.",
            remedy="" if r["npm"] else "Node.js kurulumu npm'i de getirir.",
        )
    )
    return out


# --- 2) Juggler paneli --------------------------------------------------------


def check_juggler(root: Path, want_remote: bool = True) -> list[Finding]:
    out: list[Finding] = []
    exe = juggler_exe(root)
    app = root / "tools" / "juggler" / _exe("juggler-app")

    if not exe.is_file():
        out.append(
            _f(
                id="juggler.exe",
                area="Juggler",
                title="Panel ikilisi (juggler)",
                status=FAIL,
                detail=f"yok: {exe}",
                cause="tools/juggler/ git'te tutulmaz (AGPL + boyut); ikili kaynaktan "
                "derlenir. Yeni bir kopyada veya temizlikten sonra eksik olur.",
                remedy="docs/JUGGLER.md → kaynaktan derleyip tools/juggler/ altına koyun. "
                "Yedek varsa tek tıkla geri alınabilir.",
                fix="juggler-restore" if (backup_dir(root) / _exe("juggler")).is_file() else None,
                fix_label="Yedekten geri al",
            )
        )
        return out

    local = versions.local_versions(root)["juggler"]
    latest = versions.remote_latest("juggler") if want_remote else None
    outdated = versions.is_outdated(local, latest)
    out.append(
        _f(
            id="juggler.version",
            area="Juggler",
            title="Panel sürümü",
            status=WARN if outdated else OK,
            detail=f"yerel: {local or 'okunamadı'}"
            + (f" · üstakım: v{latest}" if latest else " · üstakım: sorgulanamadı (çevrimdışı?)"),
            cause="Yeni sürüm yayınlanmış." if outdated else "",
            remedy="Güncelleme ATLAS deposunu bozmaz (tools/juggler/ git dışıdır) ama "
            "eklenti uyumluluğunu bozabilir. Önce yedek alın, sonra yeni ikiliyi "
            "koyun ve aşağıdaki 'eklenti uyumluluğu' denetimini tekrarlayın."
            if outdated
            else "",
            fix="update-juggler" if outdated else None,
            fix_label="Güvenli güncelleme adımları" if outdated else None,
        )
    )

    # Panel kendi kendini güncelleyebilir: çalışan .exe'yi yeniden adlandırıp
    # yerine indirdiğini koyar. ATLAS panelini tools/juggler/ altından çalıştırdığı
    # için bu, ATLAS'ın kullandığı ikilinin HABERSİZ değişmesi demektir — yerel
    # yamalar (ör. ACP authenticate düzeltmesi) sessizce kaybolur.
    base = read_baseline(root)
    known = base.get("juggler_sha256")
    current = sha256_file(exe)
    if known:
        same = known == current
        out.append(
            _f(
                id="juggler.fingerprint",
                area="Juggler",
                title="Panel ikilisi beklenen dosya",
                status=OK if same else FAIL,
                detail="parmak izi kayıtla aynı"
                if same
                else f"DEĞİŞTİ — kayıtlı {known[:12]}…, şu an {(current or '—')[:12]}…",
                cause=""
                if same
                else "Panel ikilisi son sağlıklı kayıttan sonra değişti. Elle "
                "değiştirmediyseniz panelin kendi güncelleyicisi çalışmış olabilir: "
                "indirdiği sürümde yerel düzeltmeleriniz (ACP authenticate, sarmalayıcı "
                "davranışı) BULUNMAZ ve ajanlar bağlanamaz hâle gelir.",
                remedy=""
                if same
                else "Ajanlar çalışıyorsa 'Sağlıklı hâli kaydet' ile yeni ikiliyi onaylayın. "
                "Bağlantı bozulduysa 'Yedekten geri al' ile eski ikiliye dönün.",
                fix=None if same else "juggler-restore",
                fix_label=None if same else "Yedekten geri al",
            )
        )

    have_backup = (backup_dir(root) / _exe("juggler")).is_file()
    out.append(
        _f(
            id="juggler.backup",
            area="Juggler",
            title="Geri dönüş yedeği",
            status=OK if have_backup else WARN,
            detail=str(backup_dir(root)) if have_backup else "yedek yok",
            cause="" if have_backup else "Çalışan ikilinin kopyası alınmamış.",
            remedy=""
            if have_backup
            else "Güncellemeden ÖNCE yedek alın: bozulursa tek tıkla geri dönersiniz.",
            fix=None if have_backup else "juggler-backup",
            fix_label=None if have_backup else "Şimdi yedek al",
        )
    )

    out.append(
        _f(
            id="juggler.app",
            area="Juggler",
            title="Masaüstü ikilisi (juggler-app)",
            status=OK if app.is_file() else WARN,
            detail=str(app) if app.is_file() else "yok — yalnız web arayüzü kullanılabilir",
            cause="" if app.is_file() else "Masaüstü penceresi ayrı bir ikilidir (Wails).",
            remedy="" if app.is_file() else "juggler-webui_Run.bat ile web arayüzünü kullanın.",
        )
    )

    # Eklenti kurulu mu ve sürümü kaynakla aynı mı?
    src, dst = ext_source_dir(root), ext_installed_dir(root)
    src_ver = _ext_version(src)
    dst_ver = _ext_version(dst)
    if not dst.is_dir():
        out.append(
            _f(
                id="ext.installed",
                area="Juggler",
                title="ATLAS eklentisi kurulu",
                status=FAIL,
                detail=f"yok: {dst}",
                cause="Eklenti ~/.juggler/extensions altına kopyalanmamış. Başlatıcılar "
                "her açılışta kopyalar; panel elle başlatıldıysa atlanmış olabilir.",
                remedy="Eklentiyi kur (kopyala) — panel yeniden başlatıldığında görünür.",
                fix="ext-install",
                fix_label="Eklentiyi kur",
            )
        )
    else:
        same = src_ver == dst_ver and _dir_same(src, dst)
        out.append(
            _f(
                id="ext.installed",
                area="Juggler",
                title="ATLAS eklentisi kurulu",
                status=OK if same else WARN,
                detail=f"kurulu: {dst_ver or '?'} · kaynak: {src_ver or '?'}"
                + ("" if same else " — kopya kaynaktan farklı"),
                cause="" if same else "Depoda eklenti güncellendi ama kurulu kopya eskide kaldı.",
                remedy="" if same else "Eklentiyi yeniden kopyalayın.",
                fix=None if same else "ext-install",
                fix_label=None if same else "Kopyayı tazele",
            )
        )

    # ASIL kırılma noktası: yeni panel ikilisi eklentiyi hâlâ kabul ediyor mu?
    code, blob = _run([str(exe), "ext", "validate", str(src)], timeout=60)
    ok = code == 0
    out.append(
        _f(
            id="ext.compat",
            area="Juggler",
            title="Eklenti ↔ panel uyumluluğu (engineApi)",
            status=OK if ok else FAIL,
            detail=(blob.splitlines() or ["çıktı yok"])[-1][:300],
            cause=""
            if ok
            else "Panel ikilisi eklentinin bildirdiği engineApi aralığını kabul etmiyor. "
            "Juggler güncellemesi motor API'sini büyüttüğünde tam olarak bu olur — "
            "eklenti sessizce yüklenmez, ATLAS araçları panelde kaybolur.",
            remedy=""
            if ok
            else "juggler-profile/extensions/atlas-engineering/juggler.extension.json "
            'içindeki "engineApi" '
            "aralığını yeni panelin desteklediği sürüme genişletin, sonra bu denetimi "
            "tekrarlayın. Çözülene kadar eski panel ikilisine dönmek güvenlidir.",
            fix=None if ok else "juggler-restore",
            fix_label=None if ok else "Eski panele dön (yedek)",
            # Başarılıysa özet satır zaten `detail`de; kanıtı tekrar basma.
            evidence=[] if ok else ([blob[:800]] if blob else []),
        )
    )
    return out


def _ext_version(d: Path) -> str | None:
    f = d / "juggler.extension.json"
    if not f.is_file():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("version")
    except (OSError, json.JSONDecodeError):
        return None


def _dir_same(a: Path, b: Path) -> bool:
    """Kaba ama yeterli karşılaştırma: aynı dosya adları ve aynı boyutlar."""

    def snap(d: Path) -> dict[str, int]:
        return {
            str(p.relative_to(d)).replace("\\", "/"): p.stat().st_size
            for p in d.rglob("*")
            if p.is_file()
        }

    try:
        return snap(a) == snap(b)
    except OSError:
        return False


# --- 2b) ATLAS profili --------------------------------------------------------


def check_profile(root: Path) -> list[Finding]:
    """ "Juggler klasörünü silsem ne kırılır?" sorusunun denetimi.

    ATLAS'ın Juggler'a kattığı her şey `juggler-profile/` altında durmalı ve
    Juggler oraya `JUGGLER_CONFIG_DIR` ile bakmalı. Bu doğruysa Juggler ağacı
    silinip yeniden kurulduğunda hiçbir şey kaybolmaz.
    """
    out: list[Finding] = []
    res = profile_sync.verify(root)
    home = profile_sync.home_dir(root)

    installed = home.is_dir()
    out.append(
        _f(
            id="profile.installed",
            area="ATLAS profili",
            title="Profil kurulu",
            status=OK if installed else WARN,
            detail=str(home) if installed else "henüz kurulmadı",
            cause=""
            if installed
            else "Profil çalışma dizini yok; Juggler hâlâ ~/.juggler'ı kullanıyor olabilir.",
            remedy="" if installed else "Profili kurun (başlatıcılar da her açılışta kurar).",
            fix=None if installed else "profile-sync",
            fix_label=None if installed else "Profili kur",
        )
    )

    stale = res["stale"]
    if installed:
        out.append(
            _f(
                id="profile.current",
                area="ATLAS profili",
                title="Kurulu kopya kaynakla aynı",
                status=OK if not stale else WARN,
                detail="güncel" if not stale else f"{len(stale)} öğe eski",
                cause="" if not stale else "Depoda değişen profil içeriği henüz kurulmadı.",
                remedy="" if not stale else "Profili tazeleyin.",
                fix=None if not stale else "profile-sync",
                fix_label=None if not stale else "Profili tazele",
                evidence=stale,
            )
        )

    # ASIL denetim: ATLAS ajanlarından herhangi biri depo dışını gösteriyor mu?
    external = res["external"]
    out.append(
        _f(
            id="profile.self-contained",
            area="ATLAS profili",
            title="Juggler klasöründen bağımsızlık",
            status=OK if not external else FAIL,
            detail="ATLAS kayıtlarının tümü depo içini gösteriyor"
            if not external
            else f"{len(external)} kayıt depo dışını gösteriyor",
            cause=""
            if not external
            else "Bir ACP kaydı ATLAS deposunun dışını (çoğunlukla Juggler ağacının "
            "içindeki sarmalayıcıları) gösteriyor. O klasör silinir veya Juggler "
            "yeniden kurulursa bu ajanlar çalışmaz.",
            remedy=""
            if not external
            else "Profili tazeleyin: kayıtlar ATLAS'ın kendi sarmalayıcılarına "
            "(tools/agents/*.cmd) yeniden yazılır.",
            fix=None if not external else "profile-sync",
            fix_label=None if not external else "Kayıtları ATLAS'a çevir",
            evidence=external,
        )
    )

    # Panelin kendi güncelleyicisi kapalı mı? (2026-07-27'de bu makinede açıkken
    # çalışan ikiliyi yerinde değiştirdi ve yerel derlemeyi sildi.)
    mode = res.get("update_mode", "?")
    off = mode == "off"
    out.append(
        _f(
            id="profile.autoupdate",
            area="ATLAS profili",
            title="Panelin otomatik güncelleyicisi",
            status=OK if off else FAIL,
            detail=f"updates.mode = {mode}" + (" (kapalı)" if off else " — AÇIK"),
            cause=""
            if off
            else "Otomatik güncelleme çalışan .exe'yi yerinde değiştirir. ATLAS panelini "
            "tools/juggler/ altından sürdüğü için indirilen upstream sürümü, kaynaktan "
            "derlenmiş yerel işin (ACP authenticate, childcontain, …) YERİNE geçer.",
            remedy=""
            if off
            else "Profili tazeleyin: settings.json'a updates.mode=off yazılır. Manuel "
            "'güncelleme denetle' çalışmaya devam eder; yalnız kendiliğinden indirme kapanır.",
            fix=None if off else "profile-sync",
            fix_label=None if off else "Otomatik güncellemeyi kapat",
        )
    )

    # Başlatıcılar Juggler'ı profile yönlendiriyor mu?
    wired = []
    for name in ("juggler-webui_Run.bat", "juggler-desktop_Run.bat"):
        f = root / name
        if f.is_file() and "JUGGLER_CONFIG_DIR" in f.read_text(encoding="utf-8", errors="replace"):
            wired.append(name)
    ok_wired = len(wired) == 2
    out.append(
        _f(
            id="profile.launchers",
            area="ATLAS profili",
            title="Başlatıcılar profili kullanıyor",
            status=OK if ok_wired else WARN,
            detail=", ".join(wired) if wired else "hiçbiri JUGGLER_CONFIG_DIR ayarlamıyor",
            cause=""
            if ok_wired
            else "Başlatıcı profili göstermezse Juggler varsayılan ~/.juggler'a düşer ve "
            "profil devre dışı kalır.",
            remedy="" if ok_wired else "Başlatıcıyı güncelleyin (bkz. juggler-profile/README.md).",
        )
    )
    return out


# --- 3) ACP ajanları ----------------------------------------------------------


def check_agents(root: Path, want_remote: bool = True) -> list[Finding]:
    specs = agent_specs(root)
    local = versions.local_versions(root)
    out: list[Finding] = []

    for name, spec in specs.items():
        label = spec["label"]
        installed = Path(spec["bin"]).is_file()
        if not installed:
            out.append(
                _f(
                    id=f"agent.{name}.installed",
                    area="ACP ajanları",
                    title=f"{label} kurulu",
                    status=WARN,
                    detail=f"yok: {spec['bin']}",
                    cause="CLI kurulmamış (veya farklı bir konuma kurulmuş).",
                    remedy="SETUP.cmd → '3. AI CLI kur' adımı bu ajanı kurar.",
                    fix="install-clis",
                    fix_label="AI CLI'ları kur",
                )
            )
            continue

        lv = local.get(name)
        latest = versions.remote_latest(name) if want_remote else None
        outdated = versions.is_outdated(lv, latest)
        out.append(
            _f(
                id=f"agent.{name}.version",
                area="ACP ajanları",
                title=f"{label} sürümü",
                status=WARN if outdated else OK,
                detail=f"yerel: {lv or 'okunamadı'}"
                + (f" · son: {latest}" if latest else " · son sürüm sorgulanamadı"),
                cause="Yeni sürüm var." if outdated else "",
                remedy="Güncelleme ajanın ACP sözleşmesini değiştirebilir; güncelledikten "
                "SONRA canlı sağlık kontrolünü çalıştırın."
                if outdated
                else "",
                fix=f"update-{name}" if outdated else None,
                fix_label="Güncelle" if outdated else None,
            )
        )
    return out


# --- 4) yerel AI --------------------------------------------------------------


def check_ollama(root: Path) -> list[Finding]:
    info = detect_ollama(root)
    out: list[Finding] = []

    installed = info["portable_installed"]
    out.append(
        _f(
            id="ollama.installed",
            area="Yerel AI",
            title="Taşınabilir Ollama",
            status=OK if installed else WARN,
            detail=info["portable_path"] if installed else "kurulu değil",
            cause=""
            if installed
            else "Anahtarsız (hesapsız) ajanlar yerel model sunucusuna bağlanır; yoksa "
            "yalnız bulut hesabı olan ajanlar çalışır.",
            remedy="" if installed else "SETUP.cmd → '4. Yerel AI' adımında 'İndir ve kur'.",
        )
    )

    serving = info["port_serving"]
    backend = info["backend_available"]
    out.append(
        _f(
            id="ollama.serving",
            area="Yerel AI",
            title=f"Model sunucusu (127.0.0.1:{info['port']})",
            status=OK if serving else (WARN if backend else INFO),
            detail="yanıt veriyor"
            if serving
            else ("proje portu kapalı; sistem Ollama 11434'te açık" if backend else "kapalı"),
            cause=""
            if serving
            else "Sunucu kendiliğinden başlamaz; ajan çağrılınca veya elle başlatılır.",
            remedy="" if serving else "Sunucuyu başlat.",
            fix=None if serving or not installed else "ollama-start",
            fix_label=None if serving or not installed else "Sunucuyu başlat",
        )
    )

    base = connect_mod.ollama_base_url(root)
    if base:
        models = connect_mod.ollama_models(base)
        has = bool(models)
        out.append(
            _f(
                id="ollama.models",
                area="Yerel AI",
                title="Yerel model",
                status=OK if has else WARN,
                detail=", ".join(models[:6]) if has else "sunucu yanıt veriyor ama model yok",
                cause="" if has else "Model deposu boş — sunucu çalışsa da istek üretemez.",
                remedy="" if has else "Bir model indirin (SETUP.cmd → Yerel AI).",
                evidence=[f"GET {base}/api/tags"],
            )
        )
    return out


# --- 5) yapılandırma bütünlüğü ------------------------------------------------


def check_config(root: Path) -> list[Finding]:
    out: list[Finding] = []
    paths = acp_config_paths(root)
    specs = agent_specs(root)

    for scope, p in paths.items():
        if not p.is_file():
            if scope == "project":
                out.append(
                    _f(
                        id="cfg.project.missing",
                        area="Yapılandırma",
                        title="Proje acp.json",
                        status=WARN,
                        detail=f"yok: {p}",
                        cause="Ajanlar bu projeye kaydedilmemiş; panel global kaydı kullanır "
                        "(başka bir kurulumu işaret ediyor olabilir).",
                        remedy="Ajanları bu projeye kaydedin.",
                        fix="register",
                        fix_label="Ajanları kaydet",
                    )
                )
            continue
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            out.append(
                _f(
                    id=f"cfg.{scope}.parse",
                    area="Yapılandırma",
                    title=f"{scope} acp.json okunabilir",
                    status=FAIL,
                    detail=str(exc),
                    cause="Dosya bozuk — panel hiçbir ajanı göremez.",
                    remedy="Kaydı yeniden üretin (dosya baştan yazılır).",
                    fix="register" if scope == "project" else None,
                    fix_label="Yeniden üret" if scope == "project" else None,
                )
            )

    # Kayıtlı her ajanın komutu gerçekten var mı? (Güncelleme sonrası en sık kopan yer:
    # paket yolu değişir, acp.json eski yolu göstermeye devam eder.)
    broken: list[str] = []
    for name in specs:
        entry = effective_entry(name, specs[name], root)
        cmd = entry["command"]
        target = cmd
        if Path(cmd).name.lower() in {"node", "node.exe"} and entry["args"]:
            target = entry["args"][0]
        resolved = shutil.which(cmd) if not Path(cmd).is_absolute() else cmd
        if not resolved or not Path(target).exists():
            broken.append(f"{name}: {target}")
    out.append(
        _f(
            id="cfg.paths",
            area="Yapılandırma",
            title="Kayıtlı ajan yolları geçerli",
            status=OK if not broken else FAIL,
            detail="tüm yollar mevcut" if not broken else f"{len(broken)} kırık yol",
            cause=""
            if not broken
            else "acp.json bir güncelleme/taşıma öncesindeki yolu gösteriyor. Panelde ajan "
            "görünür ama başlatılamaz — tipik 'güncelleme sonrası bağlantı hatası'.",
            remedy=""
            if not broken
            else "Kaydı yeniden üretin (yollar mevcut kuruluma göre yazılır).",
            fix=None if not broken else "register",
            fix_label=None if not broken else "Yolları tazele",
            evidence=broken,
        )
    )

    # Eklenti ATLAS CLI'sini PATH üzerinden çağırır; sözleşme atlas-sections --json.
    launcher = root / ("atlas-sections.cmd" if IS_WIN else "atlas-sections")
    if launcher.is_file():
        argv = ["cmd.exe", "/c", str(launcher)] if IS_WIN else [str(launcher)]
        code, blob = _run(
            [*argv, "i", "--h", "1000", "--b", "300", "--tw", "12", "--tf", "20", "--json"],
            timeout=90,
            cwd=root,
        )
        valid = code == 0 and blob.strip().startswith("{")
        out.append(
            _f(
                id="cfg.cli-bridge",
                area="Yapılandırma",
                title="ATLAS köprüsü (atlas-sections --json)",
                status=OK if valid else FAIL,
                detail="JSON döndü" if valid else (blob.splitlines() or ["çıktı yok"])[-1][:300],
                cause=""
                if valid
                else "Eklenti hesapları bu komuta shell-out ederek yapar. Komut JSON "
                "döndürmezse panelde araç çağrıları hata verir — çoğu zaman çekirdek "
                "kurulumu eksik ya da bağımlılık güncellemesi bozmuştur.",
                remedy="" if valid else "Çekirdeği yeniden kurun (setup-portable.cmd).",
                fix=None if valid else "install-core",
                fix_label=None if valid else "Çekirdeği yeniden kur",
                evidence=[] if valid else [blob[:800]],
            )
        )
    return out


# --- 5b) artık süreçler -------------------------------------------------------


def check_processes(root: Path) -> list[Finding]:
    """Sağlık testinden artakalan öksüz ajan süreçleri.

    Ajanın kendisi öldürülse de alt süreci yaşamaya devam edebiliyor (ölçüldü:
    cline, goose). Birikince çalışan `.exe` kilitli kalıyor: `npm install` EBUSY
    veriyor, klasör taşınamıyor. Panel açıkken denetim yapılmaz — o süreçler
    meşru olabilir.
    """
    if processes.juggler_running(root):
        return [
            _f(
                id="proc.stray",
                area="Artık süreçler",
                title="Öksüz ajan süreci",
                status=INFO,
                detail="panel açık — süreçler kullanımda olabilir, sayım yapılmadı",
                cause="",
                remedy="Denetim için paneli kapatıp taramayı tekrarlayın.",
            )
        ]

    found = processes.stray(root)
    return [
        _f(
            id="proc.stray",
            area="Artık süreçler",
            title="Öksüz ajan süreci",
            status=OK if not found else WARN,
            detail="yok" if not found else f"{len(found)} süreç hâlâ çalışıyor",
            cause=""
            if not found
            else "ACP sağlık testi ajanı kapatır ama bazı ajanlar işi bir ALT sürece "
            "yaptırır ve o öksüz kalır. Biriken süreçler ikiliyi kilitler: güncelleme "
            "EBUSY ile düşer, klasör taşınamaz.",
            remedy=""
            if not found
            else "Kapatın — hiçbiri bir işi sürdürmüyor; panel açılınca ajanlar yeniden "
            "başlatılır.",
            fix=None if not found else "kill-stray",
            fix_label=None if not found else f"{len(found)} süreci kapat",
            evidence=[f"{p['pid']}  {p['name']}  {p['path']}" for p in found[:10]],
        )
    ]


# --- 6) canlı sağlık kontrolü -------------------------------------------------

_STATUS_MAP = {
    "ready": (OK, "", ""),
    "needs_auth": (
        WARN,
        "Ajan bulut hesabı istiyor; kayıtlı kimlik yok veya süresi doldu.",
        "SETUP.cmd → 'Ajanları bağla' ekranındaki 'Giriş yap' düğmesini kullanın.",
    ),
    "needs_provider": (
        WARN,
        "Model sağlayıcısı ayarlı değil (ör. GOOSE_PROVIDER).",
        "Yerel Ollama'ya bağlayın ('Yerel modele bağla') veya sağlayıcı anahtarını girin.",
    ),
    "not_installed": (WARN, "İkili yok.", "SETUP.cmd → 'AI CLI kur'."),
    "timeout": (
        FAIL,
        "Ajan el sıkışmaya yanıt vermedi — çoğunlukla ilk açılış yavaşlığı ya da "
        "güncelleme sonrası bozulmuş kurulum.",
        "Tekrar deneyin; sürerse ajanı güncelleyin/yeniden kurun.",
    ),
    "error": (
        FAIL,
        "Ajan başlatıldı ama protokol hatası verdi.",
        "Aşağıdaki hata metnine bakın; ajanı güncellemek çoğu durumda çözer.",
    ),
}


def check_health(root: Path, names: list[str] | None = None) -> list[Finding]:
    """Panelin yaptığı GERÇEK el sıkışmayı yapar (initialize + session/new)."""
    out: list[Finding] = []
    specs = agent_specs(root)
    for res in probe_all(root, names):
        name = res["name"]
        label = specs.get(name, {}).get("label", name)
        status, cause, remedy = _STATUS_MAP.get(res["status"], (FAIL, "", ""))
        detail = res.get("detail", "")
        if res["status"] == "ready" and res.get("version"):
            detail = f"bağlantı doğrulandı (ajan {res['version']})"
        out.append(
            _f(
                id=f"health.{name}",
                area="Canlı sağlık",
                title=f"{label} — panel bağlantısı",
                status=status,
                detail=detail,
                cause=cause,
                remedy=remedy,
                fix="auth-hint" if res["status"] == "needs_auth" else None,
                fix_label="Nasıl giriş yaparım?" if res["status"] == "needs_auth" else None,
                evidence=[res["stderr"]] if res.get("stderr") else [],
            )
        )
    return out


# --- sürüm sapması (güncelleme ↔ arıza ilişkisi) ------------------------------


def check_drift(root: Path) -> list[Finding]:
    """Son sağlıklı andan bu yana hangi bileşenin sürümü değişti?

    Arıza ile güncellemeyi ilişkilendiren denetim budur: bir şey bozulduğunda
    kullanıcı "ne değişti?" sorusunun yanıtını tahmin etmek zorunda kalmaz.
    """
    base = read_baseline(root).get("versions") or {}
    if not base:
        return [
            _f(
                id="drift.baseline",
                area="Sürüm izi",
                title="Sağlıklı sürüm kaydı",
                status=INFO,
                detail="henüz kaydedilmedi",
                cause="Her şey yeşil olduğunda kaydedilir.",
                remedy="Tarama tamamen yeşil bittiğinde 'Sağlıklı hâli kaydet' düğmesini kullanın; "
                "sonraki bir güncelleme bir şeyi bozarsa hangi bileşenin değiştiği anında görünür.",
                fix="save-baseline",
                fix_label="Sağlıklı hâli kaydet",
            )
        ]

    now = versions.local_versions(root)
    changed = [
        f"{k}: {base.get(k) or '—'} → {now.get(k) or '—'}" for k in now if base.get(k) != now.get(k)
    ]
    return [
        _f(
            id="drift.changed",
            area="Sürüm izi",
            title="Son sağlıklı andan beri sürüm değişimi",
            status=OK if not changed else WARN,
            detail="değişiklik yok" if not changed else f"{len(changed)} bileşen değişti",
            cause=""
            if not changed
            else "Aşağıdaki bileşenler son sağlıklı kayıttan sonra güncellendi. Bir arıza "
            "varsa ilk şüpheli bunlardır.",
            remedy=""
            if not changed
            else "Canlı sağlık kontrolü yeşilse 'Sağlıklı hâli kaydet' ile yeni sürümleri "
            "temel alın; değilse ilgili bileşeni eski sürüme döndürün.",
            fix="save-baseline" if not changed else None,
            fix_label="Kaydı tazele" if not changed else None,
            evidence=changed,
        )
    ]


# --- adım kaydı ---------------------------------------------------------------

STEPS: list[dict] = [
    {"id": "runtime", "label": "Çalışma zamanları", "fn": check_runtime, "net": False},
    {"id": "juggler", "label": "Juggler paneli", "fn": check_juggler, "net": True},
    {"id": "profile", "label": "ATLAS profili", "fn": check_profile, "net": False},
    {"id": "agents", "label": "ACP ajanları", "fn": check_agents, "net": True},
    {"id": "ollama", "label": "Yerel AI", "fn": check_ollama, "net": False},
    {"id": "config", "label": "Yapılandırma", "fn": check_config, "net": False},
    {"id": "processes", "label": "Artık süreçler", "fn": check_processes, "net": False},
    {"id": "drift", "label": "Sürüm izi", "fn": check_drift, "net": False},
    {"id": "health", "label": "Canlı sağlık", "fn": check_health, "net": False},
]


def run_step(step_id: str, root: Path | None = None, want_remote: bool = True) -> list[dict]:
    """Tek bir adımı çalıştırır ve bulguları sözlük listesi olarak döndürür."""
    root = root or project_root()
    spec = next((s for s in STEPS if s["id"] == step_id), None)
    if spec is None:
        return []
    fn = spec["fn"]
    try:
        findings = fn(root, want_remote) if spec["net"] else fn(root)
    except Exception as exc:  # noqa: BLE001 - denetim çökse de tarama sürmeli
        findings = [
            _f(
                id=f"{step_id}.crashed",
                area=spec["label"],
                title="Denetim tamamlanamadı",
                status=FAIL,
                detail=f"{type(exc).__name__}: {exc}",
                cause="Denetimin kendisi beklenmedik bir hata verdi.",
                remedy="Bu metni geliştiriciye iletin; tarama diğer adımlarla sürüyor.",
            )
        ]
    return [f.as_dict() for f in findings]


def summarize(findings: list[dict]) -> dict:
    counts = {OK: 0, WARN: 0, FAIL: 0, INFO: 0}
    for f in findings:
        counts[f["status"]] = counts.get(f["status"], 0) + 1
    return {
        "counts": counts,
        "healthy": counts[FAIL] == 0 and counts[WARN] == 0,
        "blocking": counts[FAIL],
    }


if __name__ == "__main__":  # elle inceleme: python -m tools.doctor_gui.checks
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    root = project_root()
    all_f: list[dict] = []
    for s in STEPS:
        all_f += run_step(s["id"], root, want_remote=os.environ.get("ATLAS_NO_NET") != "1")
    print(
        json.dumps({"findings": all_f, "summary": summarize(all_f)}, indent=2, ensure_ascii=False)
    )
