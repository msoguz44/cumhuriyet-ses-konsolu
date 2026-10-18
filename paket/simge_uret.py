"""Uygulama simgesini dosyaya yazar: app.ico (Windows), app.icns (mac), app.png (Linux).

Kullanım:  python paket/simge_uret.py
Simge kodla çizilir (bkz. simge.py), dışarıdan dosya gerekmez.
"""

import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from PySide6.QtWidgets import QApplication   # noqa: E402
from simge import _cizim                     # noqa: E402


def main() -> int:
    QApplication(sys.argv)
    hedef = Path(__file__).resolve().parent
    buyuk = _cizim(1024)
    orta = _cizim(256)

    yazilan = []
    for ad, pixmap in (("app.png", buyuk), ("app.ico", orta), ("app.icns", buyuk)):
        yol = hedef / ad
        if pixmap.save(str(yol)):
            yazilan.append(f"{ad} ({yol.stat().st_size // 1024} KB)")
        else:
            print(f"UYARI: {ad} yazılamadı.")

    # macOS'ta çok çözünürlüklü, standart bir .icns üret (varsa iconutil ile)
    if sys.platform == "darwin" and shutil.which("iconutil"):
        kume = hedef / "app.iconset"
        shutil.rmtree(kume, ignore_errors=True)
        kume.mkdir()
        for boyut in (16, 32, 128, 256, 512):
            _cizim(boyut).save(str(kume / f"icon_{boyut}x{boyut}.png"))
            _cizim(boyut * 2).save(str(kume / f"icon_{boyut}x{boyut}@2x.png"))
        if subprocess.run(["iconutil", "-c", "icns", str(kume),
                           "-o", str(hedef / "app.icns")]).returncode == 0:
            yazilan.append("app.icns (iconutil ile çok çözünürlüklü)")
        shutil.rmtree(kume, ignore_errors=True)

    print("Yazılan simgeler:", ", ".join(yazilan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
