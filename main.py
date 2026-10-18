"""
Cumhuriyet Ses Konsolu — 29 Ekim tören/kutlama ses yönetimi
-----------------------------------------------------------
Çalıştırmak için:  python main.py
Gereken paket:     PySide6   (pip install PySide6)
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pencere import AnaPencere
from simge import uygulama_simgesi


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    uygulama = QApplication(sys.argv)
    uygulama.setApplicationName("Cumhuriyet Ses Konsolu")
    uygulama.setOrganizationName("CumhuriyetSes")
    uygulama.setApplicationDisplayName("Cumhuriyet Ses Konsolu")
    uygulama.setWindowIcon(uygulama_simgesi())

    pencere = AnaPencere()
    pencere.show()
    return uygulama.exec()


if __name__ == "__main__":
    sys.exit(main())
