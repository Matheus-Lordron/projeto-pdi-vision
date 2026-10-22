"""Leitura e gravação de imagens aceitando caminhos com acentos no Windows.

``cv.imread``/``cv.imwrite`` falham com caminhos não-ASCII no Windows; por isso
os bytes são lidos/gravados pelo NumPy e decodificados com imdecode/imencode.
"""

import os

import cv2 as cv
import numpy as np

IMAGE_FILTER = "Imagens (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")


def imread(path: str, flags: int = cv.IMREAD_COLOR) -> np.ndarray | None:
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    return cv.imdecode(data, flags)


def imwrite(path: str, mat: np.ndarray) -> bool:
    ext = os.path.splitext(path)[1] or ".png"
    ok, buffer = cv.imencode(ext, mat)
    if not ok:
        return False
    try:
        buffer.tofile(path)
    except OSError:  # pasta inexistente, sem permissão, caminho longo demais...
        return False
    return True
