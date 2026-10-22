"""Vetor de Mats: a estrutura que guarda todo o histórico do processamento.

Em C++ o OpenCV usa ``std::vector<cv::Mat>``; em Python cada ``cv::Mat`` é um
``numpy.ndarray`` e o vetor é uma lista. Esta classe encapsula essa lista e
guarda, junto de cada Mat, o nome da etapa que o gerou e o espaço de cor dos
seus canais (para a interface saber se um pixel é B,G,R ou H,S,V, por exemplo).

    Mat[0] -> imagem original (lida com imread)
    Mat[i] -> saída da etapa i do pipeline, que recebeu Mat[i-1] como entrada
"""

from dataclasses import dataclass

import numpy as np

# Nome dos canais de cada espaço de cor, na ordem em que o OpenCV os armazena
CHANNEL_NAMES = {
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

_DEPTH_NAMES = {
    np.uint8: "8U", np.int8: "8S", np.uint16: "16U", np.int16: "16S",
    np.int32: "32S", np.float32: "32F", np.float64: "64F",
}


def channels(mat: np.ndarray) -> int:
    return 1 if mat.ndim == 2 else mat.shape[2]


def mat_type(mat: np.ndarray) -> str:
    """Tipo do Mat no padrão do OpenCV, ex.: CV_8UC3 (8 bits, sem sinal, 3 canais)."""
    depth = _DEPTH_NAMES.get(mat.dtype.type, str(mat.dtype))
    return f"CV_{depth}C{channels(mat)}"


def describe(mat: np.ndarray) -> str:
    h, w = mat.shape[:2]
    c = channels(mat)
    return f"{w}×{h} · {c} {'canal' if c == 1 else 'canais'} · {mat_type(mat)}"


@dataclass
class MatEntry:
    mat: np.ndarray
    label: str
    space: str

    @property
    def channel_names(self) -> tuple:
        names = CHANNEL_NAMES.get(self.space, ())
        if len(names) != channels(self.mat):
            return tuple(f"c{i}" for i in range(channels(self.mat)))
        return names


class MatVector:
    """Equivalente ao ``vector<Mat>``: push_back, at, back, size, resize, clear."""

    def __init__(self):
        self._entries: list[MatEntry] = []

    def push_back(self, mat: np.ndarray, label: str, space: str):
        self._entries.append(MatEntry(mat, label, space))

    def at(self, index: int) -> np.ndarray:
        return self._entries[index].mat

    def entry(self, index: int) -> MatEntry:
        return self._entries[index]

    def back(self) -> np.ndarray:
        return self._entries[-1].mat

    def size(self) -> int:
        return len(self._entries)

    def empty(self) -> bool:
        return not self._entries

    def resize(self, n: int):
        """Mantém apenas Mat[0..n-1] (usado para reprocessar a partir de uma etapa)."""
        del self._entries[n:]

    def clear(self):
        self._entries.clear()

    def __len__(self):
        return self.size()

    def __getitem__(self, index: int) -> np.ndarray:
        return self.at(index)

    def __iter__(self):
        return (e.mat for e in self._entries)
