#!/bin/bash
# macOS için başlatıcı (çift tıklayın)
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Python3 bulunamadı."; read -r; exit 1; }
python3 -c "import PySide6" 2>/dev/null || python3 -m pip install --user PySide6
exec python3 main.py
