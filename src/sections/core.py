"""Kesit özellik hesaplayıcı çekirdeği.

Birim sistemi: SI-mm (mm, mm², mm³, mm⁴). Ağırlık kg/m.
Malzeme yoğunluğu: çelik 7850 kg/m³ (EN 1991-1-1).
Değişken adları EN 1993-1-1 gösterimiyle uyumludur.
"""

from __future__ import annotations

from dataclasses import dataclass

STEEL_DENSITY_KG_M3: float = 7850.0


class SectionError(ValueError):
    """Geçersiz kesit geometrisi."""


@dataclass(frozen=True, slots=True)
class SectionProperties:
    """Hesaplanmış kesit özellikleri (SI-mm).

    Attributes:
        A: Alan [mm²]
        Iy: Güçlü eksen atalet momenti [mm⁴]
        Iz: Zayıf eksen atalet momenti [mm⁴]
        Wel_y: Güçlü eksen elastik mukavemet momenti [mm³]
        Wel_z: Zayıf eksen elastik mukavemet momenti [mm³]
        Wpl_y: Güçlü eksen plastik mukavemet momenti [mm³]
        weight_kg_m: Birim boy ağırlık [kg/m]
    """

    A: float
    Iy: float
    Iz: float
    Wel_y: float
    Wel_z: float
    Wpl_y: float
    weight_kg_m: float


def _require_positive(**dims: float) -> None:
    for name, value in dims.items():
        if value <= 0:
            raise SectionError(f"{name} pozitif olmalı, verilen: {value}")


def i_section(h: float, b: float, tw: float, tf: float) -> SectionProperties:
    """Çift simetrik kaynaklı I-kesit (fillet/radius yok).

    Args:
        h: Toplam yükseklik [mm]
        b: Flanş genişliği [mm]
        tw: Gövde kalınlığı [mm]
        tf: Flanş kalınlığı [mm]

    Raises:
        SectionError: Boyutlar geometrik olarak tutarsızsa.
    """
    _require_positive(h=h, b=b, tw=tw, tf=tf)
    hw = h - 2.0 * tf  # gövde net yüksekliği [mm]
    if hw <= 0:
        raise SectionError(f"Gövde yüksekliği <= 0: h={h}, tf={tf}")
    if tw >= b:
        raise SectionError(f"Gövde kalınlığı flanş genişliğini aşamaz: tw={tw}, b={b}")

    A = 2.0 * b * tf + hw * tw

    # Iy: flanşlar (paralel eksen teoremi) + gövde
    d_f = (h - tf) / 2.0  # flanş merkezi - tarafsız eksen mesafesi [mm]
    Iy = 2.0 * (b * tf**3 / 12.0 + b * tf * d_f**2) + tw * hw**3 / 12.0
    Iz = 2.0 * (tf * b**3 / 12.0) + hw * tw**3 / 12.0

    Wel_y = Iy / (h / 2.0)
    Wel_z = Iz / (b / 2.0)
    # Plastik: flanş kuvvet çifti + gövde katkısı
    Wpl_y = b * tf * (h - tf) + tw * hw**2 / 4.0

    weight = A * 1e-6 * STEEL_DENSITY_KG_M3  # mm² -> m², kg/m
    return SectionProperties(A, Iy, Iz, Wel_y, Wel_z, Wpl_y, weight)


def box_section(h: float, b: float, t: float) -> SectionProperties:
    """Üniform et kalınlıklı dikdörtgen kutu kesit.

    Args:
        h: Dış yükseklik [mm]
        b: Dış genişlik [mm]
        t: Et kalınlığı [mm]

    Raises:
        SectionError: Et kalınlığı iç boşluğu yok ediyorsa.
    """
    _require_positive(h=h, b=b, t=t)
    hi, bi = h - 2.0 * t, b - 2.0 * t
    if hi <= 0 or bi <= 0:
        raise SectionError(f"Et kalınlığı çok büyük: h={h}, b={b}, t={t}")

    A = b * h - bi * hi
    Iy = (b * h**3 - bi * hi**3) / 12.0
    Iz = (h * b**3 - hi * bi**3) / 12.0
    Wel_y = Iy / (h / 2.0)
    Wel_z = Iz / (b / 2.0)
    Wpl_y = (b * h**2 - bi * hi**2) / 4.0

    weight = A * 1e-6 * STEEL_DENSITY_KG_M3
    return SectionProperties(A, Iy, Iz, Wel_y, Wel_z, Wpl_y, weight)
