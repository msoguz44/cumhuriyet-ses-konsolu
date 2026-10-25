"""Parça verisi, program dosyası (JSON) ve süre bulucu."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from tema import KART_RENKLERI

SES_UZANTILARI = (
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".oga",
    ".wma", ".aiff", ".aif", ".opus", ".mp4", ".m4r",
)


@dataclass
class Parca:
    yol: str
    ad: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    etiket: str = ""
    renk: str = KART_RENKLERI[0]
    sure_ms: int = 0
    kazanc: float = 1.0          # parçaya özel ses çarpanı (0.0 - 1.5)
    dongu: bool = False
    baslangic_ms: int = 0        # "buradan başlat" işareti

    @property
    def dosya_adi(self) -> str:
        return os.path.basename(self.yol)

    @property
    def var_mi(self) -> bool:
        try:
            return os.path.isfile(self.yol)
        except OSError:
            return False

    def sozluk(self) -> dict:
        return asdict(self)

    @staticmethod
    def sozlukten(veri: dict) -> "Parca":
        bilinen = {k: v for k, v in veri.items() if k in Parca.__dataclass_fields__}
        bilinen.setdefault("ad", os.path.splitext(os.path.basename(bilinen.get("yol", "")))[0])
        return Parca(**bilinen)


@dataclass
class Liste:
    """Bir çalma listesi (tören programı). Hepsi uygulamanın içinde saklanır."""

    ad: str = "Program"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    parcalar: list = field(default_factory=list)

    @property
    def toplam_ms(self) -> int:
        return sum(p.sure_ms for p in self.parcalar)

    def sozluk(self) -> dict:
        return {"id": self.id, "ad": self.ad,
                "parcalar": [p.sozluk() for p in self.parcalar]}

    @staticmethod
    def sozlukten(veri: dict) -> "Liste":
        liste = Liste(ad=str(veri.get("ad") or "Program"))
        if veri.get("id"):
            liste.id = str(veri["id"])
        liste.parcalar = [Parca.sozlukten(p) for p in veri.get("parcalar", [])]
        return liste

    def kopyala(self, yeni_ad: str) -> "Liste":
        kopya = Liste(ad=yeni_ad)
        for p in self.parcalar:
            veri = p.sozluk()
            veri.pop("id", None)
            kopya.parcalar.append(Parca.sozlukten(veri))
        return kopya


@dataclass
class Program:
    """Uygulamanın bütün hâli: listeler ve ortak ayarlar."""

    listeler: list = field(default_factory=lambda: [Liste()])
    aktif: int = 0
    ana_ses: int = 85
    fade_ms: int = 1200
    oto_gecis: bool = False
    olcek: float = 1.0           # kart boyutu çarpanı
    sigdir: str = "hepsi"        # "" | "hepsi" | "12" | "20" ... (otomatik sığdırma)
    elle_boyut: bool = False     # kullanıcı boyutu elle ayarladıysa otomatik sığdırma kapanır

    # ----------------------------------------------------------- listeler
    def __post_init__(self):
        if not self.listeler:
            self.listeler = [Liste()]
        self.aktif = max(0, min(self.aktif, len(self.listeler) - 1))

    @property
    def aktif_liste(self) -> Liste:
        self.aktif = max(0, min(self.aktif, len(self.listeler) - 1))
        return self.listeler[self.aktif]

    @property
    def parcalar(self) -> list:
        """Etkin listenin parçaları (yerinde değiştirilebilir)."""
        return self.aktif_liste.parcalar

    def liste_ekle(self, ad: str, parcalar: list | None = None) -> int:
        self.listeler.append(Liste(ad=ad, parcalar=parcalar or []))
        return len(self.listeler) - 1

    def liste_sil(self, sira: int):
        if 0 <= sira < len(self.listeler):
            self.listeler.pop(sira)
        if not self.listeler:
            self.listeler = [Liste()]
        self.aktif = max(0, min(self.aktif, len(self.listeler) - 1))

    def liste_bul(self, liste_id: str) -> int:
        for i, liste in enumerate(self.listeler):
            if liste.id == liste_id:
                return i
        return -1

    def benzersiz_ad(self, istek: str) -> str:
        adlar = {l.ad for l in self.listeler}
        if istek not in adlar:
            return istek
        n = 2
        while f"{istek} ({n})" in adlar:
            n += 1
        return f"{istek} ({n})"

    # ------------------------------------------------------------ kayıt
    def sozluk(self) -> dict:
        return {
            "surum": 2,
            "ana_ses": self.ana_ses,
            "fade_ms": self.fade_ms,
            "oto_gecis": self.oto_gecis,
            "olcek": self.olcek,
            "sigdir": self.sigdir,
            "elle_boyut": self.elle_boyut,
            "aktif": self.aktif,
            "listeler": [l.sozluk() for l in self.listeler],
        }

    @staticmethod
    def sozlukten(veri: dict) -> "Program":
        prg = Program()
        prg.ana_ses = int(veri.get("ana_ses", 85))
        prg.fade_ms = int(veri.get("fade_ms", 1200))
        prg.oto_gecis = bool(veri.get("oto_gecis", False))
        prg.olcek = float(veri.get("olcek", 1.0) or 1.0)
        prg.elle_boyut = bool(veri.get("elle_boyut", False))
        # Eski dosyalarda sığdırma yoktu; kartlar ekrana sığsın diye açık geliyor.
        prg.sigdir = str(veri.get("sigdir", "hepsi") or ("" if prg.elle_boyut else "hepsi"))

        if veri.get("listeler"):
            prg.listeler = [Liste.sozlukten(l) for l in veri["listeler"]]
        elif veri.get("parcalar"):
            # Eski tek listeli dosya: olduğu gibi tek listeye taşınır.
            prg.listeler = [Liste(ad="Program",
                                  parcalar=[Parca.sozlukten(p) for p in veri["parcalar"]])]
        else:
            prg.listeler = [Liste()]
        prg.aktif = int(veri.get("aktif", 0) or 0)
        prg.__post_init__()
        return prg


def veri_klasoru() -> Path:
    kok = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    yol = Path(kok) if kok else Path.home() / ".cumhuriyet_ses"
    yol.mkdir(parents=True, exist_ok=True)
    return yol


def otomatik_dosya() -> Path:
    return veri_klasoru() / "program.json"


def kaydet(program: Program, dosya: Path | None = None) -> Path:
    dosya = Path(dosya) if dosya else otomatik_dosya()
    dosya.parent.mkdir(parents=True, exist_ok=True)
    gecici = dosya.with_suffix(dosya.suffix + ".tmp")
    gecici.write_text(json.dumps(program.sozluk(), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(gecici, dosya)
    return dosya


def yukle(dosya: Path | None = None) -> Program:
    dosya = Path(dosya) if dosya else otomatik_dosya()
    if not dosya.is_file():
        return Program()
    try:
        return Program.sozlukten(json.loads(dosya.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return Program()


def klasordeki_sesler(klasor: str) -> list:
    """Klasörü (alt klasörleriyle) tarayıp ses dosyalarını sıralı döndürür."""
    bulunan = []
    for kok, _, dosyalar in os.walk(klasor):
        for d in sorted(dosyalar):
            if d.lower().endswith(SES_UZANTILARI) and not d.startswith("."):
                bulunan.append(os.path.join(kok, d))
    return bulunan


class SureBulucu(QObject):
    """Arka planda, dosyaların süresini sırayla okur.

    Not: QMediaPlayer'ın sinyali içinde yeni kaynak atamak kütüphanede
    çökmeye yol açıyor; bu yüzden sıradaki dosyaya her zaman olay
    döngüsüne bırakarak (singleShot) geçiyoruz.
    """

    bulundu = Signal(str, int)   # parca_id, sure_ms

    def __init__(self, parent=None):
        super().__init__(parent)
        self._kuyruk: list[tuple[str, str]] = []
        self._aktif: tuple[str, str] | None = None
        self._mesgul = False
        self._cikis = QAudioOutput(self)
        self._cikis.setVolume(0.0)
        self._oynatici = QMediaPlayer(self)
        self._oynatici.setAudioOutput(self._cikis)
        self._oynatici.durationChanged.connect(self._sure_geldi)
        self._oynatici.errorOccurred.connect(lambda *a: self._bitir())
        self._oynatici.mediaStatusChanged.connect(self._durum)

        self._zaman_asimi = QTimer(self)
        self._zaman_asimi.setSingleShot(True)
        self._zaman_asimi.setInterval(4000)
        self._zaman_asimi.timeout.connect(self._bitir)

    def kuyruga_ekle(self, parca_id: str, yol: str):
        self._kuyruk.append((parca_id, yol))
        self._plan()

    def _plan(self):
        if not self._mesgul:
            QTimer.singleShot(0, self._sonraki)

    def _sonraki(self):
        if self._mesgul or not self._kuyruk:
            return
        self._mesgul = True
        self._aktif = self._kuyruk.pop(0)
        self._zaman_asimi.start()
        self._oynatici.setSource(QUrl.fromLocalFile(self._aktif[1]))

    def _bitir(self):
        """Sıradaki dosyaya geç (her zaman olay döngüsüne bırakılır)."""
        self._zaman_asimi.stop()
        self._aktif = None
        self._mesgul = False
        self._plan()

    def _sure_geldi(self, sure: int):
        if self._aktif and sure > 0:
            self.bulundu.emit(self._aktif[0], int(sure))
            QTimer.singleShot(0, self._bitir)

    def _durum(self, durum):
        if durum in (QMediaPlayer.MediaStatus.InvalidMedia,
                     QMediaPlayer.MediaStatus.NoMedia):
            if self._aktif is not None:
                QTimer.singleShot(0, self._bitir)
