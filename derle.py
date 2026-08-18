from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent


MS_FONTLAR = ("times.ttf", "timesbd.ttf", "timesi.ttf", "timesbi.ttf",
              "arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf",
              "cour.ttf", "courbd.ttf", "couri.ttf", "courbi.ttf")


def fontlari_hazirla() -> None:
    hedef = KOK / "fonts"
    kaynak = Path(r"C:\Windows\Fonts")
    for ad in MS_FONTLAR:
        if not (hedef / ad).exists() and (kaynak / ad).exists():
            shutil.copy2(kaynak / ad, hedef / ad)


def main() -> int:
    fontlari_hazirla()
    for klasor in ("build", "dist"):
        hedef = KOK / klasor
        if hedef.exists():
            shutil.rmtree(hedef, ignore_errors=True)

    komut = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name", "PdfEdit",

        "--add-data", f"{KOK / 'fonts'}{';' if sys.platform == 'win32' else ':'}fonts",
        "--hidden-import", "pymupdf",
        "--collect-binaries", "pymupdf",
    ]

    for modul in (
        "PyQt5", "PyQt6", "PySide2", "shiboken2",
        "tkinter", "matplotlib", "numpy", "scipy", "pandas", "PIL",
        "IPython", "jupyter", "nbformat", "nbconvert", "notebook", "zmq",
        "sphinx", "docutils", "jinja2", "babel", "black", "yapf", "blib2to3",
        "cryptography", "bcrypt", "sqlalchemy", "pytest", "setuptools",
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
        "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml",
        "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization",
        "PySide6.QtNetwork", "PySide6.QtSql", "PySide6.QtTest",
        "PySide6.QtOpenGL", "PySide6.QtPositioning", "PySide6.QtBluetooth",
    ):
        komut += ["--exclude-module", modul]
    komut.append(str(KOK / "giris.py"))
    print(">>", " ".join(komut))
    sonuc = subprocess.run(komut, cwd=KOK)
    if sonuc.returncode == 0:
        print("\nTAMAM ->", KOK / "dist" / "PdfEdit" / "PdfEdit.exe")
    return sonuc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
