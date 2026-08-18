from __future__ import annotations

import os
import re
from pathlib import Path

import pymupdf as fitz

from .fonts import FontDeposu, pdf_fontu_esle
from .model import Belge, MetinBloku, Sayfa, Stil


def _yumusak_kirilim_mi(satir: dict, sonraki: dict, sag_sinir: float) -> bool:

    sonraki_spanlar = [s for s in sonraki.get("spans", []) if s.get("text", "").strip()]
    if not sonraki_spanlar:
        return False
    ilk = sonraki_spanlar[0]
    kelime = re.split(r"\s+", ilk["text"].strip(), maxsplit=1)[0]
    if not kelime:
        return False
    aile, kalin, egik = pdf_fontu_esle(ilk.get("font", ""), ilk.get("flags", 0))
    font = FontDeposu.al().mu(aile, kalin, egik)
    boy = float(ilk.get("size", 11.0))
    genislik = font.text_length(kelime, boy) + font.text_length(" ", boy)
    return satir["bbox"][2] + genislik > sag_sinir


def _blok_hizasi(satirlar: list[dict], x0: float, x1: float) -> str:
    if len(satirlar) < 2:
        return "sol"
    orta = (x0 + x1) / 2.0
    ortali = all(abs(((s["bbox"][0] + s["bbox"][2]) / 2.0) - orta) < 2.0 for s in satirlar)
    if ortali:
        return "orta"
    sagli = (all(abs(s["bbox"][2] - x1) < 2.0 for s in satirlar)
             and not all(abs(s["bbox"][0] - x0) < 2.0 for s in satirlar))
    return "sag" if sagli else "sol"


def _sag_sinir(bbox, digerleri, sayfa_sag: float) -> float:

    x0, y0, x1, y1 = bbox
    engel = sayfa_sag
    for d in digerleri:
        dx0, dy0, dx1, dy1 = d
        if dx0 <= x1 + 1:
            continue
        if dy1 <= y0 + 1 or dy0 >= y1 - 1:
            continue
        engel = min(engel, dx0 - 4.0)
    return max(x1, engel)


def yukle(yol: str) -> Belge:
    kaynak = fitz.open(yol)
    try:
        return _yukle_icinden(kaynak, yol)
    finally:
        kaynak.close()


def _yukle_icinden(kaynak: fitz.Document, yol: str) -> Belge:
    belge = Belge(yol)
    depo = FontDeposu.al()

    for sayfa_no in range(kaynak.page_count):
        pdf_sayfa = kaynak[sayfa_no]
        kutu = pdf_sayfa.rect
        sayfa = Sayfa(sayfa_no, kutu.width, kutu.height)

        sozluk = pdf_sayfa.get_text("dict")
        metin_bloklari = [b for b in sozluk["blocks"] if b.get("type") == 0 and b.get("lines")]
        tum_kutular = [b["bbox"] for b in metin_bloklari]

        sayfa_sag = max((b[2] for b in tum_kutular), default=kutu.width) + 1.0

        for ham in metin_bloklari:
            bx0, by0, bx1, by1 = ham["bbox"]
            digerleri = [k for k in tum_kutular if k is not ham["bbox"]]

            sag_sinir = _sag_sinir(ham["bbox"], digerleri, sayfa_sag)

            metin_parcalari: list[str] = []
            stiller: list[Stil] = []
            kutular: list[tuple[float, float, float, float]] = []
            tabanlar: list[float] = []
            boylar: list[float] = []

            satirlar = ham["lines"]
            for si, satir in enumerate(satirlar):
                span_listesi = [s for s in satir["spans"] if s.get("text")]
                if not span_listesi:
                    continue
                tabanlar.append(span_listesi[0]["origin"][1])
                for span in span_listesi:
                    aile, kalin, egik = pdf_fontu_esle(span.get("font", ""), span.get("flags", 0))
                    stil = Stil(
                        aile=aile,
                        boy=round(float(span.get("size", 11.0)), 2),
                        kalin=kalin,
                        egik=egik,
                        renk=int(span.get("color", 0)) & 0xFFFFFF,
                    )
                    yazi = span["text"]
                    metin_parcalari.append(yazi)
                    stiller.extend([stil] * len(yazi))
                    kutular.append(tuple(span["bbox"]))
                    boylar.append(stil.boy)

                if si < len(satirlar) - 1:
                    yumusak = _yumusak_kirilim_mi(satir, satirlar[si + 1], sag_sinir)
                    ayirici = " " if yumusak else "\n"
                    son_stil = stiller[-1] if stiller else Stil()
                    metin_parcalari.append(ayirici)
                    stiller.append(son_stil)
                    kutular.append(tuple(satir["bbox"]))

            metin = "".join(metin_parcalari)
            if not metin.strip():
                continue

            carpani = 1.16
            if len(tabanlar) >= 2:
                araliklar = [b - a for a, b in zip(tabanlar, tabanlar[1:]) if b - a > 0.5]
                if araliklar:
                    ort_aralik = sum(araliklar) / len(araliklar)
                    ort_boy = sum(boylar) / len(boylar)
                    f = depo.mu(stiller[0].aile, stiller[0].kalin, stiller[0].egik)
                    birim = (f.ascender - f.descender) * ort_boy
                    if birim > 0:
                        carpani = max(0.9, min(2.5, ort_aralik / birim))

            blok = MetinBloku(
                x0=bx0, y0=by0, x1=bx1 + 1.0, y1=by1,
                metin=metin, stiller=stiller,
                satir_carpani=carpani,
                hiza=_blok_hizasi(satirlar, ham["bbox"][0], ham["bbox"][2]),
            )
            blok.ilk_kutular = kutular
            blok.kalibre_et(
                hedef_satir=len(tabanlar),
                ilk_taban=tabanlar[0] if tabanlar else by0,
                sag_sinir=sag_sinir,
            )
            sayfa.bloklar.append(blok)

        sayfa.kaymalari_hesapla(belge.itme_acik)
        belge.sayfalar.append(sayfa)

    return belge


def arkaplan_belgesi(yol: str) -> fitz.Document:

    doc = fitz.open(yol)
    for sayfa in doc:
        bulundu = False
        for blok in sayfa.get_text("dict")["blocks"]:
            if blok.get("type") != 0:
                continue
            for satir in blok.get("lines", []):
                for span in satir.get("spans", []):
                    if span.get("text", "").strip():
                        sayfa.add_redact_annot(fitz.Rect(span["bbox"]))
                        bulundu = True
        if bulundu:
            sayfa.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                text=fitz.PDF_REDACT_TEXT_REMOVE,
            )
    return doc


_CMAP_BAS = """/CIDInit /ProcSet findresource begin
12 dict begin
begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /Adobe-Identity-UCS def
/CMapType 2 def
1 begincodespacerange
<0000> <FFFF>
endcodespacerange
"""
_CMAP_SON = """endcmap
CMapName currentdict /CMap defineresource pop
end
end"""


def _cmap_uret(gid_harf: dict[int, str]) -> bytes:

    girdiler = [
        (f"<{gid:04X}>", "<" + ch.encode("utf-16-be").hex().upper() + ">")
        for gid, ch in sorted(gid_harf.items())
    ]
    parcalar = [_CMAP_BAS]
    for i in range(0, len(girdiler), 100):
        obek = girdiler[i:i + 100]
        parcalar.append(f"{len(obek)} beginbfchar\n")
        parcalar.extend(f"{g} {u}\n" for g, u in obek)
        parcalar.append("endbfchar\n")
    parcalar.append(_CMAP_SON)
    return "".join(parcalar).encode("latin-1", "replace")


def _tounicode_duzelt(doc, kullanim: dict[str, tuple[fitz.Font, set[str]]]) -> None:

    islenen: set[int] = set()
    for sayfa in doc:
        for bilgi in sayfa.get_fonts(full=True):
            xref, basefont = bilgi[0], bilgi[3]
            if xref in islenen:
                continue
            temiz = basefont.split("+")[-1]
            kayit = kullanim.get(temiz)
            if kayit is None:
                continue
            font, harfler = kayit
            gid_harf: dict[int, str] = {}
            for ch in harfler:
                gid = font.has_glyph(ord(ch))
                if gid:
                    gid_harf[gid] = ch
            if not gid_harf:
                continue
            tur, deger = doc.xref_get_key(xref, "ToUnicode")
            if tur != "xref":
                continue
            try:
                tu_xref = int(deger.split()[0])
                doc.update_stream(tu_xref, _cmap_uret(gid_harf), new=True)
                islenen.add(xref)
            except Exception:  # noqa: BLE001
                continue


def kaydet(belge: Belge, hedef: str) -> None:
    gecici = str(Path(hedef).with_suffix(Path(hedef).suffix + ".tmp"))
    doc = fitz.open(belge.yol)
    try:
        _kaydet_icine(belge, doc, gecici)
        os.replace(gecici, hedef)
    finally:
        doc.close()
        if os.path.exists(gecici):
            os.remove(gecici)


def _kaydet_icine(belge: Belge, doc: fitz.Document, hedef: str) -> None:
    depo = FontDeposu.al()
    kullanim: dict[str, tuple[fitz.Font, set[str]]] = {}

    for sayfa in belge.sayfalar:
        pdf_sayfa = doc[sayfa.numara]
        yazilacak = [b for b in sayfa.bloklar if b.kirli or abs(b.dy) > 0.01]

        if yazilacak:
            for blok in yazilacak:
                for kutu in blok.ilk_kutular:
                    r = fitz.Rect(kutu)
                    if not r.is_empty:
                        pdf_sayfa.add_redact_annot(r)
            pdf_sayfa.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                text=fitz.PDF_REDACT_TEXT_REMOVE,
            )

        yazicilar: dict[int, fitz.TextWriter] = {}
        for blok in yazilacak:
            for satir in blok.duzen():
                if satir.son <= satir.bas:
                    continue
                taban = blok.y0 + blok.dy + satir.taban
                i = satir.bas
                while i < satir.son:
                    stil = blok.stiller[i]
                    j = i
                    while j < satir.son and blok.stiller[j] == stil:
                        j += 1
                    parca = blok.metin[i:j]
                    if parca.strip():
                        x = satir.xler[i - satir.bas]
                        mu = depo.mu(stil.aile, stil.kalin, stil.egik)
                        yazici = yazicilar.setdefault(stil.renk, fitz.TextWriter(pdf_sayfa.rect))
                        yazici.append(fitz.Point(x, taban), parca, font=mu, fontsize=stil.boy)
                        kayit = kullanim.setdefault(mu.name, (mu, set()))
                        kayit[1].update(parca)
                    i = j

        for renk, yazici in yazicilar.items():
            renk_rgb = (((renk >> 16) & 0xFF) / 255.0,
                        ((renk >> 8) & 0xFF) / 255.0,
                        (renk & 0xFF) / 255.0)
            yazici.write_text(pdf_sayfa, color=renk_rgb)

        for resim in sayfa.resimler:
            x0, y0, x1, y1 = resim.sinirlar()
            if x1 - x0 < 1 or y1 - y0 < 1:
                continue
            pdf_sayfa.insert_image(fitz.Rect(x0, y0, x1, y1),
                                   filename=resim.yol, keep_proportion=False)

    if kullanim:
        _tounicode_duzelt(doc, kullanim)

    try:
        doc.subset_fonts(verbose=False)
    except Exception:  # noqa: BLE001 - alt kumeleme basarisiz olsa da kaydet
        pass

    doc.save(hedef, garbage=4, deflate=True)
