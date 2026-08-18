from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .fonts import FontDeposu
from .window import AnaPencere


def main() -> int:
    uygulama = QApplication(sys.argv)
    uygulama.setApplicationName("PDF Edit")
    uygulama.setOrganizationName("ilker")

    FontDeposu.al().qt_kaydet()

    pencere = AnaPencere()
    pencere.show()

    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".pdf"):
        pencere.pdf_yukle(sys.argv[1])

    return uygulama.exec()


if __name__ == "__main__":
    raise SystemExit(main())
