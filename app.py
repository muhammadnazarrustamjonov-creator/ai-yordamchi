import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --disable-dev-shm-usage"

import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
browser = QWebEngineView()
browser.setUrl(QUrl("https://ai-yordamchi-1-tqs3.onrender.com"))
browser.setWindowTitle("Steve - Sun'iy Intellekt")
browser.resize(400, 700)
browser.show()
sys.exit(app.exec())