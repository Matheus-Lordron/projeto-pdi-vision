import numpy as np
from typing import List
from .filter_base import FilterBase
from .image_state import ImageState

class ImagePipeline:
    def __init__(self, image_state: ImageState):
        self.image_state = image_state
        self.filters: List[FilterBase] = []

    def add_filter(self, new_filter: FilterBase):
        self.filters.append(new_filter)
        
    def remove_filter(self, index: int):
        if 0 <= index < len(self.filters):
            self.filters.pop(index)

    def move_filter(self, old_index: int, new_index: int):
        """Muda a ordem de processamento na pilha."""
        if 0 <= old_index < len(self.filters) and 0 <= new_index < len(self.filters):
            item = self.filters.pop(old_index)
            self.filters.insert(new_index, item)

    def process(self) -> np.ndarray:
        """
        Pega a imagem original e passa por todos os filtros ativos na ordem.
        """
        img = self.image_state.get_original()
        if img is None:
            return None

        # O output de um filtro é o input do próximo
        for f in self.filters:
            if f.is_enabled:
                img = f.apply(img)

        # Atualiza o estado atual com o resultado final
        self.image_state.update_current(img)
        return self.image_state.current_image