from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QSizePolicy, QWidget

from . import tema
from .conversao_qt import mat_para_qpixmap


class Visualizador(QWidget):
    # mostra um Mat ajustado ao espaço e avisa qual pixel está embaixo do mouse
    mouse_sobre_pixel = pyqtSignal(int, int)  # (-1, -1) = fora da imagem

    MARGEM = 12

    def __init__(self, texto_vazio="", parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(240, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._texto_vazio = texto_vazio
        self._pixmap = None
        self._legenda = ""

    def mostrar(self, mat, legenda):
        self._pixmap = mat_para_qpixmap(mat)
        self._legenda = legenda
        self.update()

    def limpar(self):
        self._pixmap = None
        self._legenda = ""
        self.update()

    def _area_imagem(self):
        area = QRectF(self.rect()).adjusted(self.MARGEM, self.MARGEM, -self.MARGEM, -self.MARGEM)
        w, h = self._pixmap.width(), self._pixmap.height()
        escala = min(area.width() / w, area.height() / h)
        dw, dh = w * escala, h * escala
        return QRectF(area.x() + (area.width() - dw) / 2, area.y() + (area.height() - dh) / 2, dw, dh)

    def paintEvent(self, event):
        pintor = QPainter(self)
        pintor.fillRect(self.rect(), QColor(tema.FUNDO_IMAGEM))
        if self._pixmap is None:
            pintor.setPen(QColor(tema.APAGADO))
            pintor.drawText(self.rect().adjusted(24, 24, -24, -24),
                            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self._texto_vazio)
            return
        destino = self._area_imagem()
        # reduzindo suaviza; ampliando deixa o pixel "quadrado" pra dar pra ver
        suave = destino.width() < self._pixmap.width()
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, suave)
        pintor.drawPixmap(destino, self._pixmap, QRectF(self._pixmap.rect()))
        if self._legenda:
            self._desenhar_legenda(pintor)

    def _desenhar_legenda(self, pintor):
        metricas = pintor.fontMetrics()
        caixa = QRectF(QPointF(self.MARGEM + 6, self.MARGEM + 6),
                       QPointF(self.MARGEM + 18 + metricas.horizontalAdvance(self._legenda),
                               self.MARGEM + 12 + metricas.height()))
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QColor(0, 0, 0, 170))
        pintor.drawRoundedRect(caixa, 5, 5)
        pintor.setPen(QColor(tema.TEXTO))
        pintor.drawText(caixa, Qt.AlignmentFlag.AlignCenter, self._legenda)

    def mouseMoveEvent(self, event):
        if self._pixmap is None:
            return
        destino = self._area_imagem()
        pos = event.position()
        if not destino.contains(pos):
            self.mouse_sobre_pixel.emit(-1, -1)
            return
        # converte a posição na tela pra coordenada do pixel na imagem
        w, h = self._pixmap.width(), self._pixmap.height()
        x = min(int((pos.x() - destino.x()) * w / destino.width()), w - 1)
        y = min(int((pos.y() - destino.y()) * h / destino.height()), h - 1)
        self.mouse_sobre_pixel.emit(x, y)

    def leaveEvent(self, event):
        self.mouse_sobre_pixel.emit(-1, -1)
