"""Komut satırı arayüzü.

Örnek:
    atlas-sections i --h 1000 --b 300 --tw 12 --tf 20
    atlas-sections box --h 200 --b 300 --t 10
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from sections.core import SectionError, SectionProperties, box_section, i_section

# Alan -> birim eşlemesi (makine-okur çıktıda birlikte verilir).
_UNITS = {
    "A": "mm2",
    "Iy": "mm4",
    "Iz": "mm4",
    "Wel_y": "mm3",
    "Wel_z": "mm3",
    "Wpl_y": "mm3",
    "weight_kg_m": "kg/m",
}


def _report(p: SectionProperties) -> str:
    return (
        f"A      = {p.A:12.1f} mm²\n"
        f"Iy     = {p.Iy:12.3e} mm⁴\n"
        f"Iz     = {p.Iz:12.3e} mm⁴\n"
        f"Wel_y  = {p.Wel_y:12.3e} mm³\n"
        f"Wel_z  = {p.Wel_z:12.3e} mm³\n"
        f"Wpl_y  = {p.Wpl_y:12.3e} mm³\n"
        f"Ağırlık= {p.weight_kg_m:12.2f} kg/m"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas-sections", description=__doc__)
    sub = parser.add_subparsers(dest="type", required=True)

    p_i = sub.add_parser("i", help="Kaynaklı I-kesit")
    for name in ("h", "b", "tw", "tf"):
        p_i.add_argument(f"--{name}", type=float, required=True, help=f"{name} [mm]")

    p_box = sub.add_parser("box", help="Kutu kesit")
    for name in ("h", "b", "t"):
        p_box.add_argument(f"--{name}", type=float, required=True, help=f"{name} [mm]")

    for p in (p_i, p_box):
        p.add_argument(
            "--json", action="store_true", help="Makine-okur JSON çıktı (birimlerle)"
        )

    args = parser.parse_args(argv)
    # Windows konsolu (cp1254) üstsimge birimleri (mm², mm⁴) kodlayamaz; UTF-8'e sabitle.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if args.type == "i":
            props = i_section(args.h, args.b, args.tw, args.tf)
        else:
            props = box_section(args.h, args.b, args.t)
    except SectionError as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}), file=sys.stderr)
        else:
            print(f"HATA: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = {"type": args.type, "properties": asdict(props), "units": _UNITS}
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(_report(props))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
