"""Conversão de Mat (numpy.ndarray) para imagens do Qt."""

import cv2 as cv
import numpy as np
from PyQt6.QtGui import QImage, QPixmap


def mat_to_qimage(mat: np.ndarray) -> QImage:
    """Exibe o Mat como o cv.imshow faria: 1 canal em cinza, 3 canais lidos como BGR."""
    if mat.dtype != np.uint8:
        mat = cv.normalize(mat, None, 0, 255, cv.NORM_MINMAX).astype(np.uint8)
    if mat.ndim == 2:
        data, fmt = np.ascontiguousarray(mat), QImage.Format.Format_Grayscale8
    else:
        # O OpenCV guarda os canais em BGR; o Qt espera RGB
        data, fmt = np.ascontiguousarray(cv.cvtColor(mat[:, :, :3], cv.COLOR_BGR2RGB)), QImage.Format.Format_RGB888
    h, w = data.shape[:2]
    return QImage(data.data, w, h, data.strides[0], fmt).copy()


def mat_to_qpixmap(mat: np.ndarray, max_size: tuple[int, int] | None = None) -> QPixmap:
    """Converte para QPixmap; com ``max_size`` gera uma miniatura (reduzida com INTER_AREA)."""
    if max_size:
        h, w = mat.shape[:2]
        scale = min(max_size[0] / w, max_size[1] / h, 1.0)
        if scale < 1.0:
            mat = cv.resize(mat, (max(1, round(w * scale)), max(1, round(h * scale))),
                            interpolation=cv.INTER_AREA)
    return QPixmap.fromImage(mat_to_qimage(mat))
