"""Ekrandaki müzik kartı (boyutu ölçeklenebilir)."""

from __future__ import annotations

from PySide6.QtCore import QMimeData, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QDrag, QFont, QFontMetrics, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSlider,
    QVBoxLayout, QWidget,
)

from depo import Parca
from tema import oynat_dugme_qss
from yardimci import odagi_kapat, sure_metni

TEMEL_EN = 326
MIME = "application/x-cumhuriyet-parca"
EN_KUCUK_OLCEK = 0.50
EN_BUYUK_OLCEK = 1.40

# Yerleşimin hesaba göre fazladan istediği yükseklik. İlk kart kendini ölçüp
# burayı günceller; böylece hesap, çalışılan sistemin yazı tipine uyar.
_EK_PAY = 0


def kart_olculeri(olcek: float) -> dict:
    """Verilen ölçek için kartın bütün ölçülerini hesaplar.

    Kart küçüldükçe önce dosya adı, sonra süre satırı ve ses sürgüsü gizlenir;
    böylece ekrana çok sayıda kart sığarken kart okunaklı kalır.
    """
    s = max(EN_KUCUK_OLCEK, min(EN_BUYUK_OLCEK, float(olcek)))
    if s >= 0.86:
        mod = "tam"       # her şey görünür
    elif s >= 0.68:
        mod = "orta"      # dosya adı gizlenir
    elif s >= 0.56:
        mod = "mini"      # süre satırı da gizlenir
    else:
        mod = "mikro"     # yalnızca ad, ilerleme, çal ve ayar düğmesi

    ad_px = max(15, round(27 * s))
    dosya_px = max(9, round(11 * s))
    sure_px = max(9, round(12 * s))
    etiket_px = max(8, round(10 * s))
    sira_px = max(9, round(12 * s))

    serit = max(4, round(5 * s))
    ust = max(7, round(11 * s))
    alt = max(7, round(12 * s))
    yan = max(9, round(14 * s))
    bos = max(4, round(7 * s))

    sira_boy = max(16, round(24 * s))
    oynat = max(30, round(44 * s))
    kucuk = max(20, round(32 * s))
    ilerleme = max(4, round(6 * s))

    en = max(150, round(TEMEL_EN * s))
    ad_h = round(ad_px * 1.22) * 2
    dosya_h = round(dosya_px * 1.55)
    zaman_h = round(dosya_px * 1.55)

    boy = serit + ust + sira_boy + bos + ad_h + bos + ilerleme + bos + oynat + alt + _EK_PAY
    if mod == "tam":
        boy += bos + dosya_h
    if mod in ("tam", "orta"):
        boy += bos + zaman_h

    kucuk_adet = 1 if mod == "mikro" else 3
    ses_en = en - 2 * yan - oynat - kucuk_adet * kucuk - (kucuk_adet + 1) * bos
    return {
        "olcek": s, "mod": mod, "en": en, "boy": boy,
        "ad_px": ad_px, "dosya_px": dosya_px, "sure_px": sure_px,
        "etiket_px": etiket_px, "sira_px": sira_px,
        "serit": serit, "ust": ust, "alt": alt, "yan": yan, "bos": bos,
        "sira_boy": sira_boy, "oynat": oynat, "kucuk": kucuk,
        "ilerleme": ilerleme, "ad_h": ad_h, "dosya_h": dosya_h, "zaman_h": zaman_h,
        "ses_en": ses_en if (ses_en >= 40 and mod != "mikro") else 0,
    }


class ParcaKart(QFrame):
    oynat_istendi = Signal(str)
    duraklat_istendi = Signal(str)
    durdur_istendi = Signal(str)
    dongu_degisti = Signal(str, bool)
    kazanc_degisti = Signal(str, float)
    menu_istendi = Signal(str, QPoint)
    tasindi = Signal(str, str)        # kaynak_id, hedef_id

    def __init__(self, parca: Parca, sira: int, olcek: float = 1.0, parent=None):
        super().__init__(parent)
        self.parca = parca
        self.olcu = kart_olculeri(olcek)
        self.setObjectName("Kart")
        self.setAcceptDrops(True)
        self.setProperty("durum", "bos")
        self.setProperty("hedef", "false")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._bas_nokta = QPoint()
        self._durum = "bos"

        kok = QVBoxLayout(self)
        kok.setContentsMargins(0, 0, 0, 0)
        kok.setSpacing(0)

        self._serit = QFrame(self)
        kok.addWidget(self._serit)

        self.govde = QVBoxLayout()
        kok.addLayout(self.govde)

        # --- 1. satır: sıra no · etiket · süre
        ust = QHBoxLayout()
        self._ust_satir = ust
        self.lbl_sira = QLabel(str(sira))
        self.lbl_sira.setObjectName("KartSira")
        self.lbl_sira.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ust.addWidget(self.lbl_sira)
        self.lbl_etiket = QLabel("")
        self.lbl_etiket.setObjectName("KartEtiket")
        ust.addWidget(self.lbl_etiket)
        ust.addStretch(1)
        self.lbl_sure = QLabel("--:--")
        self.lbl_sure.setObjectName("KartSure")
        ust.addWidget(self.lbl_sure)
        self.govde.addLayout(ust)

        # --- 2. satır: müzik adı (en öne çıkan yazı)
        self.lbl_ad = QLabel("")
        self.lbl_ad.setObjectName("KartAd")
        self.lbl_ad.setWordWrap(True)
        self.lbl_ad.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.govde.addWidget(self.lbl_ad)

        self.lbl_dosya = QLabel("")
        self.lbl_dosya.setObjectName("KartDosya")
        self.govde.addWidget(self.lbl_dosya)

        self.govde.addStretch(1)

        # --- 3. satır: ilerleme + zaman
        self.ilerleme = QProgressBar()
        self.ilerleme.setTextVisible(False)
        self.ilerleme.setRange(0, 1000)
        self.ilerleme.setValue(0)
        self.govde.addWidget(self.ilerleme)

        self.zaman_kutu = QWidget()
        zaman = QHBoxLayout(self.zaman_kutu)
        zaman.setContentsMargins(0, 0, 0, 0)
        zaman.setSpacing(0)
        self.lbl_gecen = QLabel("0:00")
        self.lbl_gecen.setObjectName("KartDosya")
        self.lbl_kalan = QLabel("")
        self.lbl_kalan.setObjectName("KartDosya")
        zaman.addWidget(self.lbl_gecen)
        zaman.addStretch(1)
        zaman.addWidget(self.lbl_kalan)
        self.govde.addWidget(self.zaman_kutu)

        # --- 4. satır: düğmeler
        self.alt_satir = QHBoxLayout()
        self.btn_oynat = QPushButton("▶")
        self.btn_oynat.setObjectName("KartOynat")
        self.btn_oynat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_oynat.setToolTip("Çal / Duraklat")
        self.btn_oynat.clicked.connect(self._oynat_tiklandi)
        self.alt_satir.addWidget(self.btn_oynat)

        self.btn_durdur = QPushButton("■")
        self.btn_durdur.setObjectName("KartKucuk")
        self.btn_durdur.setToolTip("Durdur (yumuşak kıs)")
        self.btn_durdur.clicked.connect(lambda: self.durdur_istendi.emit(self.parca.id))
        self.alt_satir.addWidget(self.btn_durdur)

        self.btn_dongu = QPushButton("↻")
        self.btn_dongu.setObjectName("KartKucuk")
        self.btn_dongu.setCheckable(True)
        self.btn_dongu.setToolTip("Sürekli tekrar (döngü)")
        self.btn_dongu.toggled.connect(lambda a: self.dongu_degisti.emit(self.parca.id, a))
        self.alt_satir.addWidget(self.btn_dongu)

        self.ses = QSlider(Qt.Orientation.Horizontal)
        self.ses.setObjectName("KartSes")
        self.ses.setRange(0, 150)
        self.ses.setToolTip("Bu parçanın ses düzeyi")
        self.ses.valueChanged.connect(
            lambda v: self.kazanc_degisti.emit(self.parca.id, v / 100.0))
        self.alt_satir.addWidget(self.ses)

        self.btn_menu = QPushButton("⋯")
        self.btn_menu.setObjectName("KartKucuk")
        self.btn_menu.setToolTip("Kart ayarları")
        self.btn_menu.clicked.connect(
            lambda: self.menu_istendi.emit(
                self.parca.id, self.btn_menu.mapToGlobal(QPoint(0, self.btn_menu.height()))))
        self.alt_satir.addWidget(self.btn_menu)
        self.govde.addLayout(self.alt_satir)

        odagi_kapat(self, QPushButton, QSlider, QProgressBar)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.olcek_ayarla(olcek)
        self.tazele(parca, sira)

    # --------------------------------------------------------------- ölçekleme
    def olcek_ayarla(self, olcek: float):
        global _EK_PAY
        o = kart_olculeri(olcek)
        self.olcu = o
        self.setFixedWidth(o["en"])
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)

        self._serit.setFixedHeight(o["serit"])
        self.govde.setContentsMargins(o["yan"], o["ust"], o["yan"], o["alt"])
        self.govde.setSpacing(o["bos"])
        self._ust_satir.setSpacing(max(4, round(o["bos"] * 0.9)))
        self.alt_satir.setSpacing(o["bos"])

        self._yazi(self.lbl_ad, o["ad_px"])
        self._yazi(self.lbl_dosya, o["dosya_px"])
        self._yazi(self.lbl_gecen, o["dosya_px"])
        self._yazi(self.lbl_kalan, o["dosya_px"])
        self._yazi(self.lbl_sure, o["sure_px"])
        self._yazi(self.lbl_etiket, o["etiket_px"])
        self._yazi(self.lbl_sira, o["sira_px"])

        self.lbl_ad.setFixedHeight(o["ad_h"])
        self.lbl_dosya.setFixedHeight(o["dosya_h"])
        self.zaman_kutu.setFixedHeight(o["zaman_h"])
        self.lbl_sira.setFixedSize(o["sira_boy"], o["sira_boy"])
        self.lbl_sira.setStyleSheet(f"border-radius: {o['sira_boy'] // 2}px;")
        self.ilerleme.setFixedHeight(o["ilerleme"])

        self.btn_oynat.setFixedSize(o["oynat"], o["oynat"])
        self.btn_oynat.setStyleSheet(
            oynat_dugme_qss(o["oynat"] // 2, max(11, round(o["oynat"] * 0.40))))
        for dugme in (self.btn_durdur, self.btn_dongu, self.btn_menu):
            dugme.setFixedSize(o["kucuk"], o["kucuk"])
            self._yazi(dugme, max(10, round(o["kucuk"] * 0.42)))

        self.lbl_dosya.setVisible(o["mod"] == "tam")
        self.zaman_kutu.setVisible(o["mod"] in ("tam", "orta"))
        self.btn_durdur.setVisible(o["mod"] != "mikro")
        self.btn_dongu.setVisible(o["mod"] != "mikro")
        self.ses.setVisible(o["ses_en"] > 0)
        if o["ses_en"] > 0:
            self.ses.setFixedWidth(o["ses_en"])

        # Yerleşimin gerçekte istediği yüksekliği ölç; hesap kısa kalıyorsa düzelt.
        self.layout().invalidate()
        self.layout().activate()
        gerek = self.layout().minimumSize().height()
        if gerek > o["boy"] and _EK_PAY < 60:
            _EK_PAY = min(60, _EK_PAY + (gerek - o["boy"]))
            o = kart_olculeri(olcek)
            self.olcu = o
        self.setFixedHeight(max(o["boy"], gerek))

        self.tazele(self.parca, int(self.lbl_sira.text() or 1))

    @staticmethod
    def _yazi(bilesen, piksel: int):
        yazi: QFont = bilesen.font()
        yazi.setPixelSize(piksel)
        bilesen.setFont(yazi)

    # --------------------------------------------------------------- görünüm
    def _ad_yaz(self, metin: str):
        """Müzik adını, ayrılan kutuya sığan EN BÜYÜK punto ile yazar."""
        o = self.olcu
        genislik = o["en"] - 2 * o["yan"]
        # Kısa adlar kutuyu doldurabilsin diye tavan, taban puntonun üstünde
        tavan = round(o["ad_px"] * 1.45)
        en_az = max(11, int(o["ad_px"] * 0.60))
        yazi: QFont = self.lbl_ad.font()
        for piksel in range(tavan, en_az - 1, -1):
            yazi.setPixelSize(piksel)
            kutu = QFontMetrics(yazi).boundingRect(
                QRect(0, 0, genislik, 10000),
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft, metin)
            if kutu.height() <= o["ad_h"]:
                break
        self.lbl_ad.setFont(yazi)
        self.lbl_ad.setText(metin)

    def tazele(self, parca: Parca, sira: int):
        self.parca = parca
        self.lbl_sira.setText(str(sira))
        self._ad_yaz(parca.ad)
        self.lbl_dosya.setText(self._sigdir(parca.dosya_adi))

        sure = sure_metni(parca.sure_ms) if parca.sure_ms else "--:--"
        if parca.baslangic_ms:
            sure = "⏱ " + sure_metni(parca.baslangic_ms) + "  •  " + sure
            self.lbl_sure.setToolTip(
                "Bu parça " + sure_metni(parca.baslangic_ms) + " noktasından başlayacak")
        else:
            self.lbl_sure.setToolTip("")
        self.lbl_sure.setText(sure)

        self._serit.setStyleSheet(
            f"background-color: {parca.renk};"
            "border-top-left-radius: 15px; border-top-right-radius: 15px;")
        if parca.etiket and self.olcu["mod"] in ("tam", "orta"):
            self.lbl_etiket.setText(parca.etiket.upper())
            self.lbl_etiket.setStyleSheet(f"background-color: {parca.renk};")
            self.lbl_etiket.show()
        else:
            self.lbl_etiket.hide()

        self.ses.blockSignals(True)
        self.ses.setValue(int(round(parca.kazanc * 100)))
        self.ses.blockSignals(False)
        self.btn_dongu.blockSignals(True)
        self.btn_dongu.setChecked(parca.dongu)
        self.btn_dongu.blockSignals(False)

        if not parca.var_mi:
            self.lbl_dosya.setText("⚠ Dosya bulunamadı")
            self.lbl_dosya.setObjectName("KartUyari")
            self.durum_ayarla("eksik")
        else:
            self.lbl_dosya.setObjectName("KartDosya")
            if self._durum == "eksik":
                self.durum_ayarla("bos")
        self.lbl_dosya.style().unpolish(self.lbl_dosya)
        self.lbl_dosya.style().polish(self.lbl_dosya)
        self._yazi(self.lbl_dosya, self.olcu["dosya_px"])

        ipucu = f"{parca.ad}\n{parca.yol}"
        if self.olcu["mod"] != "tam":
            ipucu = f"{parca.ad}\n{sure_metni(parca.sure_ms)}\n{parca.yol}"
        self.setToolTip(ipucu)

    def _sigdir(self, metin: str) -> str:
        olcu = QFontMetrics(self.lbl_dosya.font())
        return olcu.elidedText(metin, Qt.TextElideMode.ElideMiddle,
                               self.olcu["en"] - 2 * self.olcu["yan"])

    def durum_ayarla(self, durum: str):
        """durum: 'bos' | 'calisiyor' | 'duraklatildi' | 'eksik'"""
        self._durum = durum
        self.setProperty("durum", durum)
        self.style().unpolish(self)
        self.style().polish(self)
        self.btn_oynat.setText("❙❙" if durum == "calisiyor" else "▶")
        if durum in ("bos", "eksik"):
            self.ilerleme.setValue(0)
            self.lbl_gecen.setText("0:00")
            self.lbl_kalan.setText("")

    def ilerleme_ayarla(self, konum_ms: int, sure_ms: int):
        if sure_ms > 0:
            self.ilerleme.setValue(int(min(1000, konum_ms / sure_ms * 1000)))
            self.lbl_kalan.setText("-" + sure_metni(max(0, sure_ms - konum_ms)))
        self.lbl_gecen.setText(sure_metni(konum_ms))

    def hedef_vurgu(self, acik: bool):
        self.setProperty("hedef", "true" if acik else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    # --------------------------------------------------------------- olaylar
    def _oynat_tiklandi(self):
        if self._durum == "calisiyor":
            self.duraklat_istendi.emit(self.parca.id)
        else:
            self.oynat_istendi.emit(self.parca.id)

    def mouseDoubleClickEvent(self, olay):
        self.oynat_istendi.emit(self.parca.id)

    def contextMenuEvent(self, olay):
        self.menu_istendi.emit(self.parca.id, olay.globalPos())

    def mousePressEvent(self, olay):
        if olay.button() == Qt.MouseButton.LeftButton:
            self._bas_nokta = olay.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(olay)

    def mouseReleaseEvent(self, olay):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(olay)

    def mouseMoveEvent(self, olay):
        if not (olay.buttons() & Qt.MouseButton.LeftButton):
            return
        if (olay.position().toPoint() - self._bas_nokta).manhattanLength() < 18:
            return
        veri = QMimeData()
        veri.setData(MIME, self.parca.id.encode("utf-8"))
        surukle = QDrag(self)
        surukle.setMimeData(veri)
        onizleme = QPixmap(self.size())
        onizleme.setDevicePixelRatio(self.devicePixelRatioF())
        self.render(onizleme)
        kucuk = onizleme.scaled(
            max(140, int(self.width() * 0.6)), max(90, int(self.height() * 0.6)),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        surukle.setPixmap(kucuk)
        surukle.setHotSpot(QPoint(kucuk.width() // 2, kucuk.height() // 2))
        surukle.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def dragEnterEvent(self, olay):
        if olay.mimeData().hasFormat(MIME):
            kaynak = bytes(olay.mimeData().data(MIME)).decode("utf-8")
            if kaynak != self.parca.id:
                self.hedef_vurgu(True)
                olay.acceptProposedAction()
                return
        olay.ignore()

    def dragMoveEvent(self, olay):
        if olay.mimeData().hasFormat(MIME):
            olay.acceptProposedAction()

    def dragLeaveEvent(self, olay):
        self.hedef_vurgu(False)

    def dropEvent(self, olay):
        self.hedef_vurgu(False)
        if olay.mimeData().hasFormat(MIME):
            kaynak = bytes(olay.mimeData().data(MIME)).decode("utf-8")
            if kaynak != self.parca.id:
                self.tasindi.emit(kaynak, self.parca.id)
                olay.acceptProposedAction()
