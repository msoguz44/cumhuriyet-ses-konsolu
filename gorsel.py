"""Küçük görsel bileşenler."""

import random

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import QWidget

from tema import RENKLER


class RitimGosterge(QWidget):
    """Çalma sürerken hareket eden, duraklatıldığında donan süs çubukları."""

    def __init__(self, cubuk=14, parent=None):
        super().__init__(parent)
        self._n = cubuk
        self._seviye = [0.12] * cubuk
        self._hedef = [0.12] * cubuk
        self._etkin = False
        self.setMinimumSize(cubuk * 7, 34)
        self._sayac = QTimer(self)
        self._sayac.setInterval(70)
        self._sayac.timeout.connect(self._tik)

    def etkinlestir(self, acik: bool):
        if acik == self._etkin:
            return
        self._etkin = acik
        if acik:
            self._sayac.start()
        else:
            self._sayac.stop()
            self._hedef = [0.16 + 0.05 * ((i % 3) == 1) for i in range(self._n)]
            self._sayac_bir_kere()
        self.update()

    def _sayac_bir_kere(self):
        self._seviye = list(self._hedef)
        self.update()

    def _tik(self):
        for i in range(self._n):
            if random.random() < 0.55:
                orta = 1.0 - abs(i - (self._n - 1) / 2) / self._n
                self._hedef[i] = max(0.15, min(1.0, random.random() * (0.45 + orta * 0.75)))
        for i in range(self._n):
            self._seviye[i] += (self._hedef[i] - self._seviye[i]) * 0.45
        self.update()

    def paintEvent(self, olay):
        b = QPainter(self)
        b.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w = self.width() / self._n
        kalinlik = max(2.0, w * 0.55)
        for i, seviye in enumerate(self._seviye):
            yuk = max(3.0, self.height() * seviye)
            x = i * w + (w - kalinlik) / 2
            y = self.height() - yuk
            gecis = QLinearGradient(0, y, 0, self.height())
            if self._etkin:
                gecis.setColorAt(0.0, QColor(RENKLER["altin"]))
                gecis.setColorAt(1.0, QColor(RENKLER["kirmizi"]))
            else:
                gecis.setColorAt(0.0, QColor("#39425C"))
                gecis.setColorAt(1.0, QColor("#2A3147"))
            b.setBrush(gecis)
            b.setPen(Qt.PenStyle.NoPen)
            b.drawRoundedRect(QRectF(x, y, kalinlik, yuk), kalinlik / 2, kalinlik / 2)
        b.end()
