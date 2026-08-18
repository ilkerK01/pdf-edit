from __future__ import annotations

from dataclasses import dataclass, field, replace

from .fonts import FontDeposu, VARSAYILAN_AILE

BOSLUKLAR = " \t "


@dataclass(frozen=True)
class Stil:
    aile: str = VARSAYILAN_AILE
    boy: float = 11.0
    kalin: bool = False
    egik: bool = False
    renk: int = 0x000000

    def rgb(self) -> tuple[float, float, float]:
        return (
            ((self.renk >> 16) & 0xFF) / 255.0,
            ((self.renk >> 8) & 0xFF) / 255.0,
            (self.renk & 0xFF) / 255.0,
        )


VARSAYILAN_STIL = Stil()


@dataclass
class Satir:
    bas: int
    son: int
    sonraki: int
    ust: float
    taban: float
    yuk: float
    xler: list[float] = field(default_factory=list)


class MetinBloku:

    def __init__(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        metin: str,
        stiller: list[Stil],
        satir_carpani: float = 1.16,
        hiza: str = "sol",
    ) -> None:
        assert len(metin) == len(stiller), "metin ve stil dizileri esit olmali"
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.ilk_yukseklik = max(1.0, y1 - y0)
        self.metin = metin
        self.stiller = stiller
        self.satir_carpani = satir_carpani
        self.hiza = hiza
        self.dy = 0.0
        self.kirli = False
        self.tasindi = False

        self.ilk_kutular: list[tuple[float, float, float, float]] = []
        self._duzen: list[Satir] | None = None
        self._adv: list[float] | None = None

    def _ilerlemeler(self) -> list[float]:
        if self._adv is None:
            depo = FontDeposu.al()
            self._adv = [
                0.0 if ch == "\n"
                else depo.mu(st.aile, st.kalin, st.egik).text_length(ch, st.boy)
                for ch, st in zip(self.metin, self.stiller)
            ]
        return self._adv

    def bozuldu(self) -> None:
        self._duzen = None
        self._adv = None

    @property
    def genislik(self) -> float:
        return max(4.0, self.x1 - self.x0)

    def stil_at(self, indeks: int) -> Stil:

        if not self.stiller:
            return VARSAYILAN_STIL
        i = min(max(indeks - 1, 0), len(self.stiller) - 1)

        if self.metin[i] == "\n" and indeks < len(self.stiller):
            return self.stiller[indeks]
        return self.stiller[i]

    def duzen(self) -> list[Satir]:
        if self._duzen is not None:
            return self._duzen

        depo = FontDeposu.al()
        metin, stiller = self.metin, self.stiller
        adv = self._ilerlemeler()
        n = len(metin)
        maks = self.genislik + 0.6
        satirlar: list[Satir] = []

        i = 0
        while True:
            j = i
            genislik = 0.0
            son_bosluk = -1
            gorunur_son = n
            sonraki = n
            while j < n:
                ch = metin[j]
                if ch == "\n":
                    gorunur_son, sonraki = j, j + 1
                    break
                genislik += adv[j]
                if genislik > maks and j > i:
                    if son_bosluk > i:
                        gorunur_son, sonraki = son_bosluk, son_bosluk + 1
                    else:
                        gorunur_son, sonraki = j, j
                    break
                if ch in BOSLUKLAR:
                    son_bosluk = j
                j += 1
            else:
                gorunur_son, sonraki = n, n

            satirlar.append(Satir(bas=i, son=gorunur_son, sonraki=sonraki, ust=0, taban=0, yuk=0))
            if sonraki >= n:
                if sonraki > gorunur_son:
                    satirlar.append(Satir(bas=n, son=n, sonraki=n, ust=0, taban=0, yuk=0))
                break
            i = sonraki

        y = 0.0
        for satir in satirlar:
            dilim = stiller[satir.bas:satir.son] or [self.stil_at(satir.bas)]
            asc = desc = 0.0
            for st in dilim:
                f = depo.mu(st.aile, st.kalin, st.egik)
                asc = max(asc, f.ascender * st.boy)
                desc = max(desc, -f.descender * st.boy)
            bosluk = (asc + desc) * (self.satir_carpani - 1.0)
            satir.yuk = asc + desc + bosluk
            satir.ust = y
            satir.taban = y + bosluk / 2.0 + asc
            y += satir.yuk

            gorunur = adv[satir.bas:satir.son]

            etkin = list(gorunur)
            k = satir.son - 1
            while k >= satir.bas and metin[k] in BOSLUKLAR:
                etkin[k - satir.bas] = 0.0
                k -= 1
            toplam = sum(etkin)

            if self.hiza == "orta":
                x = self.x0 + (self.genislik - toplam) / 2.0
            elif self.hiza == "sag":
                x = self.x1 - toplam
            else:
                x = self.x0
            satir.xler = [x]
            for w in gorunur:
                x += w
                satir.xler.append(x)

        self._duzen = satirlar
        return satirlar

    @property
    def yukseklik(self) -> float:
        d = self.duzen()
        return d[-1].ust + d[-1].yuk if d else self.ilk_yukseklik

    @property
    def buyume(self) -> float:
        return self.yukseklik - self.ilk_yukseklik

    def sinirlar(self) -> tuple[float, float, float, float]:

        return (self.x0, self.y0 + self.dy, self.x1, self.y0 + self.dy + self.yukseklik)

    def kalibre_et(self, hedef_satir: int, ilk_taban: float, sag_sinir: float) -> None:

        if hedef_satir <= 1:
            self.x1 = max(self.x1, sag_sinir)
            self.bozuldu()
        else:
            taban_x1 = self.x1
            genislik = taban_x1 - self.x0
            mevcut = len(self.duzen())
            if mevcut > hedef_satir:
                tavan = min(sag_sinir, taban_x1 + genislik * 0.12)
                adimlar = [taban_x1 + (tavan - taban_x1) * k / 10.0 for k in range(11)]
            elif mevcut < hedef_satir:
                adimlar = [taban_x1 - genislik * 0.15 * k / 10.0 for k in range(11)]
            else:
                adimlar = [taban_x1]
            for aday in adimlar:
                self.x1 = aday
                self.bozuldu()
                if len(self.duzen()) == hedef_satir:
                    break
            else:
                self.x1 = taban_x1
                self.bozuldu()

        d = self.duzen()
        if d:
            self.y0 += ilk_taban - (self.y0 + d[0].taban)
            self.bozuldu()
        self.ilk_yukseklik = max(1.0, self.yukseklik)

    def satir_no(self, indeks: int) -> int:
        d = self.duzen()
        for k, s in enumerate(d):
            if indeks < s.sonraki or k == len(d) - 1:
                return k
        return len(d) - 1

    def indeks_noktasi(self, indeks: int) -> tuple[float, float, float]:

        d = self.duzen()
        if not d:
            return self.x0, self.y0 + self.dy, 12.0
        k = self.satir_no(indeks)
        s = d[k]
        yerel = min(max(indeks - s.bas, 0), len(s.xler) - 1)
        return s.xler[yerel], self.y0 + self.dy + s.ust, s.yuk

    def nokta_indeksi(self, x: float, y: float) -> int:
        d = self.duzen()
        if not d:
            return 0
        yerel_y = y - (self.y0 + self.dy)
        hedef = d[-1]
        for s in d:
            if yerel_y < s.ust + s.yuk:
                hedef = s
                break
        en_iyi, en_yakin = hedef.bas, float("inf")
        for k, xk in enumerate(hedef.xler):
            fark = abs(xk - x)
            if fark < en_yakin:
                en_yakin, en_iyi = fark, hedef.bas + k
        return min(en_iyi, len(self.metin))

    def ekle(self, indeks: int, metin: str, stil: Stil) -> int:
        self.metin = self.metin[:indeks] + metin + self.metin[indeks:]
        self.stiller[indeks:indeks] = [stil] * len(metin)
        self.kirli = True
        self.bozuldu()
        return indeks + len(metin)

    def sil(self, bas: int, son: int) -> None:
        bas, son = max(0, min(bas, son)), min(len(self.metin), max(bas, son))
        if bas >= son:
            return
        self.metin = self.metin[:bas] + self.metin[son:]
        del self.stiller[bas:son]
        self.kirli = True
        self.bozuldu()

    def stil_uygula(self, bas: int, son: int, **degisiklik) -> None:
        bas, son = max(0, min(bas, son)), min(len(self.stiller), max(bas, son))
        for i in range(bas, son):
            self.stiller[i] = replace(self.stiller[i], **degisiklik)
        self.kirli = True
        self.bozuldu()

    def tasi(self, dx: float, dy: float) -> None:
        self.x0 += dx
        self.x1 += dx
        self.y0 += self.dy + dy
        self.dy = 0.0
        self.tasindi = True
        self.kirli = True
        self.bozuldu()

    def ayir(self, bas: int, son: int) -> "MetinBloku | None":
        bas, son = max(0, min(bas, son)), min(len(self.metin), max(bas, son))
        parca = self.metin[bas:son]
        if not parca.strip():
            return None

        x, ust, _ = self.indeks_noktasi(bas)
        stiller = list(self.stiller[bas:son])
        depo = FontDeposu.al()
        genislik = sum(
            0.0 if ch == "\n" else depo.mu(st.aile, st.kalin, st.egik).text_length(ch, st.boy)
            for ch, st in zip(parca, stiller)
        )

        yeni = MetinBloku(
            x0=x, y0=ust, x1=x + genislik + 2.0, y1=ust + 1.0,
            metin=parca, stiller=stiller,
            satir_carpani=self.satir_carpani, hiza="sol",
        )
        yeni.kirli = True
        yeni.tasindi = True
        yeni.ilk_yukseklik = max(1.0, yeni.yukseklik)
        self.sil(bas, son)
        return yeni


@dataclass
class ResimNesnesi:
    yol: str
    x0: float
    y0: float
    x1: float
    y1: float

    def tasi(self, dx: float, dy: float) -> None:
        self.x0 += dx
        self.x1 += dx
        self.y0 += dy
        self.y1 += dy

    def sinirlar(self) -> tuple[float, float, float, float]:
        return (min(self.x0, self.x1), min(self.y0, self.y1),
                max(self.x0, self.x1), max(self.y0, self.y1))


class Sayfa:
    def __init__(self, numara: int, genislik: float, yukseklik: float) -> None:
        self.numara = numara
        self.genislik = genislik
        self.yukseklik = yukseklik
        self.bloklar: list[MetinBloku] = []
        self.resimler: list[ResimNesnesi] = []

    def kaymalari_hesapla(self, itme_acik: bool) -> None:

        if not itme_acik:
            for b in self.bloklar:
                b.dy = 0.0
            return
        birikim = 0.0
        for b in sorted(self.bloklar, key=lambda b: (b.y0, b.x0)):
            if b.tasindi:
                b.dy = 0.0
                continue
            b.dy = birikim
            birikim += b.buyume

    def nesne_bul(self, x: float, y: float):
        resim = self.resim_bul(x, y)
        if resim is not None:
            return resim
        return self.blok_bul(x, y)

    def blok_bul(self, x: float, y: float) -> MetinBloku | None:
        adaylar = []
        for b in self.bloklar:
            bx0, by0, bx1, by1 = b.sinirlar()
            if bx0 - 2 <= x <= bx1 + 2 and by0 - 2 <= y <= by1 + 2:
                adaylar.append(b)
        if not adaylar:
            return None

        return min(adaylar, key=lambda b: (b.x1 - b.x0) * max(1.0, b.yukseklik))

    def en_yakin_blok(self, x: float, y: float) -> MetinBloku | None:
        if not self.bloklar:
            return None

        def uzaklik(b: MetinBloku) -> float:
            bx0, by0, bx1, by1 = b.sinirlar()
            dx = max(bx0 - x, 0, x - bx1)
            dy = max(by0 - y, 0, y - by1)
            return dx * dx + dy * dy

        return min(self.bloklar, key=uzaklik)

    def resim_bul(self, x: float, y: float) -> ResimNesnesi | None:
        for r in reversed(self.resimler):
            rx0, ry0, rx1, ry1 = r.sinirlar()
            if rx0 <= x <= rx1 and ry0 <= y <= ry1:
                return r
        return None


class Belge:
    def __init__(self, yol: str) -> None:
        self.yol = yol
        self.sayfalar: list[Sayfa] = []
        self.itme_acik = True
        self._yigin: list[tuple] = []
        self._ileri: list[tuple] = []

    def _goruntu(self) -> tuple:
        return tuple(
            (
                tuple((b.metin, tuple(b.stiller), b.kirli, b.x0, b.x1, b.y0, b.dy, b.tasindi)
                      for b in s.bloklar),
                tuple((r.yol, r.x0, r.y0, r.x1, r.y1) for r in s.resimler),
            )
            for s in self.sayfalar
        )

    def isaretle(self) -> None:

        g = self._goruntu()
        if self._yigin and self._yigin[-1] == g:
            return
        self._yigin.append(g)
        del self._yigin[:-200]
        self._ileri.clear()

    def _yukle(self, g: tuple) -> None:
        for sayfa, (blok_v, resim_v) in zip(self.sayfalar, g):
            for blok, kayit in zip(sayfa.bloklar, blok_v):
                (blok.metin, stiller, blok.kirli,
                 blok.x0, blok.x1, blok.y0, blok.dy, blok.tasindi) = kayit
                blok.stiller = list(stiller)
                blok.bozuldu()
            sayfa.resimler = [ResimNesnesi(*r) for r in resim_v]
            sayfa.kaymalari_hesapla(self.itme_acik)

    def geri_al(self) -> bool:
        if not self._yigin:
            return False
        self._ileri.append(self._goruntu())
        self._yukle(self._yigin.pop())
        return True

    def yinele(self) -> bool:
        if not self._ileri:
            return False
        self._yigin.append(self._goruntu())
        self._yukle(self._ileri.pop())
        return True
