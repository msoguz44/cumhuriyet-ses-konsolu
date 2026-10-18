"""Ses motoru: tek parça çalar, yumuşak açılma/kapanma (fade) yapar."""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudio, QAudioOutput, QMediaPlayer

ADIM_MS = 20  # fade zamanlayıcı adımı


def _dogrusal(mantiksal: float) -> float:
    """Kulağa doğrusal gelen 0-1 değerini gerçek genlik değerine çevirir."""
    mantiksal = max(0.0, min(1.0, mantiksal))
    try:
        return QAudio.convertVolume(
            mantiksal,
            QAudio.VolumeScale.LogarithmicVolumeScale,
            QAudio.VolumeScale.LinearVolumeScale,
        )
    except Exception:
        return mantiksal * mantiksal


class SesMotoru(QObject):
    konum_degisti = Signal(int)          # ms
    sure_degisti = Signal(int)           # ms
    durum_degisti = Signal(str, str)     # parca_id, "calisiyor" | "duraklatildi" | "durdu"
    parca_bitti = Signal(str)            # parca_id
    hata = Signal(str)                   # kullanıcıya gösterilecek mesaj

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cikis = QAudioOutput(self)
        self._oynatici = QMediaPlayer(self)
        self._oynatici.setAudioOutput(self._cikis)

        self.aktif_id: str | None = None
        self.son_durum = "durdu"      # calisiyor | duraklatildi | durdu
        self.fade_ms = 1200

        self._ana_ses = 0.85     # 0-1
        self._kazanc = 1.0       # parçaya özel çarpan
        self._zarf = 0.0         # fade zarfı 0-1
        self._bekleyen_konum = 0
        self._bitince = None

        self._fade = QTimer(self)
        self._fade.setInterval(ADIM_MS)
        self._fade.timeout.connect(self._fade_adim)
        self._fade_baslangic = 0.0
        self._fade_hedef = 0.0
        self._fade_sure = 1
        self._fade_gecen = 0

        self._nabiz = QTimer(self)
        self._nabiz.setInterval(80)
        self._nabiz.timeout.connect(self._konum_yayinla)

        self._oynatici.durationChanged.connect(self.sure_degisti.emit)
        self._oynatici.mediaStatusChanged.connect(self._medya_durumu)
        self._oynatici.errorOccurred.connect(self._hata)

    def _durum_bildir(self, parca_id: str, durum: str):
        if parca_id == self.aktif_id or durum != "durdu":
            self.son_durum = durum
        elif self.aktif_id is None:
            self.son_durum = "durdu"
        self.durum_degisti.emit(parca_id, durum)

    # ------------------------------------------------------------- ses düzeyi
    @property
    def ana_ses(self) -> int:
        return int(round(self._ana_ses * 100))

    def ana_ses_ayarla(self, yuzde: int):
        self._ana_ses = max(0.0, min(1.0, yuzde / 100.0))
        self._uygula()

    def kazanc_ayarla(self, kazanc: float):
        self._kazanc = max(0.0, min(1.5, kazanc))
        self._uygula()

    def _uygula(self):
        self._cikis.setVolume(_dogrusal(self._ana_ses * self._kazanc * self._zarf))

    # ------------------------------------------------------------- oynatma
    def cal(self, parca_id: str, yol: str, baslangic_ms: int = 0,
            dongu: bool = False, kazanc: float = 1.0, fade_ms: int | None = None):
        """Yeni parçayı baştan (ya da işaretli konumdan) çalar."""
        fade = self.fade_ms if fade_ms is None else fade_ms
        eski = self.aktif_id
        self._fade_durdur()
        self._oynatici.stop()
        if eski and eski != parca_id:
            self._durum_bildir(eski, "durdu")

        self.aktif_id = parca_id
        self._kazanc = max(0.0, min(1.5, kazanc))
        self._zarf = 0.0
        self._uygula()
        self._bekleyen_konum = max(0, int(baslangic_ms))
        self._oynatici.setLoops(
            QMediaPlayer.Loops.Infinite if dongu else 1
        )
        self._oynatici.setSource(QUrl.fromLocalFile(yol))
        self._oynatici.play()
        self._nabiz.start()
        self._durum_bildir(parca_id, "calisiyor")
        self._fade_baslat(1.0, fade)

    def duraklat(self, fade_ms: int | None = None):
        if self.aktif_id is None:
            return
        fade = self.fade_ms if fade_ms is None else fade_ms
        parca = self.aktif_id

        def bitti():
            self._oynatici.pause()
            self._nabiz.stop()
            self._durum_bildir(parca, "duraklatildi")

        self._fade_baslat(0.0, min(fade, 350), bitti)

    def devam(self, fade_ms: int | None = None):
        if self.aktif_id is None:
            return
        fade = self.fade_ms if fade_ms is None else fade_ms
        self._zarf = 0.0
        self._uygula()
        self._oynatici.play()
        self._nabiz.start()
        self._durum_bildir(self.aktif_id, "calisiyor")
        self._fade_baslat(1.0, min(fade, 500))

    def duraklat_devam(self):
        if self.aktif_id is None:
            return
        if self.calisiyor_mu():
            self.duraklat()
        else:
            self.devam()

    def durdur(self, fade_ms: int | None = None):
        """Varsa çalan parçayı yumuşakça kısıp durdurur (sahne için güvenli)."""
        if self.aktif_id is None:
            return
        fade = self.fade_ms if fade_ms is None else fade_ms
        parca = self.aktif_id

        def bitti():
            self._oynatici.stop()
            self._nabiz.stop()
            self.aktif_id = None
            self._durum_bildir(parca, "durdu")
            self.konum_degisti.emit(0)

        self._fade_baslat(0.0, fade, bitti)

    def hemen_kes(self):
        """Fade'siz anında kesme."""
        parca = self.aktif_id
        self._fade_durdur()
        self._oynatici.stop()
        self._nabiz.stop()
        self.aktif_id = None
        self._zarf = 0.0
        self._uygula()
        if parca:
            self._durum_bildir(parca, "durdu")
            self.konum_degisti.emit(0)

    # ------------------------------------------------------------- konum
    def calisiyor_mu(self) -> bool:
        return self._oynatici.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def konum(self) -> int:
        return int(self._oynatici.position())

    def sure(self) -> int:
        return int(self._oynatici.duration())

    def konumla(self, ms: int):
        if self.aktif_id is not None:
            self._oynatici.setPosition(max(0, int(ms)))
            self._konum_yayinla()

    def atla(self, delta_ms: int):
        if self.aktif_id is None:
            return
        sure = self.sure()
        yeni = self.konum() + delta_ms
        if sure > 0:
            yeni = min(yeni, max(0, sure - 250))
        self.konumla(max(0, yeni))

    def dongu_ayarla(self, dongu: bool):
        self._oynatici.setLoops(QMediaPlayer.Loops.Infinite if dongu else 1)

    # ------------------------------------------------------------- iç işler
    def _konum_yayinla(self):
        self.konum_degisti.emit(self.konum())

    def _fade_baslat(self, hedef: float, sure_ms: int, bitince=None):
        self._fade.stop()
        self._bitince = bitince
        if sure_ms <= ADIM_MS:
            self._zarf = hedef
            self._uygula()
            if bitince:
                self._bitince = None
                bitince()
            return
        self._fade_baslangic = self._zarf
        self._fade_hedef = hedef
        self._fade_sure = max(1, int(sure_ms))
        self._fade_gecen = 0
        self._fade.start()

    def _fade_adim(self):
        self._fade_gecen += ADIM_MS
        oran = min(1.0, self._fade_gecen / self._fade_sure)
        yumusak = oran * oran * (3 - 2 * oran)  # smoothstep
        self._zarf = self._fade_baslangic + (self._fade_hedef - self._fade_baslangic) * yumusak
        self._uygula()
        if oran >= 1.0:
            self._fade.stop()
            self._zarf = self._fade_hedef
            self._uygula()
            geri = self._bitince
            self._bitince = None
            if geri:
                geri()

    def _fade_durdur(self):
        self._fade.stop()
        self._bitince = None

    def _medya_durumu(self, durum):
        if durum in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            if self._bekleyen_konum > 0:
                self._oynatici.setPosition(self._bekleyen_konum)
                self._bekleyen_konum = 0
        elif durum == QMediaPlayer.MediaStatus.EndOfMedia:
            parca = self.aktif_id
            self._nabiz.stop()
            self.aktif_id = None
            self._zarf = 0.0
            self._uygula()
            if parca:
                self._durum_bildir(parca, "durdu")
                self.parca_bitti.emit(parca)
        elif durum == QMediaPlayer.MediaStatus.InvalidMedia:
            self.hata.emit("Dosya açılamadı ya da biçimi desteklenmiyor.")

    def _hata(self, *args):
        mesaj = self._oynatici.errorString() or "Bilinmeyen ses hatası."
        parca = self.aktif_id
        self._nabiz.stop()
        self._fade_durdur()
        self.aktif_id = None
        if parca:
            self._durum_bildir(parca, "durdu")
        self.hata.emit(mesaj)
