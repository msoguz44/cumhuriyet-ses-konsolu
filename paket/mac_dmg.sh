#!/bin/bash
# macOS: .app paketi ve dagitima hazir .dmg uretir.
set -e
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
echo "[1/4] Gerekli araçlar kuruluyor…"
"$PY" -m pip install --upgrade pip >/dev/null
"$PY" -m pip install PySide6 pyinstaller

echo "[2/4] Simgeler üretiliyor…"
"$PY" paket/simge_uret.py

echo "[3/4] Uygulama paketleniyor…"
"$PY" -m PyInstaller paket/CumhuriyetSes.spec --noconfirm --clean

echo "[4/4] DMG hazırlanıyor…"
UYG="dist/Cumhuriyet Ses Konsolu.app"
[ -d "$UYG" ] || { echo "Hata: $UYG bulunamadı."; exit 1; }
# Gatekeeper, indirilen imzasız uygulamaları engellemesin diye geçici imza
codesign --force --deep --sign - "$UYG" 2>/dev/null || true

SAHNE="$(mktemp -d)"
cp -R "$UYG" "$SAHNE/"
ln -s /Applications "$SAHNE/Applications"
rm -f "dist/CumhuriyetSesKonsolu-mac.dmg"
hdiutil create -volname "Cumhuriyet Ses Konsolu" -srcfolder "$SAHNE" \
  -ov -format UDZO "dist/CumhuriyetSesKonsolu-mac.dmg" >/dev/null
rm -rf "$SAHNE"

echo
echo "Bitti!  dist/CumhuriyetSesKonsolu-mac.dmg"
echo "DMG'yi açıp uygulamayı Applications klasörüne sürüklemek yeterli."
