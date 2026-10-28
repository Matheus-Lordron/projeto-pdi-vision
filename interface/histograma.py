import cv2 as cv
import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from . import tema

# cor de cada canal na ordem do OpenCV (B, G, R)
_CORES_BGR = ("#4c8dff", "#4cc38a", "#ff6b6b")


class Histograma(QWidget):
    # desenha o histograma de um Mat (calcHist com 256 níveis).
    # 1 canal = área cinza; 3 canais = uma curva por canal

    def __init__(self, titulo="", parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._titulo = titulo
        self._curvas = []  # lista de (contagens normalizadas 0..1, cor)

    def mostrar(self, mat, titulo=None):
        if titulo is not None:
            self._titulo = titulo
        canais = [mat] if mat.ndim == 2 else cv.split(mat)
        cores = ["#c8ccd4"] if mat.ndim == 2 else _CORES_BGR
        hists = [cv.calcHist([c], [0], None, [256], [0, 256]).ravel() for c in canais]
        maior = max(float(h.max()) for h in hists) or 1.0
        # normalizo todos pelo mesmo máximo pra dar pra comparar os canais
        self._curvas = [(h / maior, cor) for h, cor in zip(hists, cores)]
        self.update()

    def paintEvent(self, event):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.fillRect(self.rect(), QColor(tema.FUNDO_IMAGEM))
        pintor.setPen(QColor(tema.APAGADO))
        pintor.drawText(QRectF(8, 4, self.width() - 16, 18), Qt.AlignmentFlag.AlignLeft, self._titulo)
        pintor.drawText(QRectF(8, self.height() - 18, self.width() - 16, 16), Qt.AlignmentFlag.AlignLeft, "0")
        pintor.drawText(QRectF(8, self.height() - 18, self.width() - 16, 16), Qt.AlignmentFlag.AlignRight, "255")

        area = QRectF(8, 24, self.width() - 16, self.height() - 46)
        pintor.setPen(QPen(QColor(tema.BORDA), 1))
        pintor.drawLine(area.bottomLeft(), area.bottomRight())

        um_canal = len(self._curvas) == 1
        for valores, cor in self._curvas:
            caminho = QPainterPath(QPointF(area.left(), area.bottom()))
            for nivel, v in enumerate(valores):
                x = area.left() + nivel * area.width() / 255
                caminho.lineTo(QPointF(x, area.bottom() - float(v) * area.height()))
            caminho.lineTo(QPointF(area.right(), area.bottom()))
            cor_qt = QColor(cor)
            if um_canal:
                # cinza: preenche a área, fica parecido com o do ImageJ
                preenchimento = QColor(cor_qt)
                preenchimento.setAlpha(150)
                pintor.fillPath(caminho, preenchimento)
            pintor.setPen(QPen(cor_qt, 1.2))
            pintor.drawPath(caminho)


def resumo_histograma(mat):
    # faixa de valores usada pela imagem (mostra se o contraste "abriu")
    return f"mín {int(np.min(mat))} · máx {int(np.max(mat))}"
