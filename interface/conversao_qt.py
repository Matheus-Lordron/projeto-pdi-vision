import cv2 as cv
import numpy as np
from PyQt6.QtGui import QImage, QPixmap


def mat_para_qimage(mat):
    # mostra igual o cv.imshow: 1 canal = cinza, 3 canais = lido como BGR
    if mat.dtype != np.uint8:
        mat = cv.normalize(mat, None, 0, 255, cv.NORM_MINMAX).astype(np.uint8)
    if mat.ndim == 2:
        dados, formato = np.ascontiguousarray(mat), QImage.Format.Format_Grayscale8
    else:
        # o OpenCV guarda BGR e o Qt espera RGB
        dados = np.ascontiguousarray(cv.cvtColor(mat[:, :, :3], cv.COLOR_BGR2RGB))
        formato = QImage.Format.Format_RGB888
    h, w = dados.shape[:2]
    return QImage(dados.data, w, h, dados.strides[0], formato).copy()


def mat_para_qpixmap(mat, tamanho_max=None):
    # com tamanho_max gera miniatura (reduz com INTER_AREA antes de converter)
    if tamanho_max:
        h, w = mat.shape[:2]
        escala = min(tamanho_max[0] / w, tamanho_max[1] / h, 1.0)
        if escala < 1.0:
            mat = cv.resize(mat, (max(1, round(w * escala)), max(1, round(h * escala))),
                            interpolation=cv.INTER_AREA)
    return QPixmap.fromImage(mat_para_qimage(mat))
