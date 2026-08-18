from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QSettings, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QColorDialog, QComboBox,
                               QDoubleSpinBox, QFileDialog, QGraphicsDropShadowEffect,
                               QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                               QScrollArea, QSizePolicy, QToolBar, QToolButton, QVBoxLayout, QWidget)
from PySide6.QtWidgets import QSizePolicy

from . import pdfio, tema
from .canvas import Tuval
from .fonts import FontDeposu

RESIM_SUZGECI = "Gorseller (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Tum dosyalar (*)"


class AnaPencere(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._tema = str(QSettings("ilker", "PdfEdit").value("tema", "koyu"))
        self.setWindowTitle("PDF Edit")
        self.resize(1180, 900)

        self.tuval = Tuval()
        self._sayfa_sarmalayici = QWidget()
        sayfa_duzeni = QVBoxLayout(self._sayfa_sarmalayici)
        sayfa_duzeni.setContentsMargins(32, 32, 32, 32)
        sayfa_duzeni.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sayfa_duzeni.addWidget(self.tuval, 0, Qt.AlignmentFlag.AlignCenter)
        golge = QGraphicsDropShadowEffect(self.tuval)
        golge.setBlurRadius(24)
        golge.setOffset(0, 6)
        golge.setColor(QColor(0, 0, 0, 90))
        self.tuval.setGraphicsEffect(golge)
        self.kaydirma = QScrollArea()
        self.kaydirma.setWidgetResizable(True)
        self.kaydirma.setWidget(self._sayfa_sarmalayici)
        self.kaydirma.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.kaydirma)

        self.kaynak_yol: Path | None = None
        self.hedef_yol: Path | None = None
        self.degisiklik_var = False

        self._arac_cubugu()
        self._durum = self.statusBar()
        self._durum_kontekst = QLabel()
        self._durum_ipucu = QLabel("Ctrl+O ile bir PDF aç")
        self._durum.addWidget(self._durum_kontekst, 1)
        self._durum.addPermanentWidget(self._durum_ipucu)
        self._durum.addPermanentWidget(self._alt_cubuk)

        self.tuval.durum_degisti.connect(self._durumu_tazele)
        self.tuval.belge_degisti.connect(self._degisiklik_isaretle)
        self._durumu_tazele()
        self._tema_uygula(self._tema)

    def _eylem(self, ad: str, kisayol: str | None, islev, ipucu: str = "") -> QAction:
        e = QAction(ad, self)
        if kisayol:
            e.setShortcut(QKeySequence(kisayol))
        e.setToolTip(ipucu or ad)
        e.triggered.connect(islev)
        self.addAction(e)
        return e

    def _ikonlu_eylem(self, ad: str, ikon: str, kisayol: str | None, islev, ipucu: str = "") -> QAction:
        e = self._eylem(ad, kisayol, islev, ipucu)
        e.setProperty("ikon_adi", ikon)
        e.setIcon(tema.simge(ikon, tema.Tema.koyu["text"]))
        return e

    def _arac_cubugu(self) -> None:
        baslik = QToolBar("Başlık")
        baslik.setObjectName("baslik_cubugu")
        baslik.setMovable(False)
        baslik.setFloatable(False)
        ad = QLabel("PDF Edit")
        ad.setObjectName("uygulama_adi")
        baslik.addWidget(ad)
        self.etiket_dosya = QLabel("Belge açık değil")
        self.etiket_dosya.setObjectName("dosya_adi")
        baslik.addWidget(self.etiket_dosya)
        esnek = QWidget()
        esnek.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        baslik.addWidget(esnek)
        self.eylem_tema = QAction("Tema", self)
        self.eylem_tema.setToolTip("Temayı değiştir")
        self.eylem_tema.triggered.connect(self._tema_degistir)
        self.eylem_tema.setProperty("ikon_adi", "tema")
        self.eylem_tema.setIcon(tema.simge("tema", tema.Tema.koyu["text"]))
        baslik.addAction(self.eylem_tema)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, baslik)

        cubuk = QToolBar("Ana")
        cubuk.setMovable(False)
        cubuk.setFloatable(False)
        cubuk.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        cubuk.setIconSize(QSize(16, 16))
        baslik.setIconSize(QSize(16, 16))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, cubuk)

        ac = self._ikonlu_eylem("Aç", "ac", "Ctrl+O", self.pdf_ac, "PDF aç (Ctrl+O)")
        kaydet = self._ikonlu_eylem("Kaydet", "kaydet", "Ctrl+S", self.kaydet, "Kaydet (Ctrl+S)")
        farkli = self._ikonlu_eylem("Farklı Kaydet", "farkli-kaydet", "Ctrl+Shift+S", self.farkli_kaydet, "Farklı kaydet (Ctrl+Shift+S)")
        cubuk.addAction(ac)
        self.eylem_kaydet = kaydet
        cubuk.addAction(self.eylem_kaydet)
        cubuk.addAction(farkli)
        cubuk.addSeparator()
        cubuk.addAction(self._ikonlu_eylem("Geri Al", "geri", "Ctrl+Z", self.tuval.geri_al, "Geri al (Ctrl+Z)"))
        cubuk.addAction(self._ikonlu_eylem("Yinele", "ileri", "Ctrl+Y", self.tuval.yinele, "Yinele (Ctrl+Y)"))
        cubuk.addSeparator()

        self.kutu_aile = QComboBox()
        self._fontlari_doldur()
        self.kutu_aile.setFixedWidth(180)
        self.kutu_aile.setToolTip("Yazı tipi")
        self.kutu_aile.activated.connect(
            lambda: self.tuval.stil_uygula(aile=self.kutu_aile.currentText()))
        cubuk.addWidget(self.kutu_aile)

        self.kutu_boy = QDoubleSpinBox()
        self.kutu_boy.setRange(3.0, 300.0)
        self.kutu_boy.setDecimals(1)
        self.kutu_boy.setSingleStep(0.5)
        self.kutu_boy.setValue(11.0)
        self.kutu_boy.setSuffix(" pt")
        self.kutu_boy.setToolTip("Punto")
        self.kutu_boy.setFixedWidth(84)
        self.kutu_boy.editingFinished.connect(
            lambda: self.tuval.stil_uygula(boy=self.kutu_boy.value()))
        cubuk.addWidget(self.kutu_boy)

        self.eylem_kalin = QAction("K", self)
        self.eylem_kalin.setProperty("ikon_adi", "kalin")
        self.eylem_kalin.setIcon(tema.simge("kalin", tema.Tema.koyu["text"]))
        self.eylem_kalin.setCheckable(True)
        self.eylem_kalin.setToolTip("Kalın (Ctrl+B)")
        self.eylem_kalin.setShortcut(QKeySequence("Ctrl+B"))
        self.eylem_kalin.triggered.connect(
            lambda: self.tuval.stil_uygula(kalin=self.eylem_kalin.isChecked()))
        cubuk.addAction(self.eylem_kalin)

        self.eylem_egik = QAction("E", self)
        self.eylem_egik.setProperty("ikon_adi", "egik")
        self.eylem_egik.setIcon(tema.simge("egik", tema.Tema.koyu["text"]))
        self.eylem_egik.setCheckable(True)
        self.eylem_egik.setToolTip("Eğik (Ctrl+I)")
        self.eylem_egik.setShortcut(QKeySequence("Ctrl+I"))
        self.eylem_egik.triggered.connect(
            lambda: self.tuval.stil_uygula(egik=self.eylem_egik.isChecked()))
        cubuk.addAction(self.eylem_egik)

        self.eylem_renk = QAction("Renk", self)
        self.eylem_renk.setToolTip("Yazı rengi")
        self.eylem_renk.setProperty("ikon_adi", "renk")
        self.eylem_renk.setIcon(tema.simge("renk", tema.Tema.koyu["text"]))
        self.eylem_renk.triggered.connect(self.renk_sec)
        cubuk.addAction(self.eylem_renk)
        cubuk.addSeparator()

        resim = self._ikonlu_eylem("Resim Ekle", "resim", "Ctrl+M", self.resim_ekle,
                                   "Resim ekle (Ctrl+M) — sürükleyerek taşı, köşeden boyutlandır")
        cubuk.addAction(resim)
        cubuk.addSeparator()

        self.kutu_itme = QCheckBox("Blokları it")
        self.kutu_itme.setChecked(True)
        self.kutu_itme.setToolTip(
            "Bir blok büyüdüğünde altındaki bloklar aşağı kaysın. "
            "Çok sütunlu düzenlerde kapatmak isteyebilirsin.")
        self.kutu_itme.toggled.connect(self._itme_degisti)
        cubuk.addWidget(self.kutu_itme)

        alt = QToolBar("Gezinme")
        alt.setObjectName("alt_cubuk")
        alt.setMovable(False)
        alt.setFloatable(False)
        alt.setIconSize(QSize(16, 16))
        alt.addAction(self._ikonlu_eylem("Önceki", "onceki", "PgUp",
                                         lambda: self.tuval.sayfaya_git(self.tuval.sayfa_no - 1),
                                         "Önceki sayfa (PgUp)"))
        self.etiket_sayfa = QLabel("– / –")
        self.etiket_sayfa.setMinimumWidth(48)
        self.etiket_sayfa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt.addWidget(self.etiket_sayfa)
        alt.addAction(self._ikonlu_eylem("Sonraki", "sonraki", "PgDown",
                                         lambda: self.tuval.sayfaya_git(self.tuval.sayfa_no + 1),
                                         "Sonraki sayfa (PgDown)"))
        alt.addSeparator()
        alt.addAction(self._ikonlu_eylem("Küçült", "kucult", "Ctrl+-",
                                         lambda: self.tuval.zoom_ayarla(self.tuval.zoom / 1.15),
                                         "Uzaklaştır (Ctrl+-)"))
        self.etiket_zoom = QLabel("%150")
        self.etiket_zoom.setMinimumWidth(44)
        self.etiket_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt.addWidget(self.etiket_zoom)
        alt.addAction(self._ikonlu_eylem("Büyüt", "buyut", "Ctrl++",
                                         lambda: self.tuval.zoom_ayarla(self.tuval.zoom * 1.15),
                                         "Yakınlaştır (Ctrl++)"))
        self._alt_cubuk = alt

    def _fontlari_doldur(self) -> None:
        secili = self.kutu_aile.currentText() if hasattr(self, "kutu_aile") else ""
        if hasattr(self, "kutu_aile"):
            self.kutu_aile.blockSignals(True)
            self.kutu_aile.clear()
        else:
            self.kutu_aile = QComboBox()
        for aile in FontDeposu.al().aileler():
            i = self.kutu_aile.count()
            self.kutu_aile.addItem(aile)
            self.kutu_aile.setItemData(i, QFont(aile), Qt.ItemDataRole.FontRole)
        if secili:
            self.kutu_aile.setCurrentText(secili)
        self.kutu_aile.blockSignals(False)

    def _tema_uygula(self, ad: str) -> None:
        self._tema = ad if ad in ("koyu", "acik") else "koyu"
        tema.tema_uygula(QApplication.instance(), self._tema)
        token = tema.Tema.acik if self._tema == "acik" else tema.Tema.koyu
        self.tuval.renkleri_ayarla(token)
        self.eylem_tema.setIcon(tema.simge("tema", token["text"]))
        for e in self.findChildren(QAction):
            ikon = e.property("ikon_adi")
            if ikon:
                e.setIcon(tema.simge(ikon, token["text"]))
        golge = self.tuval.graphicsEffect()
        if isinstance(golge, QGraphicsDropShadowEffect):
            golge.setColor(QColor(token["shadow"]))
        self._durumu_tazele()

    def _tema_degistir(self) -> None:
        self._tema_uygula("acik" if self._tema == "koyu" else "koyu")

    def pdf_ac(self) -> None:
        yol, _ = QFileDialog.getOpenFileName(self, "PDF ac", str(Path.home()),
                                             "PDF dosyalari (*.pdf)")
        if not yol:
            return
        self.pdf_yukle(yol)

    def pdf_yukle(self, yol: str) -> None:
        try:
            belge = pdfio.yukle(yol)
            arkaplan = pdfio.arkaplan_belgesi(yol)
            if self.tuval.arkaplan_doc is not None:
                self.tuval.arkaplan_doc.close()
        except Exception as hata:  # noqa: BLE001
            QMessageBox.critical(self, "Acilamadi", f"PDF okunamadi:\n{hata}")
            return
        self.kaynak_yol = Path(yol)
        self.hedef_yol = self.kaynak_yol.with_name(self.kaynak_yol.stem + "-duzenlenmis.pdf")
        belge.itme_acik = self.kutu_itme.isChecked()
        self.tuval.belge_yukle(belge, arkaplan)
        self._fontlari_doldur()
        self.degisiklik_var = False
        self._basligi_tazele()
        self._durum_ipucu.setText(f"{self.kaynak_yol.name} açıldı · Kaydet: {self.hedef_yol.name}")

    def kaydet(self) -> None:
        if not self.tuval.belge or not self.hedef_yol:
            return
        self._kaydet_yola(self.hedef_yol)

    def farkli_kaydet(self) -> None:
        if not self.tuval.belge:
            return
        onerilen = str(self.hedef_yol or Path.home() / "cikti.pdf")
        yol, _ = QFileDialog.getSaveFileName(self, "Farkli kaydet", onerilen,
                                             "PDF dosyalari (*.pdf)")
        if yol:
            self.hedef_yol = Path(yol)
            self._kaydet_yola(self.hedef_yol)

    def _kaydet_yola(self, yol: Path) -> None:
        if self.kaynak_yol and yol.resolve() == self.kaynak_yol.resolve():
            QMessageBox.warning(
                self, "Ustune yazilamaz",
                "Kaynak PDF acikken uzerine yazilamaz.\n"
                "Lutfen 'Farkli Kaydet' ile baska bir ad sec.")
            return
        try:
            pdfio.kaydet(self.tuval.belge, str(yol))
        except Exception as hata:  # noqa: BLE001
            QMessageBox.critical(self, "Kaydedilemedi", f"Yazma hatasi:\n{hata}")
            return
        self.degisiklik_var = False
        self._basligi_tazele()
        self._durum_kontekst.setText("Kaydedildi ✓")
        self._durum_kontekst.setStyleSheet(f"color: {tema.Tema.acik['accent'] if self._tema == 'acik' else tema.Tema.koyu['accent']};")
        QTimer.singleShot(3000, self._durumu_tazele)

    def resim_ekle(self) -> None:
        if not self.tuval.belge:
            QMessageBox.information(self, "Once PDF ac", "Resim eklemek icin once bir PDF ac.")
            return
        yol, _ = QFileDialog.getOpenFileName(self, "Gorsel sec", str(Path.home()), RESIM_SUZGECI)
        if yol:
            self.tuval.resim_ekle(yol)
            self._durum.showMessage(
                "Resim eklendi - surukleyerek tasi, koselerden boyutlandir "
                "(Shift = orani koru), Delete ile sil", 8000)

    def renk_sec(self) -> None:
        stil = self.tuval.gecerli_stil()
        baslangic = QColor(stil.renk) if stil else QColor("#000000")
        renk = QColorDialog.getColor(baslangic, self, "Yazi rengi")
        if renk.isValid():
            self.tuval.stil_uygula(renk=renk.rgb() & 0xFFFFFF)

    def _itme_degisti(self, acik: bool) -> None:
        if self.tuval.belge:
            self.tuval.belge.itme_acik = acik
            for sayfa in self.tuval.belge.sayfalar:
                sayfa.kaymalari_hesapla(acik)
            self.tuval.metni_tazele()

    def _degisiklik_isaretle(self) -> None:
        self.degisiklik_var = True
        self._basligi_tazele()

    def _basligi_tazele(self) -> None:
        ad = self.kaynak_yol.name if self.kaynak_yol else "PDF Edit"
        yildiz = " *" if self.degisiklik_var else ""
        self.setWindowTitle(f"{ad}{yildiz} - PDF Edit")
        if hasattr(self, "etiket_dosya"):
            self.etiket_dosya.setText(f"{ad}{yildiz}" if self.kaynak_yol else "Belge açık değil")

    def _durumu_tazele(self) -> None:
        belge = self.tuval.belge
        stil = self.tuval.gecerli_stil()
        aile = stil.aile if stil else "Georgia"
        boy = stil.boy if stil else 10.2
        sayfa = f"{self.tuval.sayfa_no + 1}/{len(belge.sayfalar)}" if belge else "-/-"
        self._durum_kontekst.setText(f"{aile} · {boy:.1f}pt · Sayfa {sayfa}")
        self._durum_kontekst.setStyleSheet("")
        if belge:
            self.etiket_sayfa.setText(f" {self.tuval.sayfa_no + 1} / {len(belge.sayfalar)} ")
        self.etiket_zoom.setText(f" %{int(self.tuval.zoom * 100)} ")

        bloke = (self.kutu_aile, self.kutu_boy, self.eylem_kalin, self.eylem_egik)
        for w in bloke:
            w.blockSignals(True)
        if stil is not None:
            self.kutu_aile.setCurrentText(stil.aile)
            self.kutu_boy.setValue(stil.boy)
            self.eylem_kalin.setChecked(stil.kalin)
            self.eylem_egik.setChecked(stil.egik)
            self.eylem_renk.setIcon(self._renk_simgesi(stil.renk))
        for w in bloke:
            w.blockSignals(False)

    @staticmethod
    def _renk_simgesi(renk: int) -> QIcon:
        pix = QPixmap(16, 16)
        pix.fill(QColor(renk | 0xFF000000))
        return QIcon(pix)

    def closeEvent(self, olay) -> None:
        if not self.degisiklik_var:
            olay.accept()
            return
        cevap = QMessageBox.question(
            self, "Kaydedilmemis degisiklikler",
            "Degisiklikler kaydedilmedi. Yine de cikilsin mi?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel)
        if cevap == QMessageBox.StandardButton.Save:
            self.kaydet()
            olay.accept()
        elif cevap == QMessageBox.StandardButton.Discard:
            olay.accept()
        else:
            olay.ignore()
