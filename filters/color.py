import cv2
import numpy as np
from core.filter_base import FilterBase

class GrayscaleFilter(FilterBase):
    def __init__(self):
        super().__init__("Tons de Cinza")
        self.params = {'metodo': 'OpenCV (Padrão)'}

    def get_ui_schema(self) -> dict:
        return {
            'metodo': {
                'type': 'combobox',
                'options': ['OpenCV (Padrão)', 'Média Simples (R+G+B)/3'],
                'default': 'OpenCV (Padrão)'
            }
        }

    def apply(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 2 or image.shape[2] == 1:
            return image

        metodo = self.params.get('metodo', 'OpenCV (Padrão)')
        
        if metodo == 'Média Simples (R+G+B)/3':
            gray = np.mean(image, axis=2).astype(np.uint8)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


class ChannelExtractionFilter(FilterBase):
    def __init__(self):
        super().__init__("Extração de Canal RGB")
        self.params = {'canal': 'Red (Vermelho)'}

    def get_ui_schema(self) -> dict:
        return {
            'canal': {
                'type': 'combobox',
                'options': ['Red (Vermelho)', 'Green (Verde)', 'Blue (Azul)'],
                'default': 'Red (Vermelho)'
            }
        }

    def apply(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 2 or image.shape[2] == 1:
            return image

        b, g, r = cv2.split(image)
        zeros = np.zeros_like(b)

        canal = self.params.get('canal', 'Red (Vermelho)')
        
        if canal == 'Red (Vermelho)':
            return cv2.merge([zeros, zeros, r])
        elif canal == 'Green (Verde)':
            return cv2.merge([zeros, g, zeros])
        else:
            return cv2.merge([b, zeros, zeros])