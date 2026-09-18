from abc import ABC, abstractmethod
import numpy as np

class FilterBase(ABC):
    def __init__(self, name: str):
        self.name = name
        self.is_enabled = True
        self.params = {} # Dicionário para guardar os valores atuais (ex: {'ksize': 5})

    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        Recebe a imagem da camada anterior, aplica o processamento do OpenCV
        usando os valores de self.params, e retorna a nova imagem.
        """
        pass

    @abstractmethod
    def get_ui_schema(self) -> dict:
        """
        Retorna o dicionário de configuração da interface.
        Exemplo:
        return {
            'ksize': {'type': 'slider', 'min': 1, 'max': 31, 'step': 2, 'default': 3}
        }
        """
        pass

    def update_param(self, param_name: str, value):
        """Atualiza um parâmetro dinamicamente via interface gráfica."""
        if param_name in self.params:
            self.params[param_name] = value