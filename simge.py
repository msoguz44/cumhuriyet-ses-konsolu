"""Uygulama simgesi: kırmızı zemin üzerine ay-yıldız, kodla çizilir."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPixmap


def _yildiz(merkez: QPointF, dis: float, ic: float, donme: float = -90.0) -> QPainterPath:
    yol = QPainterPath()
    for i in range(10):
        aci = math.radians(donme + i * 36.0)
        r = dis if i % 2 == 0 else ic
        nokta = QPointF(merkez.x() + r * math.cos(aci), merkez.y() + r * math.sin(aci))
        if i == 0:
            yol.moveTo(nokta)
        else:
            yol.lineTo(nokta)
    yol.closeSubpath()
    return yol


def _cizim(boyut: int) -> QPixmap:
    pm = QPixmap(boyut, boyut)
    pm.fill(Qt.GlobalColor.transparent)
    b = QPainter(pm)
    b.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # yuvarlak köşeli kırmızı zemin
    b.setPen(Qt.PenStyle.NoPen)
    b.setBrush(QBrush(QColor("#E30A17")))
    b.drawRoundedRect(QRectF(0, 0, boyut, boyut), boyut * 0.22, boyut * 0.22)

    # ay: büyük beyaz daireden küçük kırmızı daire çıkarılır
    yol = QPainterPath()
    yol.addEllipse(QRectF(boyut * 0.17, boyut * 0.25, boyut * 0.50, boyut * 0.50))
    kes = QPainterPath()
    kes.addEllipse(QRectF(boyut * 0.29, boyut * 0.29, boyut * 0.42, boyut * 0.42))
    b.setBrush(QBrush(QColor("#FFFFFF")))
    b.drawPath(yol.subtracted(kes))

    # yıldız
    b.drawPath(_yildiz(QPointF(boyut * 0.70, boyut * 0.50), boyut * 0.17, boyut * 0.072))
    b.end()
    return pm


def uygulama_simgesi() -> QIcon:
    simge = QIcon()
    for boyut in (16, 24, 32, 48, 64, 128, 256):
        simge.addPixmap(_cizim(boyut))
    return simge
