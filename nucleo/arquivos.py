import os

import cv2 as cv
import numpy as np

FILTRO_IMAGENS = "Imagens (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)"
EXTENSOES = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")

# cv.imread/imwrite não funcionam com acento no caminho no Windows,
# por isso leio os bytes com numpy e uso imdecode/imencode.


def ler_imagem(caminho, flags=cv.IMREAD_COLOR):
    try:
        dados = np.fromfile(caminho, dtype=np.uint8)
    except OSError:
        return None
    return cv.imdecode(dados, flags)


def salvar_imagem(caminho, mat):
    extensao = os.path.splitext(caminho)[1] or ".png"
    ok, buffer = cv.imencode(extensao, mat)
    if not ok:
        return False
    try:
        buffer.tofile(caminho)
    except OSError:
        return False
    return True
