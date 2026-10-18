"""Ana pencere: üst şerit, kart tahtası ve alt ses konsolu."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox, QProgressBar,
    QPushButton, QScrollArea, QSlider, QVBoxLayout, QWidget,
)

import depo
from akis_duzeni import AkisDuzeni
from depo import Parca, Program, SureBulucu
from gorsel import RitimGosterge
from kart import (EN_BUYUK_OLCEK, EN_KUCUK_OLCEK, MIME, ParcaKart,
                  kart_olculeri)
from ses_motoru import SesMotoru
from simge import uygulama_simgesi
from tema import KART_RENKLERI, QSS, RENKLER
from yardimci import odagi_kapat, sure_metni

KENAR = 18      # kart tahtasının kenar boşluğu
BOSLUK = 16     # kartlar arası boşluk

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

HAZIR_ETIKETLER = [
    "", "İstiklal Marşı", "Saygı Duruşu", "Açılış", "Kapanış", "Şiir Fonu",
    "Dans / Gösteri", "Ara Müziği", "Alkış", "Marş", "Efekt", "Anons",
]

SES_FILTRESI = (
    "Ses dosyaları (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.wma *.aiff *.opus);;"
    "Tüm dosyalar (*.*)"
)

KISAYOLLAR = [
    ("Boşluk", "Çalan parçayı duraklat / devam ettir"),
    ("1 - 9, 0", "O sıradaki kartı çal (0 = 10. kart)"),
    ("Esc", "ACİL: sesi yumuşakça kıs ve durdur"),
    ("K", "Anında kes (fade yok)"),
    ("N / P", "Sonraki / önceki parçaya geç"),
    ("← / →", "5 saniye geri / ileri sar"),
    ("Shift + ← / →", "30 saniye geri / ileri sar"),
    ("↑ / ↓", "Ana sesi %5 arttır / azalt"),
    ("Ctrl + O", "Müzik dosyası ekle"),
    ("Ctrl + Shift + O", "Klasör ekle"),
    ("Ctrl + F", "Arama kutusuna git"),
    ("Ctrl + S", "Programı yedek dosyaya kaydet"),
    ("Ctrl + +  /  −", "Kartları büyüt / küçült"),
    ("Ctrl + 0", "Kart boyutunu varsayılana döndür"),
    ("Ctrl + Shift + F", "Bütün kartları ekrana sığdır"),
    ("F11", "Tam ekran aç / kapat"),
    ("F1", "Bu yardım penceresi"),
]


class KartTahtasi(QWidget):
    """Kartların durduğu alan. Boş bir yere bırakılan kart listenin sonuna gider."""

    sona_birakildi = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Kok")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, olay):
        if olay.mimeData().hasFormat(MIME):
            olay.acceptProposedAction()

    def dragMoveEvent(self, olay):
        if olay.mimeData().hasFormat(MIME):
            olay.acceptProposedAction()

    def dropEvent(self, olay):
        if olay.mimeData().hasFormat(MIME):
            self.sona_birakildi.emit(bytes(olay.mimeData().data(MIME)).decode("utf-8"))
            olay.acceptProposedAction()


class YardimPenceresi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kısayollar ve İpuçları")
        self.setMinimumWidth(560)
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(26, 22, 26, 22)
        duzen.setSpacing(14)

        baslik = QLabel("Klavye Kısayolları")
        baslik.setObjectName("YardimBaslik")
        duzen.addWidget(baslik)

        izgara = QGridLayout()
        izgara.setHorizontalSpacing(18)
        izgara.setVerticalSpacing(9)
        for sira, (tus, aciklama) in enumerate(KISAYOLLAR):
            etiket_tus = QLabel(tus)
            etiket_tus.setObjectName("YardimTus")
            etiket_tus.setAlignment(Qt.AlignmentFlag.AlignCenter)
            aciklama_lbl = QLabel(aciklama)
            aciklama_lbl.setObjectName("YardimSatir")
            izgara.addWidget(etiket_tus, sira, 0)
            izgara.addWidget(aciklama_lbl, sira, 1)
        izgara.setColumnStretch(1, 1)
        duzen.addLayout(izgara)

        ipucu = QLabel(
            "İpuçları:\n"
            "•  Dosyaları ya da klasörleri doğrudan pencereye sürükleyip bırakabilirsiniz.\n"
            "•  Kartları tutup başka bir kartın üzerine sürükleyerek sırayı değiştirin;\n"
            "   boş alana bırakılan kart listenin sonuna gider.\n"
            "•  “☰ Menü → Kart boyutu” ile kartları büyütüp küçültebilir, bütün kartları\n"
            "   ya da seçtiğiniz sayıda kartı tek ekrana sığdırabilirsiniz.\n"
            "•  Kartın sağ alt köşesindeki ⋯ düğmesi (ya da sağ tık) ile ad, etiket,\n"
            "   renk, başlangıç noktası ayarlanır.\n"
            "•  Her kartın kendi ses düzeyi vardır; sahnede konuşma üstüne fon müziği\n"
            "   çalarken bunu %30-40 seviyesine almak işinizi kolaylaştırır.\n"
            "•  Program kendiliğinden kaydedilir; bilgisayar kapansa da listeniz kaybolmaz."
        )
        ipucu.setObjectName("YardimSatir")
        duzen.addWidget(ipucu)

        kapat = QPushButton("Anladım")
        kapat.setObjectName("Birincil")
        kapat.clicked.connect(self.accept)
        duzen.addWidget(kapat, alignment=Qt.AlignmentFlag.AlignRight)


class AnaPencere(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Kok")
        self.setWindowTitle("Cumhuriyet Ses Konsolu — 29 Ekim")
        self.setMinimumSize(1060, 720)
        self.resize(1360, 880)
        self.setAcceptDrops(True)
        self.setStyleSheet(QSS)

        self.program: Program = depo.yukle()
        self.kartlar: dict[str, ParcaKart] = {}
        self._suruklenen_seek = False
        self._olcek = max(EN_KUCUK_OLCEK, min(EN_BUYUK_OLCEK, self.program.olcek))
        self._sigdir_hedef = self.program.sigdir or ""

        self.motor = SesMotoru(self)
        self.motor.fade_ms = self.program.fade_ms
        self.motor.ana_ses_ayarla(self.program.ana_ses)

        self.sure_bulucu = SureBulucu(self)
        self.sure_bulucu.bulundu.connect(self._sure_geldi)

        self._kayit_zamani = QTimer(self)
        self._kayit_zamani.setSingleShot(True)
        self._kayit_zamani.setInterval(700)
        self._kayit_zamani.timeout.connect(self._kaydet)

        self._yeniden_sigdir_zamani = QTimer(self)
        self._yeniden_sigdir_zamani.setSingleShot(True)
        self._yeniden_sigdir_zamani.setInterval(140)
        self._yeniden_sigdir_zamani.timeout.connect(self._sigdiri_yenile)

        self._bildirim_zamani = QTimer(self)
        self._bildirim_zamani.setSingleShot(True)
        self._bildirim_zamani.timeout.connect(lambda: self.lbl_bildirim.setText(""))

        self._arayuz_kur()
        self._kisayollar_kur()
        self._motor_bagla()
        self._kartlari_kur()
        self._saat_kur()
        self._fade_degisti(self.fade_surgu.value())
        self.olcek_uygula(self._olcek)
        self._konsol_tazele()

    # =================================================================== ARAYÜZ
    def _arayuz_kur(self):
        kok = QVBoxLayout(self)
        kok.setContentsMargins(0, 0, 0, 0)
        kok.setSpacing(0)
        kok.addWidget(self._ust_serit())
        kok.addWidget(self._tahta(), 1)
        kok.addWidget(self._alt_konsol())

        # Klavye kısayolları her zaman pencereye ulaşsın (arama kutusu hariç)
        odagi_kapat(self, QPushButton, QSlider, QCheckBox, QScrollArea)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ---------------------------------------------------------------- üst şerit
    def _ust_serit(self) -> QFrame:
        """Tek satırlık ince şerit: her şey “Menü” altında, kartlara yer kalsın."""
        serit = QFrame()
        serit.setObjectName("UstSerit")
        serit.setFixedHeight(56)
        duzen = QHBoxLayout(serit)
        duzen.setContentsMargins(KENAR, 7, KENAR, 7)
        duzen.setSpacing(9)

        rozet = QLabel()
        rozet.setPixmap(uygulama_simgesi().pixmap(26, 26))
        rozet.setToolTip("29 Ekim Cumhuriyet Bayramı · Ses Yönetim Konsolu")
        duzen.addWidget(rozet)

        btn_ekle = QPushButton("＋  Müzik Ekle")
        btn_ekle.setObjectName("Birincil")
        btn_ekle.setToolTip("Müzik dosyası ekle (Ctrl+O)")
        btn_ekle.clicked.connect(self.muzik_ekle)
        duzen.addWidget(btn_ekle)

        self.btn_menu = QPushButton("\u2630  Menü")
        self.btn_menu.setToolTip("Bütün ayarlar ve işlemler")
        self.btn_menu.clicked.connect(self._ana_menu)
        duzen.addWidget(self.btn_menu)

        self.arama = QLineEdit()
        self.arama.setPlaceholderText("Ara…")
        self.arama.setClearButtonEnabled(True)
        self.arama.setFixedWidth(168)
        self.arama.textChanged.connect(self._filtre_uygula)
        duzen.addWidget(self.arama)

        self.lbl_bildirim = QLabel("")
        self.lbl_bildirim.setObjectName("MiniEtiket")
        duzen.addWidget(self.lbl_bildirim, 1)

        self.lbl_ozet = QLabel("")
        self.lbl_ozet.setObjectName("MiniEtiket")
        self.lbl_ozet.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        duzen.addWidget(self.lbl_ozet)

        self.lbl_saat = QLabel("--:--:--")
        self.lbl_saat.setObjectName("Saat")
        self.lbl_saat.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        duzen.addWidget(self.lbl_saat)
        return serit

    # ------------------------------------------------------------------- tahta
    def _tahta(self) -> QWidget:
        sarmal = QWidget()
        duzen = QVBoxLayout(sarmal)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.setSpacing(0)

        self.kaydirma = QScrollArea()
        self.kaydirma.setWidgetResizable(True)
        self.kaydirma.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tahta = KartTahtasi()
        self.tahta.sona_birakildi.connect(self._sona_tasi)
        self.akis = AkisDuzeni(self.tahta, bosluk=BOSLUK, kenar=KENAR)
        self.tahta.setLayout(self.akis)
        self.kaydirma.setWidget(self.tahta)
        duzen.addWidget(self.kaydirma, 1)

        # boş ekran bilgisi
        self.bos_kutu = QWidget()
        bos_duzen = QVBoxLayout(self.bos_kutu)
        bos_duzen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bos_duzen.setSpacing(10)
        simge = QLabel("♫")
        simge.setStyleSheet("font-size: 64px; color: #2C3348;")
        simge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b1 = QLabel("Henüz müzik eklenmedi")
        b1.setObjectName("BosBaslik")
        b1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b2 = QLabel("Müzik dosyalarını buraya sürükleyip bırakın\n"
                    "ya da yukarıdaki “Müzik Ekle” düğmesini kullanın.")
        b2.setObjectName("BosYazi")
        b2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bos_duzen.addWidget(simge)
        bos_duzen.addWidget(b1)
        bos_duzen.addWidget(b2)
        duzen.addWidget(self.bos_kutu, 1)
        return sarmal

    # -------------------------------------------------------------- alt konsol
    def _alt_konsol(self) -> QFrame:
        konsol = QFrame()
        konsol.setObjectName("AltKonsol")
        konsol.setFixedHeight(126)
        duzen = QHBoxLayout(konsol)
        duzen.setContentsMargins(KENAR, 8, KENAR, 9)
        duzen.setSpacing(18)

        # --- sol: ritim göstergesi
        self.ritim = RitimGosterge(12)
        self.ritim.setFixedSize(78, 44)
        sol = QVBoxLayout()
        sol.addStretch(1)
        sol.addWidget(self.ritim)
        sol.addStretch(1)
        duzen.addLayout(sol)

        # --- orta: şimdi çalan + sürgü
        orta = QVBoxLayout()
        orta.setSpacing(3)

        ust = QHBoxLayout()
        self.lbl_simdi_etiket = QLabel("ŞİMDİ ÇALIYOR")
        self.lbl_simdi_etiket.setObjectName("SimdiEtiket")
        ust.addWidget(self.lbl_simdi_etiket)
        ust.addStretch(1)
        self.lbl_siradaki = QLabel("")
        self.lbl_siradaki.setObjectName("SiradakiAd")
        ust.addWidget(self.lbl_siradaki)
        orta.addLayout(ust)

        self.lbl_simdi_ad = QLabel("—")
        self.lbl_simdi_ad.setObjectName("SimdiAd")
        orta.addWidget(self.lbl_simdi_ad)

        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 1000)
        self.seek.setValue(0)
        self.seek.sliderPressed.connect(lambda: setattr(self, "_suruklenen_seek", True))
        self.seek.sliderReleased.connect(self._seek_birak)
        self.seek.sliderMoved.connect(self._seek_onizle)
        orta.addWidget(self.seek)

        zaman = QHBoxLayout()
        self.lbl_gecen = QLabel("0:00")
        self.lbl_gecen.setObjectName("Gecen")
        self.lbl_toplam = QLabel("0:00")
        self.lbl_toplam.setObjectName("MiniEtiket")
        zaman.addWidget(self.lbl_gecen)
        zaman.addStretch(1)
        zaman.addWidget(self.lbl_toplam)
        orta.addLayout(zaman)
        duzen.addLayout(orta, 1)

        # --- kalan süre
        kalan_kutu = QVBoxLayout()
        kalan_kutu.setSpacing(0)
        kalan_etiket = QLabel("KALAN")
        kalan_etiket.setObjectName("KalanEtiket")
        kalan_etiket.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_kalan = QLabel("0:00")
        self.lbl_kalan.setObjectName("Kalan")
        self.lbl_kalan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kalan_kutu.addStretch(1)
        kalan_kutu.addWidget(kalan_etiket)
        kalan_kutu.addWidget(self.lbl_kalan)
        kalan_kutu.addStretch(1)
        duzen.addLayout(kalan_kutu)

        # --- denetimler
        denetim = QVBoxLayout()
        denetim.setSpacing(6)

        dugmeler = QHBoxLayout()
        dugmeler.setSpacing(8)
        btn_onceki = QPushButton("⏮")
        btn_onceki.setToolTip("Önceki parça (P)")
        btn_onceki.clicked.connect(lambda: self.komsu_cal(-1))
        self.btn_oynat = QPushButton("▶")
        self.btn_oynat.setObjectName("Birincil")
        self.btn_oynat.setFixedWidth(74)
        self.btn_oynat.setToolTip("Çal / Duraklat (Boşluk)")
        self.btn_oynat.clicked.connect(self.duraklat_devam)
        btn_sonraki = QPushButton("⏭")
        btn_sonraki.setToolTip("Sonraki parça (N)")
        btn_sonraki.clicked.connect(lambda: self.komsu_cal(1))
        btn_dur = QPushButton("■  DURDUR")
        btn_dur.setObjectName("Panik")
        btn_dur.setToolTip("Yumuşakça kıs ve durdur (Esc)")
        btn_dur.clicked.connect(lambda: self.motor.durdur())
        for b in (btn_onceki, self.btn_oynat, btn_sonraki, btn_dur):
            dugmeler.addWidget(b)
        denetim.addLayout(dugmeler)

        ayar = QHBoxLayout()
        ayar.setSpacing(10)
        ayar.addWidget(QLabel("\U0001F50A"))
        self.ses_surgu = QSlider(Qt.Orientation.Horizontal)
        self.ses_surgu.setRange(0, 100)
        self.ses_surgu.setFixedWidth(130)
        self.ses_surgu.setValue(self.program.ana_ses)
        self.ses_surgu.setToolTip("Ana ses düzeyi (↑ / ↓)")
        self.ses_surgu.valueChanged.connect(self._ana_ses_degisti)
        ayar.addWidget(self.ses_surgu)
        self.lbl_ses = QLabel(f"%{self.program.ana_ses}")
        self.lbl_ses.setObjectName("MiniEtiket")
        self.lbl_ses.setFixedWidth(38)
        ayar.addWidget(self.lbl_ses)

        ayar.addSpacing(8)
        gecis_etiket = QLabel("GEÇİŞ")
        gecis_etiket.setObjectName("MiniEtiket")
        ayar.addWidget(gecis_etiket)
        self.fade_surgu = QSlider(Qt.Orientation.Horizontal)
        self.fade_surgu.setRange(0, 4000)
        self.fade_surgu.setSingleStep(100)
        self.fade_surgu.setPageStep(250)
        self.fade_surgu.setFixedWidth(104)
        self.fade_surgu.setValue(self.program.fade_ms)
        self.fade_surgu.setToolTip("Sesin açılma ve kapanma yumuşaklığı")
        self.fade_surgu.valueChanged.connect(self._fade_degisti)
        ayar.addWidget(self.fade_surgu)
        self.lbl_fade = QLabel("")
        self.lbl_fade.setObjectName("MiniEtiket")
        self.lbl_fade.setFixedWidth(46)
        ayar.addWidget(self.lbl_fade)

        self.oto_kutu = QCheckBox("Otomatik sıradaki")
        self.oto_kutu.setChecked(self.program.oto_gecis)
        self.oto_kutu.setToolTip("Parça bitince listedeki sıradaki parçaya kendiliğinden geç")
        self.oto_kutu.toggled.connect(self._oto_degisti)
        ayar.addWidget(self.oto_kutu)
        ayar.addStretch(1)
        denetim.addLayout(ayar)
        duzen.addLayout(denetim)

        # odak hırsızlığını önle: tuşlar pencereye gelsin
        odagi_kapat(konsol, QPushButton, QSlider, QCheckBox)
        return konsol

    # ================================================================ KISAYOL
    def _kisayollar_kur(self):
        def kisayol(dizi, islev):
            ks = QShortcut(QKeySequence(dizi), self)
            ks.activated.connect(islev)
            return ks

        kisayol("Ctrl+O", self.muzik_ekle)
        kisayol("Ctrl+Shift+O", self.klasor_ekle)
        kisayol("Ctrl+S", self.programi_aktar)
        kisayol("Ctrl+F", lambda: (self.arama.setFocus(), self.arama.selectAll()))
        kisayol("F1", self.yardim_goster)
        kisayol("F11", self.tam_ekran_degistir)
        kisayol("Ctrl+Shift+F", lambda: self.sigdir("hepsi"))
        kisayol("Ctrl+0", lambda: self.olcek_uygula(1.0, elle=True))
        for dizi in ("Ctrl++", "Ctrl+=", "Ctrl+Shift+="):
            kisayol(dizi, lambda: self.olcegi_degistir(0.08))
        for dizi in ("Ctrl+-", "Ctrl+_"):
            kisayol(dizi, lambda: self.olcegi_degistir(-0.08))

    def keyPressEvent(self, olay):
        tus = olay.key()
        shift = olay.modifiers() & Qt.KeyboardModifier.ShiftModifier

        if tus == Qt.Key.Key_Escape:
            if self.arama.hasFocus():
                self.arama.clear()
                self.setFocus()
            elif self.isFullScreen():
                self.showNormal()
            else:
                self.motor.durdur()
                self._bildir("Ses yumuşakça kısılıp durduruldu.")
            return
        if self.arama.hasFocus():
            super().keyPressEvent(olay)
            return

        if tus == Qt.Key.Key_Space:
            self.duraklat_devam()
        elif tus == Qt.Key.Key_K:
            self.motor.hemen_kes()
            self._bildir("Ses anında kesildi.")
        elif tus == Qt.Key.Key_N:
            self.komsu_cal(1)
        elif tus == Qt.Key.Key_P:
            self.komsu_cal(-1)
        elif tus == Qt.Key.Key_Right:
            self.motor.atla(30000 if shift else 5000)
        elif tus == Qt.Key.Key_Left:
            self.motor.atla(-30000 if shift else -5000)
        elif tus == Qt.Key.Key_Up:
            self.ses_surgu.setValue(min(100, self.ses_surgu.value() + 5))
        elif tus == Qt.Key.Key_Down:
            self.ses_surgu.setValue(max(0, self.ses_surgu.value() - 5))
        elif Qt.Key.Key_0 <= tus <= Qt.Key.Key_9:
            sira = 10 if tus == Qt.Key.Key_0 else tus - Qt.Key.Key_0
            if sira <= len(self.program.parcalar):
                self.kart_oynat(self.program.parcalar[sira - 1].id)
        else:
            super().keyPressEvent(olay)

    # ================================================================ KARTLAR
    def _kartlari_kur(self):
        for kart in self.kartlar.values():
            kart.setParent(None)
            kart.deleteLater()
        self.kartlar.clear()
        while self.akis.count():
            self.akis.takeAt(0)

        for sira, parca in enumerate(self.program.parcalar, start=1):
            kart = ParcaKart(parca, sira, self._olcek)
            kart.oynat_istendi.connect(self.kart_oynat)
            kart.duraklat_istendi.connect(lambda _i: self.motor.duraklat())
            kart.durdur_istendi.connect(lambda _i: self.motor.durdur())
            kart.dongu_degisti.connect(self._dongu_degisti)
            kart.kazanc_degisti.connect(self._kazanc_degisti)
            kart.menu_istendi.connect(self._kart_menusu)
            kart.tasindi.connect(self._kart_tasindi)
            self.akis.addWidget(kart)
            self.kartlar[parca.id] = kart
            if not parca.sure_ms and parca.var_mi:
                self.sure_bulucu.kuyruga_ekle(parca.id, parca.yol)

        aktif = self.motor.aktif_id
        if aktif in self.kartlar:
            self.kartlar[aktif].durum_ayarla(self.motor.son_durum)

        self._bos_ekran_tazele()
        self._ozet_tazele()
        self._filtre_uygula(self.arama.text())

    def _siralari_tazele(self):
        for sira, parca in enumerate(self.program.parcalar, start=1):
            kart = self.kartlar.get(parca.id)
            if kart:
                kart.tazele(parca, sira)

    def _bos_ekran_tazele(self):
        bos = not self.program.parcalar
        self.bos_kutu.setVisible(bos)
        self.kaydirma.setVisible(not bos)

    def _ozet_tazele(self):
        adet = len(self.program.parcalar)
        if not adet:
            self.lbl_ozet.setText("")
            return
        toplam = sum(p.sure_ms for p in self.program.parcalar)
        if self._sigdir_hedef == "hepsi":
            boyut = "KART: HEPSİ SIĞDI"
        elif self._sigdir_hedef:
            boyut = f"KART: {self._sigdir_hedef}'LİK"
        else:
            boyut = f"KART %{int(round(self._olcek * 100))}"
        metin = f"{adet} PARÇA  •  {sure_metni(toplam)}  •  {boyut}"
        eksik = sum(1 for p in self.program.parcalar if not p.var_mi)
        if eksik:
            metin += f"  •  {eksik} DOSYA YOK"
        self.lbl_ozet.setText(metin)

    def _filtre_uygula(self, metin: str):
        arama = (metin or "").strip().lower()
        for parca in self.program.parcalar:
            kart = self.kartlar.get(parca.id)
            if not kart:
                continue
            uyar = (not arama
                    or arama in parca.ad.lower()
                    or arama in parca.etiket.lower()
                    or arama in parca.dosya_adi.lower())
            kart.setVisible(uyar)
        self.akis.invalidate()
        self.akis.update()

    # ------------------------------------------------------------- parça ekle
    def muzik_ekle(self):
        dosyalar, _ = QFileDialog.getOpenFileNames(
            self, "Müzik dosyalarını seçin", str(Path.home()), SES_FILTRESI)
        if dosyalar:
            self.parcalari_ekle(dosyalar)

    def klasor_ekle(self):
        klasor = QFileDialog.getExistingDirectory(
            self, "Müzik klasörünü seçin", str(Path.home()))
        if not klasor:
            return
        bulunan = depo.klasordeki_sesler(klasor)
        if not bulunan:
            self._bildir("Klasörde ses dosyası bulunamadı.")
            return
        self.parcalari_ekle(bulunan)

    def parcalari_ekle(self, yollar):
        mevcut = {os.path.normcase(os.path.abspath(p.yol)) for p in self.program.parcalar}
        eklenen = 0
        for yol in yollar:
            tam = os.path.abspath(yol)
            if os.path.normcase(tam) in mevcut or not os.path.isfile(tam):
                continue
            mevcut.add(os.path.normcase(tam))
            renk = KART_RENKLERI[len(self.program.parcalar) % len(KART_RENKLERI)]
            ad = os.path.splitext(os.path.basename(tam))[0].replace("_", " ").strip()
            self.program.parcalar.append(Parca(yol=tam, ad=ad or os.path.basename(tam), renk=renk))
            eklenen += 1
        if eklenen:
            self._kartlari_kur()
            self._sigdiri_yenile()
            self._kayit_planla()
            self._konsol_tazele()
            self._bildir(f"{eklenen} parça eklendi.")
        else:
            self._bildir("Yeni parça eklenmedi (zaten listede olabilir).")

    def _parca_bul(self, parca_id: str):
        for sira, parca in enumerate(self.program.parcalar):
            if parca.id == parca_id:
                return sira, parca
        return -1, None

    # ----------------------------------------------------------------- çalma
    def kart_oynat(self, parca_id: str):
        _, parca = self._parca_bul(parca_id)
        if parca is None:
            return
        if not parca.var_mi:
            QMessageBox.warning(
                self, "Dosya yok",
                f"Bu dosya bulunamadı:\n{parca.yol}\n\n"
                "Kart menüsünden “Dosyayı yeniden bağla” ile düzeltebilirsiniz.")
            return
        if self.motor.aktif_id == parca_id:
            self.motor.duraklat_devam()
            return
        self.motor.cal(parca_id, parca.yol, parca.baslangic_ms, parca.dongu, parca.kazanc)

    def duraklat_devam(self):
        if self.motor.aktif_id is None:
            if self.program.parcalar:
                self.kart_oynat(self.program.parcalar[0].id)
            return
        self.motor.duraklat_devam()

    def komsu_cal(self, yon: int):
        if not self.program.parcalar:
            return
        if self.motor.aktif_id is None:
            hedef = 0 if yon > 0 else len(self.program.parcalar) - 1
        else:
            sira, _ = self._parca_bul(self.motor.aktif_id)
            hedef = (sira + yon) % len(self.program.parcalar)
        self.kart_oynat(self.program.parcalar[hedef].id)

    # --------------------------------------------------------------- kart menü
    def _kart_menusu(self, parca_id: str, konum: QPoint):
        sira, parca = self._parca_bul(parca_id)
        if parca is None:
            return
        menu = QMenu(self)
        menu.addAction("▶  Çal", lambda: self.kart_oynat(parca_id))
        menu.addSeparator()
        menu.addAction("Adını değiştir…", lambda: self._ad_degistir(parca_id))

        etiket_menu = menu.addMenu("Etiket")
        for etiket in HAZIR_ETIKETLER:
            gosterim = etiket if etiket else "— etiket yok —"
            etiket_menu.addAction(gosterim, lambda e=etiket: self._etiket_ayarla(parca_id, e))
        etiket_menu.addSeparator()
        etiket_menu.addAction("Kendim yazacağım…", lambda: self._etiket_sor(parca_id))

        renk_menu = menu.addMenu("Renk")
        for renk in KART_RENKLERI:
            renk_menu.addAction(renk, lambda r=renk: self._renk_ayarla(parca_id, r))

        dongu_eylem = menu.addAction("Sürekli tekrar (döngü)")
        dongu_eylem.setCheckable(True)
        dongu_eylem.setChecked(parca.dongu)
        dongu_eylem.toggled.connect(lambda a, i=parca_id: self._dongu_menuden(i, a))

        menu.addSeparator()
        if self.motor.aktif_id == parca_id and self.motor.konum() > 1000:
            menu.addAction(
                f"Başlangıcı buraya al ({sure_metni(self.motor.konum())})",
                lambda: self._baslangic_ayarla(parca_id, self.motor.konum()))
        if parca.baslangic_ms:
            menu.addAction(
                f"Başlangıç işaretini kaldır ({sure_metni(parca.baslangic_ms)})",
                lambda: self._baslangic_ayarla(parca_id, 0))

        menu.addSeparator()
        if sira > 0:
            menu.addAction("←  Sola taşı", lambda: self._tasi(sira, sira - 1))
        if sira < len(self.program.parcalar) - 1:
            menu.addAction("→  Sağa taşı", lambda: self._tasi(sira, sira + 1))
        menu.addAction("Başa al", lambda: self._tasi(sira, 0))

        menu.addSeparator()
        if parca.var_mi:
            menu.addAction("Dosya konumunu aç", lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(os.path.dirname(parca.yol))))
        else:
            menu.addAction("Dosyayı yeniden bağla…", lambda: self._yeniden_bagla(parca_id))
        menu.addAction("\U0001F5D1  Listeden kaldır", lambda: self._kaldir(parca_id))
        menu.exec(konum)

    def _ad_degistir(self, parca_id: str):
        _, parca = self._parca_bul(parca_id)
        yeni, tamam = QInputDialog.getText(self, "Parça adı", "Kartta görünecek ad:",
                                           QLineEdit.EchoMode.Normal, parca.ad)
        if tamam and yeni.strip():
            parca.ad = yeni.strip()
            self._siralari_tazele()
            self._kayit_planla()
            self._konsol_tazele()

    def _etiket_sor(self, parca_id: str):
        _, parca = self._parca_bul(parca_id)
        yeni, tamam = QInputDialog.getText(self, "Etiket", "Etiket (örn. Saygı Duruşu):",
                                           QLineEdit.EchoMode.Normal, parca.etiket)
        if tamam:
            self._etiket_ayarla(parca_id, yeni.strip())

    def _etiket_ayarla(self, parca_id: str, etiket: str):
        _, parca = self._parca_bul(parca_id)
        parca.etiket = etiket
        self._siralari_tazele()
        self._kayit_planla()

    def _renk_ayarla(self, parca_id: str, renk: str):
        _, parca = self._parca_bul(parca_id)
        parca.renk = renk
        self._siralari_tazele()
        self._kayit_planla()

    def _baslangic_ayarla(self, parca_id: str, ms: int):
        _, parca = self._parca_bul(parca_id)
        parca.baslangic_ms = int(ms)
        self._kayit_planla()
        self._bildir("Başlangıç noktası güncellendi." if ms else "Başlangıç işareti kaldırıldı.")

    def _dongu_menuden(self, parca_id: str, acik: bool):
        self._dongu_degisti(parca_id, acik)
        kart = self.kartlar.get(parca_id)
        if kart:
            kart.btn_dongu.blockSignals(True)
            kart.btn_dongu.setChecked(acik)
            kart.btn_dongu.blockSignals(False)

    def _dongu_degisti(self, parca_id: str, acik: bool):
        _, parca = self._parca_bul(parca_id)
        if parca is None:
            return
        parca.dongu = acik
        if self.motor.aktif_id == parca_id:
            self.motor.dongu_ayarla(acik)
        self._kayit_planla()

    def _kazanc_degisti(self, parca_id: str, kazanc: float):
        _, parca = self._parca_bul(parca_id)
        if parca is None:
            return
        parca.kazanc = kazanc
        if self.motor.aktif_id == parca_id:
            self.motor.kazanc_ayarla(kazanc)
        self._kayit_planla()

    def _tasi(self, kaynak: int, hedef: int):
        if kaynak == hedef or not (0 <= hedef < len(self.program.parcalar)):
            return
        parca = self.program.parcalar.pop(kaynak)
        self.program.parcalar.insert(hedef, parca)
        self._kartlari_kur()
        self._kayit_planla()
        self._konsol_tazele()

    def _sona_tasi(self, kaynak_id: str):
        k, _ = self._parca_bul(kaynak_id)
        if k >= 0:
            self._tasi(k, len(self.program.parcalar) - 1)

    def _kart_tasindi(self, kaynak_id: str, hedef_id: str):
        k, _ = self._parca_bul(kaynak_id)
        h, _ = self._parca_bul(hedef_id)
        if k >= 0 and h >= 0:
            self._tasi(k, h)

    def _kaldir(self, parca_id: str):
        sira, parca = self._parca_bul(parca_id)
        if parca is None:
            return
        cevap = QMessageBox.question(
            self, "Kaldır",
            f"“{parca.ad}” listeden kaldırılsın mı?\n(Dosya bilgisayardan silinmez.)")
        if cevap != QMessageBox.StandardButton.Yes:
            return
        if self.motor.aktif_id == parca_id:
            self.motor.hemen_kes()
        self.program.parcalar.pop(sira)
        self._kartlari_kur()
        self._kayit_planla()
        self._konsol_tazele()
        self._bildir("Parça kaldırıldı.")

    def _yeniden_bagla(self, parca_id: str):
        _, parca = self._parca_bul(parca_id)
        yol, _ = QFileDialog.getOpenFileName(
            self, f"“{parca.ad}” için dosyayı seçin", str(Path.home()), SES_FILTRESI)
        if yol:
            parca.yol = os.path.abspath(yol)
            parca.sure_ms = 0
            self._kartlari_kur()
            self._kayit_planla()
            self._bildir("Dosya yeniden bağlandı.")

    # ================================================================= BOYUT
    def olcek_uygula(self, olcek: float, elle: bool = False):
        """Bütün kartları verilen boyut çarpanına göre yeniden ölçekler."""
        yeni = max(EN_KUCUK_OLCEK, min(EN_BUYUK_OLCEK, round(float(olcek), 2)))
        self._olcek = yeni
        if elle:
            self._sigdir_hedef = ""
        self.program.olcek = yeni
        self.program.sigdir = self._sigdir_hedef

        for kart in self.kartlar.values():
            kart.olcek_ayarla(yeni)
        self._siralari_tazele()

        self._ozet_tazele()
        self.akis.invalidate()
        self.tahta.updateGeometry()
        self.tahta.adjustSize()
        self._kayit_planla()

    def olcegi_degistir(self, fark: float):
        self.olcek_uygula(self._olcek + fark, elle=True)

    def _boyut_menusu(self, ana: QMenu) -> QMenu:
        menu = ana.addMenu("Kart boyutu")
        menu.addAction("Büyüt\t\tCtrl +", lambda: self.olcegi_degistir(0.08))
        menu.addAction("Küçült\t\tCtrl −", lambda: self.olcegi_degistir(-0.08))
        menu.addAction("Varsayılan boyut\tCtrl 0",
                       lambda: self.olcek_uygula(1.0, elle=True))
        menu.addSeparator()
        menu.addAction("Bütün kartları ekrana sığdır\tCtrl ⇧ F",
                       lambda: self.sigdir("hepsi"))
        for adet in (12, 20, 30, 40):
            menu.addAction(f"Ekranda {adet} kart görünsün",
                           lambda a=adet: self.sigdir(str(a)))
        return menu

    def sigdir(self, hedef: str = "hepsi"):
        """hedef: 'hepsi' ya da ekranda görünmesi istenen kart sayısı."""
        self._sigdir_hedef = hedef
        adet = len(self.program.parcalar) if hedef == "hepsi" else int(hedef)
        if adet <= 0:
            self._sigdir_hedef = ""
            return
        self.olcek_uygula(self._en_iyi_olcek(adet))

        tamam = self._kac_sigiyor() >= adet
        if not tamam:
            self._bildir(f"Kartlar en küçük boyutta; ekrana {self._kac_sigiyor()} kart "
                         "sığdı, kalanlar aşağı kaydırınca görünür.")
        elif hedef == "hepsi":
            self._bildir(f"{len(self.program.parcalar)} kartın hepsi ekrana sığdırıldı.")
        else:
            self._bildir(f"Kartlar, ekranda {adet} tanesi görünecek biçimde ayarlandı.")

    def _kac_sigiyor(self) -> int:
        """Şu anki boyutta ekrana kaydırmadan kaç kart sığdığını söyler."""
        alan = self.kaydirma.viewport().size()
        o = kart_olculeri(self._olcek)
        bosluk = BOSLUK
        sutun = max(1, (alan.width() - 2 * KENAR + bosluk) // (o["en"] + bosluk))
        satir = max(1, (alan.height() - 2 * KENAR + bosluk) // (o["boy"] + bosluk))
        return int(sutun * satir)

    def _en_iyi_olcek(self, hedef_adet: int) -> float:
        """Verilen sayıda kartın kaydırmasız sığdığı en büyük boyutu bulur."""
        alan = self.kaydirma.viewport().size()
        genislik = alan.width() - 2 * KENAR
        yukseklik = alan.height() - 2 * KENAR
        if genislik < 80 or yukseklik < 80:
            return self._olcek
        bosluk = BOSLUK
        for yuz in range(int(EN_BUYUK_OLCEK * 100), int(EN_KUCUK_OLCEK * 100) - 1, -1):
            o = kart_olculeri(yuz / 100.0)
            sutun = max(1, (genislik + bosluk) // (o["en"] + bosluk))
            satir = -(-hedef_adet // sutun)
            if satir * o["boy"] + (satir - 1) * bosluk <= yukseklik:
                return yuz / 100.0
        return EN_KUCUK_OLCEK

    def _sigdiri_yenile(self):
        """Pencere boyutu değişince otomatik sığdırmayı tazeler."""
        if not self._sigdir_hedef or not self.program.parcalar:
            return
        adet = (len(self.program.parcalar) if self._sigdir_hedef == "hepsi"
                else int(self._sigdir_hedef))
        yeni = self._en_iyi_olcek(adet)
        if abs(yeni - self._olcek) >= 0.01:
            self.olcek_uygula(yeni)

    def showEvent(self, olay):
        super().showEvent(olay)
        if not getattr(self, "_ilk_gosterim", False):
            self._ilk_gosterim = True
            if self._sigdir_hedef:
                QTimer.singleShot(60, self._sigdiri_yenile)

    def resizeEvent(self, olay):
        super().resizeEvent(olay)
        self._yeniden_sigdir_zamani.start()

    # ================================================================ PROGRAM
    def _ana_menu(self):
        menu = QMenu(self)
        menu.addAction("Müzik dosyası ekle…\tCtrl O", self.muzik_ekle)
        menu.addAction("Klasör ekle…\tCtrl ⇧ O", self.klasor_ekle)
        menu.addSeparator()
        self._boyut_menusu(menu)
        menu.addAction("Tam ekran\tF11", self.tam_ekran_degistir)
        menu.addSeparator()
        menu.addAction("Programı dosyaya kaydet…\tCtrl S", self.programi_aktar)
        menu.addAction("Program dosyası yükle…", self.programi_al)
        menu.addAction("Süreleri yeniden oku", self._sureleri_tazele)
        menu.addSeparator()
        menu.addAction("Tüm listeyi temizle", self._listeyi_temizle)
        menu.addSeparator()
        menu.addAction("Kısayollar ve ipuçları\tF1", self.yardim_goster)
        menu.exec(self.btn_menu.mapToGlobal(QPoint(0, self.btn_menu.height() + 4)))

    def programi_aktar(self):
        yol, _ = QFileDialog.getSaveFileName(
            self, "Programı kaydet",
            str(Path.home() / "cumhuriyet-programi.json"), "Program dosyası (*.json)")
        if yol:
            depo.kaydet(self.program, Path(yol))
            self._bildir(f"Program kaydedildi: {os.path.basename(yol)}")

    def programi_al(self):
        yol, _ = QFileDialog.getOpenFileName(
            self, "Program dosyası seç", str(Path.home()), "Program dosyası (*.json)")
        if not yol:
            return
        yeni = depo.yukle(Path(yol))
        if not yeni.parcalar:
            self._bildir("Dosyada parça bulunamadı.")
            return
        self.motor.hemen_kes()
        self.program = yeni
        self.ses_surgu.setValue(self.program.ana_ses)
        self.fade_surgu.setValue(self.program.fade_ms)
        self.oto_kutu.setChecked(self.program.oto_gecis)
        self._sigdir_hedef = self.program.sigdir or ""
        self._kartlari_kur()
        self.olcek_uygula(self.program.olcek)
        self._kaydet()
        self._konsol_tazele()
        self._bildir("Program yüklendi.")

    def _sureleri_tazele(self):
        for parca in self.program.parcalar:
            if parca.var_mi:
                parca.sure_ms = 0
                self.sure_bulucu.kuyruga_ekle(parca.id, parca.yol)
        self._siralari_tazele()
        self._bildir("Süreler okunuyor…")

    def _listeyi_temizle(self):
        if not self.program.parcalar:
            return
        cevap = QMessageBox.question(
            self, "Listeyi temizle",
            "Bütün parçalar listeden kaldırılsın mı?\n(Dosyalar bilgisayardan silinmez.)")
        if cevap != QMessageBox.StandardButton.Yes:
            return
        self.motor.hemen_kes()
        self.program.parcalar.clear()
        self._kartlari_kur()
        self._kaydet()
        self._konsol_tazele()

    def _kayit_planla(self):
        self._kayit_zamani.start()

    def _kaydet(self):
        self.program.ana_ses = self.ses_surgu.value()
        self.program.fade_ms = self.fade_surgu.value()
        self.program.oto_gecis = self.oto_kutu.isChecked()
        self.program.olcek = self._olcek
        self.program.sigdir = self._sigdir_hedef
        try:
            depo.kaydet(self.program)
        except OSError:
            pass

    # ================================================================== MOTOR
    def _motor_bagla(self):
        self.motor.konum_degisti.connect(self._konum_degisti)
        self.motor.sure_degisti.connect(self._sure_motordan)
        self.motor.durum_degisti.connect(self._durum_degisti)
        self.motor.parca_bitti.connect(self._parca_bitti)
        self.motor.hata.connect(lambda m: QMessageBox.warning(self, "Ses hatası", m))

    def _durum_degisti(self, parca_id: str, durum: str):
        kart = self.kartlar.get(parca_id)
        if kart:
            if durum == "durdu":
                _, parca = self._parca_bul(parca_id)
                kart.durum_ayarla("bos" if (parca and parca.var_mi) else "eksik")
            else:
                kart.durum_ayarla(durum)
        self.ritim.etkinlestir(durum == "calisiyor")
        self.btn_oynat.setText("❙❙" if durum == "calisiyor" else "▶")
        self._konsol_tazele()

    def _konum_degisti(self, konum: int):
        sure = self.motor.sure()
        if not self._suruklenen_seek and sure > 0:
            self.seek.setValue(int(min(1000, konum / sure * 1000)))
        self.lbl_gecen.setText(sure_metni(konum))
        self.lbl_kalan.setText(sure_metni(max(0, sure - konum)))
        kart = self.kartlar.get(self.motor.aktif_id or "")
        if kart:
            kart.ilerleme_ayarla(konum, sure)

    def _sure_motordan(self, sure: int):
        self.lbl_toplam.setText(sure_metni(sure))
        aktif = self.motor.aktif_id
        if aktif and sure > 0:
            _, parca = self._parca_bul(aktif)
            if parca and parca.sure_ms != sure:
                parca.sure_ms = sure
                self._siralari_tazele()
                self._kayit_planla()
                self._ozet_tazele()

    def _parca_bitti(self, parca_id: str):
        if not self.oto_kutu.isChecked():
            self._konsol_tazele()
            return
        sira, _ = self._parca_bul(parca_id)
        if 0 <= sira < len(self.program.parcalar) - 1:
            self.kart_oynat(self.program.parcalar[sira + 1].id)
        else:
            self._bildir("Program listesinin sonuna gelindi.")
            self._konsol_tazele()

    def _sure_geldi(self, parca_id: str, sure_ms: int):
        _, parca = self._parca_bul(parca_id)
        if parca:
            parca.sure_ms = sure_ms
            kart = self.kartlar.get(parca_id)
            if kart:
                sira, _ = self._parca_bul(parca_id)
                kart.tazele(parca, sira + 1)
            self._ozet_tazele()
            self._kayit_planla()

    # -------------------------------------------------------------- konsol/ses
    def _konsol_tazele(self):
        aktif = self.motor.aktif_id
        if aktif:
            _, parca = self._parca_bul(aktif)
            ad = parca.ad if parca else "—"
            etiket = f"{parca.etiket.upper()}  •  " if (parca and parca.etiket) else ""
            self.lbl_simdi_ad.setText(ad)
            self.lbl_simdi_etiket.setText(
                etiket + ("ŞİMDİ ÇALIYOR" if self.motor.son_durum == "calisiyor"
                          else "DURAKLATILDI"))
            sira, _ = self._parca_bul(aktif)
            if 0 <= sira < len(self.program.parcalar) - 1:
                self.lbl_siradaki.setText("Sıradaki:  " + self.program.parcalar[sira + 1].ad)
            else:
                self.lbl_siradaki.setText("Sıradaki:  —")
        else:
            self.lbl_simdi_ad.setText("—")
            self.lbl_simdi_etiket.setText("HAZIR")
            self.seek.setValue(0)
            self.lbl_gecen.setText("0:00")
            self.lbl_kalan.setText("0:00")
            self.lbl_toplam.setText("0:00")
            ilk = self.program.parcalar[0].ad if self.program.parcalar else "—"
            self.lbl_siradaki.setText("Sıradaki:  " + ilk)
        self._ozet_tazele()

    def _seek_onizle(self, deger: int):
        sure = self.motor.sure()
        if sure > 0:
            konum = int(sure * deger / 1000)
            self.lbl_gecen.setText(sure_metni(konum))
            self.lbl_kalan.setText(sure_metni(max(0, sure - konum)))

    def _seek_birak(self):
        self._suruklenen_seek = False
        sure = self.motor.sure()
        if sure > 0:
            self.motor.konumla(int(sure * self.seek.value() / 1000))

    def _ana_ses_degisti(self, deger: int):
        self.motor.ana_ses_ayarla(deger)
        self.lbl_ses.setText(f"%{deger}")
        self._kayit_planla()

    def _fade_degisti(self, deger: int):
        self.motor.fade_ms = deger
        self.lbl_fade.setText("kapalı" if deger < 100 else f"{deger / 1000:.1f} sn")
        self._kayit_planla()

    def _oto_degisti(self, _acik: bool):
        self._kayit_planla()
        self._konsol_tazele()

    # =================================================================== DİĞER
    def _saat_kur(self):
        from PySide6.QtCore import QDateTime

        def tik():
            simdi = QDateTime.currentDateTime()
            self.lbl_saat.setText(simdi.toString("HH:mm:ss"))
            t = simdi.date()
            self.lbl_saat.setToolTip(
                f"{t.day()} {AYLAR[t.month() - 1]} {t.year()}  •  {GUNLER[t.dayOfWeek() - 1]}")

        self._saat = QTimer(self)
        self._saat.setInterval(500)
        self._saat.timeout.connect(tik)
        self._saat.start()
        tik()

    def _bildir(self, mesaj: str):
        self.lbl_bildirim.setText(mesaj)
        self._bildirim_zamani.start(4000)

    def yardim_goster(self):
        YardimPenceresi(self).exec()

    def tam_ekran_degistir(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # --------------------------------------------------------- sürükle & bırak
    def dragEnterEvent(self, olay):
        if olay.mimeData().hasUrls():
            olay.acceptProposedAction()

    def dragMoveEvent(self, olay):
        if olay.mimeData().hasUrls():
            olay.acceptProposedAction()

    def dropEvent(self, olay):
        yollar = []
        for url in olay.mimeData().urls():
            yerel = url.toLocalFile()
            if not yerel:
                continue
            if os.path.isdir(yerel):
                yollar.extend(depo.klasordeki_sesler(yerel))
            elif yerel.lower().endswith(depo.SES_UZANTILARI):
                yollar.append(yerel)
        if yollar:
            self.parcalari_ekle(yollar)
            olay.acceptProposedAction()
        else:
            self._bildir("Bırakılan dosyalar arasında ses dosyası yok.")

    def closeEvent(self, olay):
        self.motor.hemen_kes()
        self._kaydet()
        super().closeEvent(olay)
