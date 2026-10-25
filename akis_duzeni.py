"""Pencere genişliğine göre kendiliğinden satıra bölen yerleşim (flow layout)."""

from PySide6.QtCore import QMargins, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QSizePolicy


class AkisDuzeni(QLayout):
    def __init__(self, parent=None, bosluk=16, kenar=0):
        super().__init__(parent)
        self._ogeler = []
        self._bosluk = bosluk
        self.setContentsMargins(QMargins(kenar, kenar, kenar, kenar))

    # --- QLayout arayüzü ---
    def addItem(self, oge):
        self._ogeler.append(oge)

    def count(self):
        return len(self._ogeler)

    def itemAt(self, i):
        return self._ogeler[i] if 0 <= i < len(self._ogeler) else None

    def takeAt(self, i):
        if 0 <= i < len(self._ogeler):
            return self._ogeler.pop(i)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, genislik):
        return self._yerlestir(QRect(0, 0, genislik, 0), sadece_olc=True)

    def setGeometry(self, dikdortgen):
        super().setGeometry(dikdortgen)
        self._yerlestir(dikdortgen, sadece_olc=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        boyut = QSize()
        for oge in self._ogeler:
            boyut = boyut.expandedTo(oge.minimumSize())
        kenar = self.contentsMargins()
        return boyut + QSize(kenar.left() + kenar.right(), kenar.top() + kenar.bottom())

    # --- Yerleştirme hesabı ---
    def _yerlestir(self, dikdortgen, sadece_olc):
        kenar = self.contentsMargins()
        alan = dikdortgen.adjusted(kenar.left(), kenar.top(), -kenar.right(), -kenar.bottom())
        x, y, satir_yuksekligi = alan.x(), alan.y(), 0

        for oge in self._ogeler:
            # isVisible() pencere gösterilmeden önce bütün kartlar için False
            # döner; o anda yerleştirme yapılmazsa kartlar üst üste kalırdı.
            # isHidden() yalnızca elle gizlenenler (arama filtresi) için True.
            if oge.widget().isHidden():
                continue
            ebat = oge.sizeHint()
            sonraki = x + ebat.width() + self._bosluk
            if sonraki - self._bosluk > alan.right() and satir_yuksekligi > 0:
                x = alan.x()
                y = y + satir_yuksekligi + self._bosluk
                satir_yuksekligi = 0
                sonraki = x + ebat.width() + self._bosluk
            if not sadece_olc:
                oge.setGeometry(QRect(QPoint(x, y), ebat))
            x = sonraki
            satir_yuksekligi = max(satir_yuksekligi, ebat.height())

        return y + satir_yuksekligi - dikdortgen.y() + kenar.bottom()


class AkisKapsayici:
    """Yardımcı: boyut politikası kısayolu."""

    @staticmethod
    def sabit(widget):
        widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return widget
