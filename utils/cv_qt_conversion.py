import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPixmap

def cv_to_qpixmap(cv_img: np.ndarray) -> QPixmap:
    """
    Converte uma imagem OpenCV (NumPy array BGR/Cinza) para um QPixmap do PyQt6.
    """
    if cv_img is None:
        return QPixmap()

    # Se a imagem for em escala de cinza (apenas 2 dimensões)
    if len(cv_img.shape) == 2:
        height, width = cv_img.shape
        bytes_per_line = width
        q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        return QPixmap.fromImage(q_img)

    # Se for colorida (BGR de 3 canais)
    height, width, channel = cv_img.shape
    bytes_per_line = 3 * width
    # Converte BGR para RGB para que o Qt exiba com as cores corretas
    rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    q_img = QImage(rgb_img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(q_img)