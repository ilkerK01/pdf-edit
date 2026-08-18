from __future__ import annotations

import re

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QCursor, QGuiApplication, QImage, QPainter,
                           QPen, QPixmap)
from PySide6.QtWidgets import QWidget

from .fonts import FontDeposu
from .model import Belge, MetinBloku, ResimNesnesi, Stil

TUTAMAC = 7.0


class Tuval(QWidget):
    durum_degisti = Signal()
    belge_degisti = Signal()
    renkler = {
        "accent": "#6d8bff",
        "accent_soft": "rgba(109,139,255,0.16)",
        "imlec": "#111111",
        "tutamac_kenar": "#6d8bff",
        "blok_cerceve": "rgba(109,139,255,0.35)",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.IBeamCursor)

        self.belge: Belge | None = None
        self.arkaplan_doc = None
        self.sayfa_no = 0
        self.zoom = 1.5

        self.aktif_blok: MetinBloku | None = None
        self.imlec = 0
        self.capa = 0
        self.zorlanan_stil: Stil | None = None

        self.mod = "metin"
        self.tasinan = None
        self._surukleme = None
        self._metin_secimi = False
        self._yazim_acik = False
        self._tercih_x: float | None = None

        self._ap_pix: QPixmap | None = None
        self._ap_anahtar = None
        self._metin_pix: QPixmap | None = None
        self._metin_anahtar = None
        self._resim_onbellek: dict[str, QPixmap] = {}

        self._vurgu = None
        self._imlec_gorunur = True
        self._zamanlayici = QTimer(self)
        self._zamanlayici.timeout.connect(self._imlec_yanip_son)
        self._zamanlayici.start(530)

    @property
    def secili_resim(self):
        return self.tasinan if isinstance(self.tasinan, ResimNesnesi) else None

    @secili_resim.setter
    def secili_resim(self, deger) -> None:
        self.tasinan = deger

    @property
    def secili_blok(self):
        return self.tasinan if isinstance(self.tasinan, MetinBloku) else None

    def mod_ayarla(self, ad: str) -> None:
        self.mod = "tasi" if ad == "tasi" else "metin"
        if self.mod == "tasi":
            self.aktif_blok = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.tasinan = None
            self.setCursor(Qt.CursorShape.IBeamCursor)
        self.update()
        self.durum_degisti.emit()

    def secimi_ayir(self) -> bool:
        blok = self.aktif_blok
        if blok is None or self.imlec == self.capa or not self.belge:
            return False
        bas, son = sorted((self.imlec, self.capa))
        self.belge.isaretle()
        yeni = blok.ayir(bas, son)
        if yeni is None:
            return False
        self.sayfa.bloklar.append(yeni)
        self.aktif_blok = None
        self.imlec = self.capa = 0
        self.tasinan = yeni
        self.mod = "tasi"
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._degisti()
        return True

    def renkleri_ayarla(self, renkler: dict[str, str]) -> None:
        self.renkler = {**self.renkler, **renkler}
        self.update()

    def _renk(self, ad: str) -> QColor:
        deger = self.renkler.get(ad, "#000000")
        m = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)", deger)
        if m:
            r, g, b = int(m[1]), int(m[2]), int(m[3])
            a = int(round(float(m[4]) * 255)) if m[4] else 255
            return QColor(r, g, b, a)
        return QColor(deger)

    def belge_yukle(self, belge: Belge, arkaplan_doc) -> None:
        self.belge = belge
        self.arkaplan_doc = arkaplan_doc
        self.sayfa_no = 0
        self.aktif_blok = None
        self.imlec = self.capa = 0
        self.secili_resim = None
        self._onbellek_temizle()
        self.boyut_guncelle()
        self.durum_degisti.emit()

    @property
    def sayfa(self):
        if not self.belge:
            return None
        return self.belge.sayfalar[self.sayfa_no]

    def sayfaya_git(self, no: int) -> None:
        if not self.belge:
            return
        no = max(0, min(no, len(self.belge.sayfalar) - 1))
        if no == self.sayfa_no:
            return
        self.sayfa_no = no
        self.aktif_blok = None
        self.secili_resim = None
        self.imlec = self.capa = 0
        self._onbellek_temizle()
        self.boyut_guncelle()
        self.durum_degisti.emit()

    def zoom_ayarla(self, z: float) -> None:
        self.zoom = max(0.25, min(6.0, z))
        self._onbellek_temizle()
        self.boyut_guncelle()
        self.durum_degisti.emit()

    def boyut_guncelle(self) -> None:
        s = self.sayfa
        if s:
            self.setFixedSize(int(s.genislik * self.zoom) + 1, int(s.yukseklik * self.zoom) + 1)
            if self.parentWidget() is not None:
                self.parentWidget().adjustSize()
        self.update()

    def _onbellek_temizle(self) -> None:
        self._ap_pix = None
        self._ap_anahtar = None
        self._metin_pix = None
        self._metin_anahtar = None

    def metni_tazele(self) -> None:
        self._metin_pix = None
        self._metin_anahtar = None
        self.update()

    def p2e(self, x: float, y: float) -> QPointF:
        return QPointF(x * self.zoom, y * self.zoom)

    def e2p(self, nokta) -> tuple[float, float]:
        return nokta.x() / self.zoom, nokta.y() / self.zoom

    def _arkaplan(self) -> QPixmap | None:
        if not self.arkaplan_doc:
            return None
        anahtar = (self.sayfa_no, round(self.zoom, 3))
        if self._ap_pix is not None and self._ap_anahtar == anahtar:
            return self._ap_pix
        import pymupdf as fitz
        sayfa = self.arkaplan_doc[self.sayfa_no]
        pix = sayfa.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom), alpha=False)
        goruntu = QImage(pix.samples, pix.width, pix.height, pix.stride,
                         QImage.Format.Format_RGB888).copy()
        self._ap_pix = QPixmap.fromImage(goruntu)
        self._ap_anahtar = anahtar
        return self._ap_pix

    def _metin_katmani(self) -> QPixmap | None:
        s = self.sayfa
        if not s:
            return None
        anahtar = (self.sayfa_no, round(self.zoom, 3), self._metin_surumu())
        if self._metin_pix is not None and self._metin_anahtar == anahtar:
            return self._metin_pix

        oran = self.devicePixelRatioF()
        pix = QPixmap(int(self.width() * oran), int(self.height() * oran))
        pix.setDevicePixelRatio(oran)
        pix.fill(Qt.GlobalColor.transparent)

        depo = FontDeposu.al()
        boyaci = QPainter(pix)
        boyaci.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        for blok in s.bloklar:
            ust_kayma = blok.y0 + blok.dy
            for satir in blok.duzen():
                taban = (ust_kayma + satir.taban) * self.zoom
                for k in range(satir.bas, satir.son):
                    ch = blok.metin[k]
                    if ch == "\n" or not ch.strip():
                        continue
                    st = blok.stiller[k]
                    boyaci.setFont(depo.qt(st.aile, st.kalin, st.egik, st.boy * self.zoom))
                    boyaci.setPen(QColor(st.renk | 0xFF000000))
                    boyaci.drawText(QPointF(satir.xler[k - satir.bas] * self.zoom, taban), ch)
        boyaci.end()

        self._metin_pix = pix
        self._metin_anahtar = anahtar
        return pix

    def _metin_surumu(self) -> int:
        s = self.sayfa
        if not s:
            return 0
        return hash(tuple((b.metin, round(b.x0, 2), round(b.x1, 2), round(b.y0, 2),
                           round(b.dy, 2), len(b.stiller)) for b in s.bloklar))

    def _resim_pix(self, yol: str) -> QPixmap:
        pix = self._resim_onbellek.get(yol)
        if pix is None:
            pix = QPixmap(yol)
            self._resim_onbellek[yol] = pix
        return pix

    def paintEvent(self, olay) -> None:
        boyaci = QPainter(self)
        boyaci.fillRect(self.rect(), QColor("#ffffff"))
        if not self.belge:
            boyaci.setPen(QColor("#888"))
            boyaci.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                            "PDF acmak icin Ctrl+O")
            return

        ap = self._arkaplan()
        if ap:
            boyaci.drawPixmap(0, 0, ap)
        mk = self._metin_katmani()
        if mk:
            boyaci.drawPixmap(0, 0, mk)

        for resim in self.sayfa.resimler:
            x0, y0, x1, y1 = resim.sinirlar()
            hedef = QRectF(self.p2e(x0, y0), self.p2e(x1, y1))
            boyaci.drawPixmap(hedef, self._resim_pix(resim.yol),
                              QRectF(self._resim_pix(resim.yol).rect()))
            if resim is self.secili_resim:
                boyaci.setPen(QPen(self._renk("accent"), 1.5, Qt.PenStyle.DashLine))
                boyaci.setBrush(Qt.BrushStyle.NoBrush)
                boyaci.drawRect(hedef)
                boyaci.setPen(QPen(self._renk("tutamac_kenar"), 1))
                boyaci.setBrush(QColor("#ffffff"))
                for kose in self._tutamaclar(resim):
                    boyaci.drawRect(kose)

        if self.aktif_blok is not None:
            bx0, by0, bx1, by1 = self.aktif_blok.sinirlar()
            cerceve = QRectF(self.p2e(bx0, by0), self.p2e(bx1, by1))
            boyaci.setPen(QPen(self._renk("blok_cerceve"), 1, Qt.PenStyle.DashLine))
            boyaci.setBrush(Qt.BrushStyle.NoBrush)
            boyaci.drawRect(cerceve.adjusted(-2, -2, 2, 2))

        secili = self.secili_blok
        if secili is not None:
            bx0, by0, bx1, by1 = secili.sinirlar()
            cerceve = QRectF(self.p2e(bx0, by0), self.p2e(bx1, by1)).adjusted(-3, -3, 3, 3)
            boyaci.setPen(QPen(self._renk("accent"), 1.5, Qt.PenStyle.DashLine))
            boyaci.setBrush(Qt.BrushStyle.NoBrush)
            boyaci.drawRect(cerceve)
            boyaci.setPen(QPen(self._renk("tutamac_kenar"), 1))
            boyaci.setBrush(QColor("#ffffff"))
            for nokta in (cerceve.topLeft(), cerceve.topRight(),
                          cerceve.bottomLeft(), cerceve.bottomRight()):
                boyaci.drawRect(QRectF(nokta.x() - TUTAMAC / 2, nokta.y() - TUTAMAC / 2,
                                       TUTAMAC, TUTAMAC))

        if self.mod == "tasi" and self._vurgu is not None and self._vurgu is not self.tasinan:
            vx0, vy0, vx1, vy1 = self._vurgu.sinirlar()
            boyaci.setPen(QPen(self._renk("blok_cerceve"), 1))
            boyaci.setBrush(Qt.BrushStyle.NoBrush)
            boyaci.drawRect(QRectF(self.p2e(vx0, vy0), self.p2e(vx1, vy1)).adjusted(-3, -3, 3, 3))

        self._secimi_ciz(boyaci)

        if self.aktif_blok is not None and self._imlec_gorunur and self.imlec == self.capa:
            x, y, h = self.aktif_blok.indeks_noktasi(self.imlec)
            ust = self.p2e(x, y)
            boyaci.setPen(QPen(self._renk("imlec"), 1.4))
            boyaci.drawLine(ust, QPointF(ust.x(), ust.y() + h * self.zoom))

    def _secimi_ciz(self, boyaci: QPainter) -> None:
        blok = self.aktif_blok
        if blok is None or self.imlec == self.capa:
            return
        bas, son = sorted((self.imlec, self.capa))
        boyaci.setPen(Qt.PenStyle.NoPen)
        boyaci.setBrush(self._renk("accent_soft"))
        ust_kayma = blok.y0 + blok.dy
        for satir in blok.duzen():
            a, b = max(bas, satir.bas), min(son, satir.son)
            if a >= b:
                continue
            x1 = satir.xler[a - satir.bas]
            x2 = satir.xler[b - satir.bas]
            boyaci.drawRect(QRectF(self.p2e(x1, ust_kayma + satir.ust),
                                   self.p2e(x2, ust_kayma + satir.ust + satir.yuk)))

    def _tutamaclar(self, resim: ResimNesnesi) -> list[QRectF]:
        x0, y0, x1, y1 = resim.sinirlar()
        noktalar = [self.p2e(x0, y0), self.p2e(x1, y0), self.p2e(x0, y1), self.p2e(x1, y1)]
        return [QRectF(n.x() - TUTAMAC / 2, n.y() - TUTAMAC / 2, TUTAMAC, TUTAMAC)
                for n in noktalar]

    def _imlec_yanip_son(self) -> None:
        self._imlec_gorunur = not self._imlec_gorunur
        if self.aktif_blok is not None:
            self.update()

    def mousePressEvent(self, olay) -> None:
        if not self.belge or olay.button() != Qt.MouseButton.LeftButton:
            return
        self.setFocus()
        px, py = self.e2p(olay.position())
        alt = bool(olay.modifiers() & Qt.KeyboardModifier.AltModifier)
        tasi_modu = self.mod == "tasi" or alt

        if self.secili_resim is not None:
            for i, tut in enumerate(self._tutamaclar(self.secili_resim)):
                if tut.contains(olay.position()):
                    self.belge.isaretle()
                    self._surukleme = ("boyut", i, (px, py), self.secili_resim.sinirlar())
                    return

        resim = self.sayfa.resim_bul(px, py)
        if resim is not None:
            self.belge.isaretle()
            self.secili_resim = resim
            self.aktif_blok = None
            self._surukleme = ("tasi", 0, (px, py), resim.sinirlar())
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.update()
            self.durum_degisti.emit()
            return

        if tasi_modu:
            hedef = self.sayfa.blok_bul(px, py)
            self.aktif_blok = None
            self.tasinan = hedef
            if hedef is not None:
                self.belge.isaretle()
                self._surukleme = ("tasi", 0, (px, py), hedef.sinirlar())
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.update()
            self.durum_degisti.emit()
            return

        self.tasinan = None
        blok = self.sayfa.blok_bul(px, py) or self.sayfa.en_yakin_blok(px, py)
        self.aktif_blok = blok
        if blok is not None:
            self.imlec = self.capa = blok.nokta_indeksi(px, py)
        self.zorlanan_stil = None
        self._yazim_acik = False
        self._tercih_x = None
        self._metin_secimi = True
        self._imlec_gorunur = True
        self.update()
        self.durum_degisti.emit()

    def mouseMoveEvent(self, olay) -> None:
        if not self.belge:
            return
        px, py = self.e2p(olay.position())

        if self._surukleme is not None:
            tur, indeks, (bx, by), (ix0, iy0, ix1, iy1) = self._surukleme
            dx, dy = px - bx, py - by
            r = self.tasinan
            if r is None:
                return
            if tur == "tasi":
                if isinstance(r, MetinBloku):
                    simdi = r.sinirlar()
                    r.tasi((ix0 + dx) - simdi[0], (iy0 + dy) - simdi[1])
                    self.metni_tazele()
                else:
                    r.x0, r.y0, r.x1, r.y1 = ix0 + dx, iy0 + dy, ix1 + dx, iy1 + dy
            else:
                nx0, ny0, nx1, ny1 = ix0, iy0, ix1, iy1
                if indeks in (0, 2):
                    nx0 = min(ix0 + dx, ix1 - 8)
                else:
                    nx1 = max(ix1 + dx, ix0 + 8)
                if indeks in (0, 1):
                    ny0 = min(iy0 + dy, iy1 - 8)
                else:
                    ny1 = max(iy1 + dy, iy0 + 8)
                if olay.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    oran = (ix1 - ix0) / max(1.0, (iy1 - iy0))
                    ny1 = ny0 + (nx1 - nx0) / oran
                r.x0, r.y0, r.x1, r.y1 = nx0, ny0, nx1, ny1
            self.update()
            return

        if self._metin_secimi and self.aktif_blok is not None:
            self.imlec = self.aktif_blok.nokta_indeksi(px, py)
            self.update()
            return

        if self.mod == "tasi":
            yeni_vurgu = self.sayfa.nesne_bul(px, py) if self.sayfa else None
            if yeni_vurgu is not self._vurgu:
                self._vurgu = yeni_vurgu
                self.update()
            self.setCursor(Qt.CursorShape.OpenHandCursor if yeni_vurgu is not None
                           else Qt.CursorShape.ArrowCursor)
            return
        self._vurgu = None
        if self.sayfa and self.sayfa.resim_bul(px, py) is not None:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.IBeamCursor)

    def mouseReleaseEvent(self, olay) -> None:
        if self._surukleme is not None:
            self._surukleme = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            if self.sayfa and self.belge:
                self.sayfa.kaymalari_hesapla(self.belge.itme_acik)
            self.metni_tazele()
            self.durum_degisti.emit()
            self.belge_degisti.emit()
        self._metin_secimi = False

    def mouseDoubleClickEvent(self, olay) -> None:

        blok = self.aktif_blok
        if blok is None or not blok.metin:
            return
        i = min(self.imlec, len(blok.metin) - 1)
        bas = i
        while bas > 0 and blok.metin[bas - 1].isalnum():
            bas -= 1
        son = i
        while son < len(blok.metin) and blok.metin[son].isalnum():
            son += 1
        self.capa, self.imlec = bas, son
        self.update()
        self.durum_degisti.emit()

    def wheelEvent(self, olay) -> None:
        if olay.modifiers() & Qt.KeyboardModifier.ControlModifier:
            adim = 1.1 if olay.angleDelta().y() > 0 else 1 / 1.1
            self.zoom_ayarla(self.zoom * adim)
            olay.accept()
        else:
            olay.ignore()

    def keyPressEvent(self, olay) -> None:
        if not self.belge:
            return
        tus = olay.key()
        mod = olay.modifiers()
        ctrl = bool(mod & Qt.KeyboardModifier.ControlModifier)
        shift = bool(mod & Qt.KeyboardModifier.ShiftModifier)

        if tus == Qt.Key.Key_Escape:
            self.mod_ayarla("metin")
            return

        if self.tasinan is not None and self.aktif_blok is None:
            if tus in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self.belge.isaretle()
                if isinstance(self.tasinan, MetinBloku):
                    self.tasinan.sil(0, len(self.tasinan.metin))
                else:
                    self.sayfa.resimler.remove(self.tasinan)
                self.tasinan = None
                self.metni_tazele()
                self.durum_degisti.emit()
                self.belge_degisti.emit()
                return
            adim = 1.0 if shift else 5.0
            yon = {Qt.Key.Key_Left: (-adim, 0), Qt.Key.Key_Right: (adim, 0),
                   Qt.Key.Key_Up: (0, -adim), Qt.Key.Key_Down: (0, adim)}.get(tus)
            if yon:
                self.belge.isaretle()
                self.tasinan.tasi(*yon)
                if isinstance(self.tasinan, MetinBloku):
                    self.metni_tazele()
                else:
                    self.update()
                self.durum_degisti.emit()
                self.belge_degisti.emit()
                return

        blok = self.aktif_blok
        if blok is None:
            return

        if ctrl and tus == Qt.Key.Key_A:
            self.capa, self.imlec = 0, len(blok.metin)
            self.update()
            return
        if ctrl and tus in (Qt.Key.Key_C, Qt.Key.Key_X):
            bas, son = sorted((self.capa, self.imlec))
            if bas != son:
                QGuiApplication.clipboard().setText(blok.metin[bas:son])
                if tus == Qt.Key.Key_X:
                    self._duzenleme_basla()
                    blok.sil(bas, son)
                    self.imlec = self.capa = bas
                    self._degisti()
            return
        if ctrl and tus == Qt.Key.Key_V:
            metin = QGuiApplication.clipboard().text()
            if metin:
                self._yaz(metin.replace("\r\n", "\n").replace("\r", "\n"))
            return

        yon_tuslari = (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
                       Qt.Key.Key_Home, Qt.Key.Key_End)
        if tus in yon_tuslari:
            self._gezin(tus, shift, ctrl)
            return

        if tus in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            bas, son = sorted((self.capa, self.imlec))
            self._duzenleme_basla()
            if bas != son:
                blok.sil(bas, son)
                self.imlec = self.capa = bas
            elif tus == Qt.Key.Key_Backspace and self.imlec > 0:
                blok.sil(self.imlec - 1, self.imlec)
                self.imlec = self.capa = self.imlec - 1
            elif tus == Qt.Key.Key_Delete and self.imlec < len(blok.metin):
                blok.sil(self.imlec, self.imlec + 1)
            self._degisti()
            return

        if tus in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._yaz("\n")
            return

        if olay.text() and olay.text().isprintable():
            self._yaz(olay.text())
            return

        super().keyPressEvent(olay)

    def _gezin(self, tus, shift: bool, ctrl: bool) -> None:
        blok = self.aktif_blok
        assert blok is not None
        d = blok.duzen()
        k = blok.satir_no(self.imlec)
        satir = d[k]

        if tus == Qt.Key.Key_Left:
            self.imlec = max(0, self.imlec - 1)
            self._tercih_x = None
        elif tus == Qt.Key.Key_Right:
            self.imlec = min(len(blok.metin), self.imlec + 1)
            self._tercih_x = None
        elif tus == Qt.Key.Key_Home:
            self.imlec = satir.bas
            self._tercih_x = None
        elif tus == Qt.Key.Key_End:
            self.imlec = satir.son
            self._tercih_x = None
        else:
            if self._tercih_x is None:
                self._tercih_x = blok.indeks_noktasi(self.imlec)[0]
            hedef_k = k - 1 if tus == Qt.Key.Key_Up else k + 1
            if 0 <= hedef_k < len(d):
                h = d[hedef_k]
                en_iyi, en_yakin = h.bas, float("inf")
                for i, xi in enumerate(h.xler):
                    fark = abs(xi - self._tercih_x)
                    if fark < en_yakin:
                        en_yakin, en_iyi = fark, h.bas + i
                self.imlec = min(en_iyi, len(blok.metin))

        if not shift:
            self.capa = self.imlec
        self.zorlanan_stil = None
        self._yazim_acik = False
        self._imlec_gorunur = True
        self.update()
        self.durum_degisti.emit()

    def _duzenleme_basla(self) -> None:
        assert self.belge is not None
        self.belge.isaretle()
        self._yazim_acik = False

    def _yaz(self, metin: str) -> None:
        blok = self.aktif_blok
        if blok is None or not self.belge:
            return
        bas, son = sorted((self.capa, self.imlec))

        if not self._yazim_acik or bas != son:
            self.belge.isaretle()
            self._yazim_acik = True

        if bas != son:
            blok.sil(bas, son)
            self.imlec = bas

        stil = self.zorlanan_stil or blok.stil_at(self.imlec)
        self.imlec = blok.ekle(self.imlec, metin, stil)
        self.capa = self.imlec
        self._tercih_x = None
        self._degisti()

    def _degisti(self) -> None:
        if self.sayfa and self.belge:
            self.sayfa.kaymalari_hesapla(self.belge.itme_acik)
        self._imlec_gorunur = True
        self.metni_tazele()
        self.durum_degisti.emit()
        self.belge_degisti.emit()

    def stil_uygula(self, **degisiklik) -> None:

        blok = self.aktif_blok
        if blok is None:
            return
        bas, son = sorted((self.capa, self.imlec))
        if bas != son:
            self.belge.isaretle()
            blok.stil_uygula(bas, son, **degisiklik)
            self._degisti()
        else:
            from dataclasses import replace
            temel = self.zorlanan_stil or blok.stil_at(self.imlec)
            self.zorlanan_stil = replace(temel, **degisiklik)
            self.durum_degisti.emit()

    def gecerli_stil(self) -> Stil | None:
        blok = self.aktif_blok
        if blok is None:
            return None
        if self.zorlanan_stil is not None:
            return self.zorlanan_stil
        bas, son = sorted((self.capa, self.imlec))
        return blok.stiller[bas] if bas != son and blok.stiller else blok.stil_at(self.imlec)

    def resim_ekle(self, yol: str) -> None:
        if not self.belge or not self.sayfa:
            return
        pix = self._resim_pix(yol)
        if pix.isNull():
            return
        sayfa = self.sayfa
        en_fazla = sayfa.genislik * 0.4
        olcek = min(1.0, en_fazla / max(1, pix.width()))
        g, y = pix.width() * olcek, pix.height() * olcek
        x0 = (sayfa.genislik - g) / 2
        y0 = (sayfa.yukseklik - y) / 2
        self.belge.isaretle()
        resim = ResimNesnesi(yol, x0, y0, x0 + g, y0 + y)
        sayfa.resimler.append(resim)
        self.secili_resim = resim
        self.aktif_blok = None
        self.update()
        self.durum_degisti.emit()
        self.belge_degisti.emit()

    def geri_al(self) -> None:
        if self.belge and self.belge.geri_al():
            self.aktif_blok = None
            self.tasinan = None
            self.metni_tazele()
            self.durum_degisti.emit()

    def yinele(self) -> None:
        if self.belge and self.belge.yinele():
            self.aktif_blok = None
            self.tasinan = None
            self.metni_tazele()
            self.durum_degisti.emit()
