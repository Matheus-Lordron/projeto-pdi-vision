import cv2
import numpy as np

class ImageState:
    def __init__(self):
        self.original_image = None
        self.current_image = None

    def load_image(self, filepath: str) -> bool:
        """Carrega a imagem usando o OpenCV (BGR)."""
        img = cv2.imread(filepath)
        if img is not None:
            self.original_image = img.copy()
            self.current_image = img.copy()
            return True
        return False

    def get_original(self) -> np.ndarray:
        return self.original_image

    def update_current(self, image: np.ndarray):
        self.current_image = image.copy()