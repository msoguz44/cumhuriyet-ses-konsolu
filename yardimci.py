"""Küçük ortak yardımcılar."""


def sure_metni(ms: int) -> str:
    """12345 -> '0:12'  /  3725000 -> '1:02:05'"""
    if ms is None or ms <= 0:
        return "0:00"
    toplam = int(ms // 1000)
    sa, kalan = divmod(toplam, 3600)
    dk, sn = divmod(kalan, 60)
    if sa:
        return f"{sa}:{dk:02d}:{sn:02d}"
    return f"{dk}:{sn:02d}"


def kisalt(metin: str, uzunluk: int) -> str:
    metin = (metin or "").strip()
    return metin if len(metin) <= uzunluk else metin[: uzunluk - 1] + "…"


def odagi_kapat(kok, *turler):
    """Verilen tipteki alt bileşenlerin klavye odağını kapatır.

    Böylece Boşluk / yön tuşları düğmelere değil, pencerenin kendisine gider.
    """
    from PySide6.QtCore import Qt

    for tur in turler:
        for bilesen in kok.findChildren(tur):
            bilesen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
