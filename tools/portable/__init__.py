"""Taşınabilirlik katmanı: klasörü sıkıştırıp başka bir Windows'ta açınca çalışsın.

Üç sorun çözülür:

* **runtimes** — node ve git-bash depo İÇİNDE tutulur; sarmalayıcılar mutlak
  makine yolu (`%LOCALAPPDATA%\\hermes\\node`) yerine `%ROOT%` göreli yol yazar.
* **relocate** — makine/yol değiştiğinde makineye özgü ne varsa yeniden üretilir
  (sarmalayıcılar, ACP kayıtları, profil). Kullanıcı hiçbir sihirbaz açmaz.
* **autoupdate** — ajan güncellemeleri günde bir kez kendiliğinden yapılır;
  panel ikilisi ASLA otomatik güncellenmez (ölçülmüş self-update olayı).
"""
