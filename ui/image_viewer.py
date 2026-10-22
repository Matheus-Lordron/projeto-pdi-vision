"""Visualizador de um Mat: ajusta a imagem ao espaço e informa o pixel sob o mouse."""

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QSizePolicy, QWidget

from . import theme
from .qt_image import mat_to_qpixmap


class ImageViewer(QWidget):
    hovered = pyqtSignal(int, int)  # coordenadas (x, y) no Mat; (-1, -1) fora da imagem

    MARGIN = 12

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(240, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._placeholder = placeholder
        self._pixmap: QPixmap | None = None
        self._caption = ""

    def show_mat(self, mat: np.ndarray, caption: str):
        self._pixmap = mat_to_qpixmap(mat)
        self._caption = caption
        self.update()

    def clear(self):
        self._pixmap = None
        self._caption = ""
        self.update()

    def _image_rect(self) -> QRectF:
        area = QRectF(self.rect()).adjusted(self.MARGIN, self.MARGIN, -self.MARGIN, -self.MARGIN)
        w, h = self._pixmap.width(), self._pixmap.height()
        scale = min(area.width() / w, area.height() / h)
        dw, dh = w * scale, h * scale
        return QRectF(area.x() + (area.width() - dw) / 2, area.y() + (area.height() - dh) / 2, dw, dh)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(theme.VIEWER_BG))
        if self._pixmap is None:
            painter.setPen(QColor(theme.MUTED))
            painter.drawText(self.rect().adjusted(24, 24, -24, -24),
                             Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self._placeholder)
            return
        target = self._image_rect()
        # Reduzindo: suaviza. Ampliando: mantém os pixels "quadrados" para que fiquem visíveis.
        smooth = target.width() < self._pixmap.width()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, smooth)
        painter.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))
        if self._caption:
            self._draw_caption(painter)

    def _draw_caption(self, painter: QPainter):
        metrics = painter.fontMetrics()
        box = QRectF(QPointF(self.MARGIN + 6, self.MARGIN + 6),
                     QPointF(self.MARGIN + 18 + metrics.horizontalAdvance(self._caption),
                             self.MARGIN + 12 + metrics.height()))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 170))
        painter.drawRoundedRect(box, 5, 5)
        painter.setPen(QColor(theme.TEXT))
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, self._caption)

    def mouseMoveEvent(self, event):
        if self._pixmap is None:
            return
        target = self._image_rect()
        pos = event.position()
        if not target.contains(pos):
            self.hovered.emit(-1, -1)
            return
        w, h = self._pixmap.width(), self._pixmap.height()
        x = min(int((pos.x() - target.x()) * w / target.width()), w - 1)
        y = min(int((pos.y() - target.y()) * h / target.height()), h - 1)
        self.hovered.emit(x, y)

    def leaveEvent(self, event):
        self.hovered.emit(-1, -1)
