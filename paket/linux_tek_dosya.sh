#!/bin/bash
# Linux: tek dosyalik calistirilabilir uretir (istege bagli AppImage).
set -e
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
echo "[1/4] Gerekli araçlar kuruluyor…"
"$PY" -m pip install --upgrade pip >/dev/null
"$PY" -m pip install PySide6 pyinstaller

echo "[2/4] Simgeler üretiliyor…"
"$PY" paket/simge_uret.py

echo "[3/4] Tek dosya derleniyor…"
"$PY" -m PyInstaller paket/CumhuriyetSes.spec --noconfirm --clean
chmod +x dist/CumhuriyetSesKonsolu

echo "[4/4] AppImage (appimagetool varsa)…"
if command -v appimagetool >/dev/null; then
  KOK="build/AppDir"
  rm -rf "$KOK"; mkdir -p "$KOK/usr/bin"
  cp dist/CumhuriyetSesKonsolu "$KOK/usr/bin/"
  cp paket/app.png "$KOK/cumhuriyet-ses.png"
  cat > "$KOK/cumhuriyet-ses.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Cumhuriyet Ses Konsolu
Exec=CumhuriyetSesKonsolu
Icon=cumhuriyet-ses
Categories=AudioVideo;Audio;Player;
Terminal=false
DESKTOP
  printf '#!/bin/sh\nexec "$APPDIR/usr/bin/CumhuriyetSesKonsolu" "$@"\n' > "$KOK/AppRun"
  chmod +x "$KOK/AppRun"
  appimagetool "$KOK" dist/CumhuriyetSesKonsolu-linux-x86_64.AppImage
  echo "AppImage: dist/CumhuriyetSesKonsolu-linux-x86_64.AppImage"
else
  echo "appimagetool bulunamadı — tek dosya zaten hazır, AppImage atlandı."
fi

echo
echo "Bitti!  dist/CumhuriyetSesKonsolu  (çift tıklayın ya da ./CumhuriyetSesKonsolu)"
