"""Uygulamanın renk paleti ve Qt stil şablonu (QSS)."""

RENKLER = {
    "zemin":        "#0B0D12",
    "panel":        "#121521",
    "kart":         "#1A1F2E",
    "kart_hover":   "#222940",
    "cizgi":        "#2C3348",
    "metin":        "#EEF1F7",
    "metin_soluk":  "#98A2B8",
    "kirmizi":      "#E30A17",
    "kirmizi_koyu": "#9E0710",
    "kirmizi_acik": "#FF3A46",
    "altin":        "#F2C14E",
    "yesil":        "#22C55E",
    "turuncu":      "#FB923C",
}

# Kartların sırayla kullandığı vurgu renkleri
KART_RENKLERI = [
    "#E30A17", "#F2C14E", "#38BDF8", "#22C55E", "#A78BFA",
    "#FB923C", "#F472B6", "#2DD4BF", "#FACC15", "#60A5FA",
]

QSS = """
* { font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif; }

QWidget#Kok { background-color: %(zemin)s; }

/* ------------------------------ Üst şerit ------------------------------ */
QFrame#UstSerit {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #150507, stop:0.45 %(panel)s, stop:1 #141828);
    border-bottom: 1px solid %(cizgi)s;
}
QLabel#Baslik   { color: %(metin)s; font-size: 20px; font-weight: 800; letter-spacing: 1px; }
QLabel#AltBaslik{ color: %(kirmizi_acik)s; font-size: 11px; font-weight: 700; letter-spacing: 3px; }
QLabel#Saat     { color: %(metin)s; font-size: 21px; font-weight: 800; }
QLabel#Tarih    { color: %(metin_soluk)s; font-size: 11px; font-weight: 600; letter-spacing: 1px; }

/* ------------------------------ Düğmeler ------------------------------ */
QPushButton {
    background-color: %(kart)s;
    color: %(metin)s;
    border: 1px solid %(cizgi)s;
    border-radius: 10px;
    padding: 9px 14px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover   { background-color: %(kart_hover)s; border-color: #3C4664; }
QPushButton:pressed { background-color: #0F131E; }
QPushButton:disabled{ color: #5A6480; border-color: #202536; }

QPushButton#Birincil {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 %(kirmizi_acik)s, stop:1 %(kirmizi_koyu)s);
    border: 1px solid #FF5A64;
    color: #FFFFFF;
    font-weight: 800;
}
QPushButton#Birincil:hover   { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #FF5660, stop:1 #B4090F); }
QPushButton#Birincil:pressed { background: %(kirmizi_koyu)s; }

QPushButton#Panik {
    background-color: #2A0F13;
    border: 1px solid %(kirmizi)s;
    color: %(kirmizi_acik)s;
    font-weight: 800;
}
QPushButton#Panik:hover { background-color: #3C1218; }

QPushButton#Aktar { padding: 7px 12px; font-size: 12px; }
QPushButton#Mini {
    padding: 4px 10px; font-size: 12px; font-weight: 700;
    border-radius: 8px; background-color: #191E2E;
}
QPushButton#Mini:hover { background-color: %(kart_hover)s; }
QSlider#Boyut::groove:horizontal { height: 4px; background-color: #222A3E; }
QSlider#Boyut::handle:horizontal { width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
QSlider#Boyut::sub-page:horizontal {
    height: 4px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4A5370, stop:1 #8B93AD);
}

/* Kart içindeki küçük yuvarlak düğmeler (boyutları koddan ölçeklenir) */
QPushButton#KartKucuk {
    background-color: rgba(255,255,255,18);
    border: 1px solid %(cizgi)s;
    border-radius: 9px;
    padding: 0px;
}
QPushButton#KartKucuk:hover { background-color: rgba(255,255,255,40); }
QPushButton#KartKucuk:checked {
    background-color: %(kirmizi_koyu)s;
    border-color: %(kirmizi_acik)s;
    color: #FFFFFF;
}

/* ------------------------------ Kartlar ------------------------------ */
QFrame#Kart {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 %(kart)s, stop:1 #141927);
    border: 1px solid %(cizgi)s;
    border-radius: 16px;
}
QFrame#Kart:hover { border-color: #46516F; }
QFrame#Kart[durum="calisiyor"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2A1218, stop:1 #180F16);
    border: 2px solid %(kirmizi)s;
}
QFrame#Kart[durum="duraklatildi"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2A2410, stop:1 #171508);
    border: 2px solid %(altin)s;
}
QFrame#Kart[durum="eksik"] { border: 1px dashed #7A2630; }
QFrame#Kart[hedef="true"]  { border: 2px dashed %(altin)s; }

QLabel#KartSira {
    background-color: rgba(255,255,255,20);
    color: %(metin)s;
    font-weight: 800;
}
QLabel#KartAd     { color: %(metin)s; font-weight: 700; }
QLabel#KartDosya  { color: %(metin_soluk)s; }
QLabel#KartSure   { color: %(metin_soluk)s; font-weight: 700; }
QLabel#KartEtiket { color: #10131C; border-radius: 8px; padding: 1px 7px; font-weight: 800; }
QLabel#KartUyari  { color: %(kirmizi_acik)s; font-weight: 700; }

/* ------------------------------ Alt konsol ------------------------------ */
QFrame#AltKonsol {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #151A28, stop:1 %(panel)s);
    border-top: 1px solid %(cizgi)s;
}
QLabel#SimdiEtiket { color: %(kirmizi_acik)s; font-size: 10px; font-weight: 800; letter-spacing: 3px; }
QLabel#SimdiAd     { color: %(metin)s; font-size: 20px; font-weight: 800; }
QLabel#SiradakiAd  { color: %(metin_soluk)s; font-size: 12px; }
QLabel#Gecen       { color: %(metin)s; font-size: 13px; font-weight: 700; }
QLabel#Kalan       { color: %(altin)s; font-size: 30px; font-weight: 800; }
QLabel#KalanEtiket { color: %(metin_soluk)s; font-size: 10px; font-weight: 700; letter-spacing: 2px; }
QLabel#MiniEtiket  { color: %(metin_soluk)s; font-size: 10px; font-weight: 700; letter-spacing: 1px; }

/* ------------------------------ Girdi öğeleri ------------------------------ */
QLineEdit {
    background-color: #0E1220;
    border: 1px solid %(cizgi)s;
    border-radius: 10px;
    padding: 8px 12px;
    color: %(metin)s;
    font-size: 13px;
    selection-background-color: %(kirmizi)s;
}
QLineEdit:focus { border-color: %(kirmizi)s; }

QSlider::groove:horizontal {
    height: 6px; border-radius: 3px; background-color: #222A3E;
}
QSlider::sub-page:horizontal {
    height: 6px; border-radius: 3px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 %(kirmizi_koyu)s, stop:1 %(kirmizi_acik)s);
}
QSlider::handle:horizontal {
    background: #FFFFFF; border: none; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}
QSlider::handle:horizontal:hover { background: %(altin)s; }
QSlider#KartSes::groove:horizontal { height: 4px; background-color: #222A3E; }
QSlider#KartSes::handle:horizontal { width: 10px; height: 10px; margin: -3px 0; border-radius: 5px; }
QSlider#KartSes::sub-page:horizontal { height: 4px; }

QProgressBar {
    background-color: #0E1220;
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    border-radius: 3px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 %(kirmizi)s, stop:1 %(altin)s);
}

QCheckBox { color: %(metin_soluk)s; font-size: 12px; font-weight: 600; spacing: 7px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 5px;
    border: 1px solid %(cizgi)s; background-color: #0E1220;
}
QCheckBox::indicator:checked { background-color: %(kirmizi)s; border-color: %(kirmizi_acik)s; }

QSpinBox {
    background-color: #0E1220; border: 1px solid %(cizgi)s; border-radius: 8px;
    padding: 4px 6px; color: %(metin)s; font-size: 12px; font-weight: 600;
}
QSpinBox::up-button, QSpinBox::down-button { width: 14px; background-color: #1B2133; border: none; }

QScrollArea { border: none; background-color: transparent; }
QScrollBar:vertical { background: transparent; width: 12px; margin: 4px; }
QScrollBar::handle:vertical { background: #313A54; border-radius: 6px; min-height: 40px; }
QScrollBar::handle:vertical:hover { background: #46516F; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page { background: none; border: none; }

QMenu {
    background-color: %(kart)s; border: 1px solid %(cizgi)s; border-radius: 10px;
    padding: 6px; color: %(metin)s; font-size: 13px;
}
QMenu::item { padding: 7px 18px; border-radius: 7px; }
QMenu::item:selected { background-color: %(kirmizi_koyu)s; }
QMenu::separator { height: 1px; background: %(cizgi)s; margin: 5px 8px; }

QToolTip {
    background-color: #0E1220; color: %(metin)s;
    border: 1px solid %(cizgi)s; border-radius: 7px; padding: 6px 9px; font-size: 12px;
}

QLabel#BosEkran { color: #55608080; }
QLabel#BosBaslik { color: %(metin_soluk)s; font-size: 17px; font-weight: 700; }
QLabel#BosYazi   { color: #6B7694; font-size: 13px; }

QDialog { background-color: %(panel)s; }
QLabel#YardimBaslik { color: %(metin)s; font-size: 17px; font-weight: 800; }
QLabel#YardimSatir  { color: %(metin_soluk)s; font-size: 13px; }
QLabel#YardimTus    {
    background-color: #0E1220; border: 1px solid %(cizgi)s; border-radius: 6px;
    color: %(altin)s; font-size: 12px; font-weight: 800; padding: 3px 9px;
}
""" % RENKLER


def oynat_dugme_qss(yaricap: int, yazi_px: int) -> str:
    """Kart üzerindeki büyük çal/duraklat düğmesinin biçimi (boyuta göre)."""
    return (
        "QPushButton#KartOynat {"
        "  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
        "              stop:0 #FFFFFF, stop:1 #D7DCEA);"
        "  color: #10131C; border: none; padding: 0px; text-align: center;"
        f" border-radius: {yaricap}px; font-size: {yazi_px}px; font-weight: 900;"
        "}"
        "QPushButton#KartOynat:hover { background: #FFFFFF; }"
    )
