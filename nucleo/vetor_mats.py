import numpy as np
from dataclasses import dataclass

# Em C++ seria vector<Mat>. Em Python o Mat é um ndarray do numpy,
# então o vetor é basicamente uma lista de imagens.
#   mats[0] -> imagem original
#   mats[i] -> resultado da etapa i do pipeline

NOMES_CANAIS = {
    "BGR": ("B", "G", "R"),
    "RGB": ("R", "G", "B"),
    "HSV": ("H", "S", "V"),
    "HLS": ("H", "L", "S"),
    "Lab": ("L", "a", "b"),
    "Luv": ("L", "u", "v"),
    "XYZ": ("X", "Y", "Z"),
    "YCrCb": ("Y", "Cr", "Cb"),
    "GRAY": ("I",),
}

_PROFUNDIDADES = {
    np.uint8: "8U", np.int8: "8S", np.uint16: "16U", np.int16: "16S",
    np.int32: "32S", np.float32: "32F", np.float64: "64F",
}


def num_canais(mat):
    return 1 if mat.ndim == 2 else mat.shape[2]


def tipo_mat(mat):
    # mesmo nome que o OpenCV usa, ex: CV_8UC3 = 8 bits sem sinal, 3 canais
    profundidade = _PROFUNDIDADES.get(mat.dtype.type, str(mat.dtype))
    return f"CV_{profundidade}C{num_canais(mat)}"


def descrever(mat):
    h, w = mat.shape[:2]
    c = num_canais(mat)
    return f"{w}×{h} · {c} {'canal' if c == 1 else 'canais'} · {tipo_mat(mat)}"


@dataclass
class ItemMat:
    mat: np.ndarray
    rotulo: str
    espaco: str  # espaço de cor (BGR, HSV, GRAY...) pra saber o nome de cada canal

    @property
    def nomes_canais(self):
        nomes = NOMES_CANAIS.get(self.espaco, ())
        if len(nomes) != num_canais(self.mat):
            return tuple(f"c{i}" for i in range(num_canais(self.mat)))
        return nomes


class VetorMats:
    # usei os mesmos nomes de método do vector do C++ (push_back, at, back, size...)

    def __init__(self):
        self._itens = []

    def push_back(self, mat, rotulo, espaco):
        self._itens.append(ItemMat(mat, rotulo, espaco))

    def at(self, indice):
        return self._itens[indice].mat

    def item(self, indice):
        return self._itens[indice]

    def back(self):
        return self._itens[-1].mat

    def size(self):
        return len(self._itens)

    def empty(self):
        return not self._itens

    def resize(self, n):
        # mantém só mats[0..n-1]; uso isso pra reprocessar a partir de uma etapa
        del self._itens[n:]

    def clear(self):
        self._itens.clear()

    def __len__(self):
        return self.size()

    def __getitem__(self, indice):
        return self.at(indice)

    def __iter__(self):
        return (item.mat for item in self._itens)
