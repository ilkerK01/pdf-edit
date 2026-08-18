from __future__ import annotations

import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pymupdf as fitz
from PySide6.QtGui import QFont, QFontDatabase


def kaynak_dizini() -> Path:

    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


FONT_DIZINI = kaynak_dizini() / "fonts"


GOMULU: dict[str, tuple[str, str, str, str]] = {
    "Times New Roman": ("times.ttf", "timesbd.ttf", "timesi.ttf", "timesbi.ttf"),
    "Arial": ("arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf"),
    "Courier New": ("cour.ttf", "courbd.ttf", "couri.ttf", "courbi.ttf"),
    "JetBrains Mono": (
        "JetBrainsMonoNerdFont-Regular.ttf",
        "JetBrainsMonoNerdFont-Bold.ttf",
        "JetBrainsMonoNerdFont-Italic.ttf",
        "JetBrainsMonoNerdFont-BoldItalic.ttf",
    ),
}

VARSAYILAN_AILE = "Times New Roman"


ESLESME: list[tuple[tuple[str, ...], str]] = [
    (("jetbrains", "cascadia", "fira", "hack", "inconsolata", "sourcecode"), "JetBrains Mono"),
    (("courier", "mono", "typewriter", "consol"), "Courier New"),
    (("times", "serif", "georgia", "garamond", "roman", "minion", "cambria",
      "book", "palatino", "century", "constantia"), "Times New Roman"),
    (("arial", "helvetica", "sans", "calibri", "verdana", "segoe", "roboto",
      "tahoma", "futura", "gill", "myriad", "lato", "opensans", "inter"), "Arial"),
]


SONEK_KALIN = ("bd", "b", "-bold", "bold")
SONEK_EGIK = ("i", "it", "-italic", "italic", "-oblique")
SONEK_KALIN_EGIK = ("z", "bi", "bd i", "-bolditalic", "bolditalic", "bdit")

SISTEM_DIZINLERI = [
    Path(r"C:\Windows\Fonts"),
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
]


def _gomulu_yol(ad: str) -> Path:
    yerel = FONT_DIZINI / ad
    if yerel.exists():
        return yerel
    for dizin in SISTEM_DIZINLERI:
        aday = dizin / ad
        if aday.exists():
            return aday
    return yerel


def _normalize(ad: str) -> str:
    return "".join(ch for ch in ad.lower() if ch.isalnum())


@dataclass(frozen=True)
class FontAnahtari:
    aile: str
    kalin: bool
    egik: bool


@lru_cache(maxsize=1)
def _sistem_haritasi() -> dict[str, Path]:

    harita: dict[str, Path] = {}
    for dizin in SISTEM_DIZINLERI:
        if not dizin.is_dir():
            continue
        try:
            for yol in dizin.iterdir():
                if yol.suffix.lower() in (".ttf", ".otf"):
                    harita.setdefault(_normalize(yol.stem), yol)
        except OSError:
            continue
    return harita


def _sistem_ailesi(taban: str) -> tuple[Path, Path, Path, Path] | None:

    harita = _sistem_haritasi()
    normal = harita.get(taban)
    if normal is None:
        return None

    def ara(sonekler: tuple[str, ...]) -> Path:
        for s in sonekler:
            bulunan = harita.get(taban + _normalize(s))
            if bulunan is not None:
                return bulunan
        return normal

    return normal, ara(SONEK_KALIN), ara(SONEK_EGIK), ara(SONEK_KALIN_EGIK)


class FontDeposu:

    _tekil: "FontDeposu | None" = None

    def __init__(self) -> None:
        self._yollar: dict[str, tuple[Path, Path, Path, Path]] = {
            aile: tuple(_gomulu_yol(ad) for ad in dosyalar)  # type: ignore[misc]
            for aile, dosyalar in GOMULU.items()
        }
        self._gomulu_adlar = list(GOMULU.keys())
        self._kesfedilen: list[str] = []
        self._mu: dict[FontAnahtari, fitz.Font] = {}
        self._qt_aile: dict[str, str] = {}
        self._coz_onbellek: dict[tuple[str, int], tuple[str, bool, bool]] = {}

    @classmethod
    def al(cls) -> "FontDeposu":
        if cls._tekil is None:
            cls._tekil = FontDeposu()
        return cls._tekil

    def qt_kaydet(self) -> None:

        for aile in self._gomulu_adlar:
            self._qt_tanit(aile)

    def _qt_tanit(self, aile: str) -> None:
        if aile in self._qt_aile or aile not in self._yollar:
            return
        adlar: list[str] = []
        for yol in self._yollar[aile]:
            if not yol.exists():
                continue
            kimlik = QFontDatabase.addApplicationFont(str(yol))
            if kimlik != -1:
                adlar.extend(QFontDatabase.applicationFontFamilies(kimlik))
        self._qt_aile[aile] = adlar[0] if adlar else aile

    def aile_ekle(self, ad: str, yollar: tuple[Path, Path, Path, Path]) -> None:
        if ad in self._yollar:
            return
        self._yollar[ad] = yollar
        self._kesfedilen.append(ad)

    def aileler(self) -> list[str]:

        return self._gomulu_adlar + sorted(self._kesfedilen)

    def dosya_yolu(self, aile: str, kalin: bool = False, egik: bool = False) -> Path:
        yollar = self._yollar.get(aile) or self._yollar[VARSAYILAN_AILE]
        indeks = (2 if egik else 0) + (1 if kalin else 0)
        secili = yollar[indeks]
        return secili if secili.exists() else yollar[0]

    def mu(self, aile: str, kalin: bool = False, egik: bool = False) -> fitz.Font:

        anahtar = FontAnahtari(aile if aile in self._yollar else VARSAYILAN_AILE, kalin, egik)
        font = self._mu.get(anahtar)
        if font is None:
            try:
                font = fitz.Font(fontfile=str(self.dosya_yolu(anahtar.aile, kalin, egik)))
            except Exception:  # noqa: BLE001 - bozuk font dosyasi
                font = fitz.Font(fontfile=str(self.dosya_yolu(VARSAYILAN_AILE, kalin, egik)))
            self._mu[anahtar] = font
        return font

    def qt(self, aile: str, kalin: bool, egik: bool, piksel: float) -> QFont:

        self._qt_tanit(aile)
        f = QFont(self._qt_aile.get(aile, aile))
        f.setPixelSize(max(1, int(round(piksel))))
        f.setBold(kalin)
        f.setItalic(egik)
        f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        f.setKerning(False)
        return f

    def coz(self, pdf_adi: str, bayraklar: int) -> tuple[str, bool, bool]:

        onbellek_anahtari = (pdf_adi, bayraklar)
        hazir = self._coz_onbellek.get(onbellek_anahtari)
        if hazir is not None:
            return hazir
        sonuc = self._coz_hesapla(pdf_adi, bayraklar)
        self._coz_onbellek[onbellek_anahtari] = sonuc
        return sonuc

    def _coz_hesapla(self, pdf_adi: str, bayraklar: int) -> tuple[str, bool, bool]:
        ham = (pdf_adi or "").split("+")[-1]
        govde = ham.split(",")[0].split("-")[0]
        dusuk = _normalize(ham)
        taban = _normalize(govde)

        kalin = bool(bayraklar & 16) or any(
            k in dusuk for k in ("bold", "black", "heavy", "semibold", "demibold"))
        egik = bool(bayraklar & 2) or any(k in dusuk for k in ("italic", "oblique"))

        for aday in (taban, dusuk):
            if not aday:
                continue
            if aday in self._yollar:
                return aday, kalin, egik
            bulunan = _sistem_ailesi(aday)
            if bulunan is not None:
                ad = govde or ham
                self.aile_ekle(ad, bulunan)
                if _normalize(ad) != aday:
                    self.aile_ekle(aday, bulunan)
                return ad, kalin, egik

        for aile in self._yollar:
            if _normalize(aile) == taban:
                return aile, kalin, egik

        for anahtarlar, aile in ESLESME:
            if any(k in dusuk for k in anahtarlar):
                return aile, kalin, egik
        if bayraklar & 8:
            return "Courier New", kalin, egik
        if bayraklar & 4:
            return "Times New Roman", kalin, egik
        return VARSAYILAN_AILE, kalin, egik


def pdf_fontu_esle(pdf_adi: str, bayraklar: int) -> tuple[str, bool, bool]:
    return FontDeposu.al().coz(pdf_adi, bayraklar)
