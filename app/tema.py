from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QApplication


class Tema:
    koyu = {
        "bg-app": "#0f1115",
        "bg-panel": "#161920",
        "bg-canvas": "#1c1f27",
        "border": "#262a35",
        "text": "#e6e8ee",
        "text-muted": "#8b91a1",
        "accent": "#6d8bff",
        "accent-soft": "rgba(109,139,255,0.16)",
        "danger": "#ff6b6b",
        "shadow": "rgba(0,0,0,0.35)",
        "accent_soft": "rgba(109,139,255,0.16)",
        "imlec": "#6d8bff",
        "tutamac_kenar": "#6d8bff",
        "blok_cerceve": "rgba(109,139,255,0.35)",
    }
    acik = {
        "bg-app": "#f4f5f7",
        "bg-panel": "#ffffff",
        "bg-canvas": "#e6e8ec",
        "border": "#dfe2e8",
        "text": "#1a1d24",
        "text-muted": "#6b7280",
        "accent": "#3b5bdb",
        "accent-soft": "rgba(59,91,219,0.12)",
        "danger": "#e03131",
        "shadow": "rgba(0,0,0,0.12)",
        "accent_soft": "rgba(59,91,219,0.12)",
        "imlec": "#3b5bdb",
        "tutamac_kenar": "#3b5bdb",
        "blok_cerceve": "rgba(59,91,219,0.35)",
    }


_SVG = {
    "ac": '<path d="M4 5h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z"/><path d="M16 8h4a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-4"/>',
    "kaydet": '<path d="M4 3h13l3 3v15H4Z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/>',
    "geri": '<path d="M9 7 4 12l5 5"/><path d="M4 12h10a6 6 0 0 1 6 6v1"/>',
    "ileri": '<path d="m15 7 5 5-5 5"/><path d="M20 12H10a6 6 0 0 0-6 6v1"/>',
    "kalin": '<path d="M7 4h6a4 4 0 0 1 0 8H7Zm0 8h7a4 4 0 0 1 0 8H7Z"/>',
    "egik": '<path d="m10 4-4 16M14 4h6M4 20h6"/>',
    "renk": '<path d="M12 3a9 9 0 1 0 0 18h1.5a2 2 0 0 0 0-4H12a2 2 0 0 1 0-4h4a5 5 0 0 0 0-10Z"/><path d="M7 9h.01M9 6h.01M15 7h.01M17 10h.01"/>',
    "resim": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9" r="1.5"/><path d="m3 16 5-5 4 4 3-3 6 6"/>',
    "onceki": '<path d="m14 6-6 6 6 6"/><path d="M8 12h12"/>',
    "sonraki": '<path d="m10 6 6 6-6 6"/><path d="M4 12h12"/>',
    "kucult": '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
    "buyut": '<circle cx="12" cy="12" r="9"/><path d="M8 12h8M12 8v8"/>',
    "tema": '<path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/><circle cx="12" cy="12" r="4"/>',
    "farkli-kaydet": '<path d="M4 3h13l3 3v15H4Z"/><path d="M8 3v6h8V3M8 21v-7h8v7M19 12h4M21 10l2 2-2 2"/>',
}


def qss(ad: str) -> str:
    t = Tema.acik if ad == "acik" else Tema.koyu
    return f"""
QMainWindow {  background: {t['bg-app']}; }
QWidget {  color: {t['text']}; font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif; font-size: 13px; }
QToolBar {  background: {t['bg-panel']}; border: 0; border-bottom: 1px solid {t['border']}; spacing: 2px; padding: 4px 8px; }
QToolBar::separator {  background: {t['border']}; width: 1px; margin: 6px 8px; }
QToolBar#baslik_cubugu {  padding: 6px 12px; }
QToolBar#baslik_cubugu QLabel {  background: transparent; }
QToolBar QLabel {  background: transparent; color: {t['text-muted']}; padding: 0 2px; }
QLabel#uygulama_adi {  color: {t['text']}; font-size: 14px; font-weight: 600; padding-right: 8px; }
QLabel#dosya_adi {  color: {t['text-muted']}; }
QToolButton {  background: transparent; border: 0; border-radius: 6px; color: {t['text']}; min-height: 28px; min-width: 28px; padding: 0 6px; }
QToolButton:hover {  background: {t['accent-soft']}; }
QToolButton:pressed {  background: {t['accent']}; color: #ffffff; }
QToolButton:checked {  background: {t['accent-soft']}; border: 1px solid {t['accent']}; }
QToolButton:disabled {  color: {t['text-muted']}; }
QComboBox, QDoubleSpinBox {  background: {t['bg-app']}; border: 1px solid {t['border']}; border-radius: 6px; color: {t['text']}; min-height: 26px; padding: 0 8px; selection-background-color: {t['accent']}; }
QComboBox:hover, QDoubleSpinBox:hover {  border-color: {t['text-muted']}; }
QComboBox:focus, QDoubleSpinBox:focus {  border: 1px solid {t['accent']}; }
QComboBox::drop-down {  border: 0; width: 20px; }
QComboBox::down-arrow {  width: 8px; height: 8px; }
QComboBox QAbstractItemView {  background: {t['bg-panel']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 4px; outline: 0; selection-background-color: {t['accent-soft']}; selection-color: {t['text']}; }
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {  width: 14px; border: 0; background: transparent; }
QScrollArea {  background: {t['bg-canvas']}; border: 0; }
QScrollArea > QWidget > QWidget {  background: {t['bg-canvas']}; }
QScrollBar:vertical {  background: transparent; width: 10px; margin: 2px; }
QScrollBar:horizontal {  background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle {  background: {t['text-muted']}; border-radius: 3px; min-height: 28px; min-width: 28px; }
QScrollBar::handle:hover {  background: {t['accent']}; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {  background: transparent; border: 0; height: 0; width: 0; }
QStatusBar {  background: {t['bg-panel']}; border-top: 1px solid {t['border']}; color: {t['text-muted']}; min-height: 24px; font-size: 12px; }
QStatusBar QLabel {  background: transparent; color: {t['text-muted']}; padding: 0 6px; }
QStatusBar::item {  border: 0; }
QStatusBar QToolBar {  background: transparent; border: 0; padding: 0 4px; }
QStatusBar QToolButton {  min-height: 22px; min-width: 22px; padding: 0 3px; }
QMenu {  background: {t['bg-panel']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 4px; }
QMenu::item {  padding: 5px 14px; border-radius: 4px; }
QMenu::item:selected {  background: {t['accent-soft']}; }
QCheckBox {  color: {t['text-muted']}; spacing: 6px; background: transparent; }
QCheckBox::indicator {  width: 14px; height: 14px; border: 1px solid {t['border']}; border-radius: 4px; background: {t['bg-app']}; }
QCheckBox::indicator:checked {  background: {t['accent']}; border-color: {t['accent']}; }
QToolTip {  background: {t['bg-panel']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 4px 8px; }
QMessageBox, QFileDialog, QColorDialog {  background: {t['bg-panel']}; }
QPushButton {  background: {t['bg-app']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 5px 14px; min-height: 24px; }
QPushButton:hover {  border-color: {t['accent']}; }
QPushButton:default {  background: {t['accent']}; color: #ffffff; border-color: {t['accent']}; }
"""


def simge(ad: str, renk: str) -> QIcon:
    yol = _SVG.get(ad, _SVG["tema"])
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="{renk}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">{yol}</svg>'
    return QIcon(QPixmap.fromImage(QImage.fromData(svg.encode("utf-8"))))


def tema_uygula(app: QApplication, ad: str) -> None:
    secim = ad if ad in ("koyu", "acik") else "koyu"
    app.setStyleSheet(qss(secim))
    QSettings("ilker", "PdfEdit").setValue("tema", secim)
