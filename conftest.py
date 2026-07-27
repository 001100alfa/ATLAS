"""Depo kökünü içe-aktarma yoluna alır.

`tools/` bir dağıtım paketi değildir (kurulmaz); araçlar depo kökünden
`python -m tools.<araç>` biçiminde çalıştırılır — `SETUP.cmd` ve `DOCTOR.cmd`
tam olarak bunu yapar. Testler de aynı biçimde import edebilsin diye kök
yolu buraya eklenir.

Neden gerekli: `python -m pytest` çalışma dizinini yola ekler, çıplak `pytest`
EKLEMEZ. İkisi arasındaki bu fark olmadan testler geliştiricinin makinesinde
geçip CI'da "No module named 'tools'" ile düşer.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
