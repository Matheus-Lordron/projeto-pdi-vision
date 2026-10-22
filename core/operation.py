"""Base das operações do pipeline e descritores dos seus parâmetros.

Cada operação declara seus parâmetros (``params``); a interface lê essa lista e
monta sozinha os controles (slider, combobox, checkbox...). Assim, criar uma
operação nova não exige mexer em nenhum arquivo da interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

import cv2 as cv
import numpy as np

from .mat_vector import MatVector


@dataclass(kw_only=True)
class Param:
    key: str
    label: str
    default: Any
    help: str = ""

    def coerce(self, value):
        return value


@dataclass(kw_only=True)
class IntParam(Param):
    minimum: int = 0
    maximum: int = 255
    step: int = 1
    odd: bool = False  # kernels (ksize) do OpenCV geralmente precisam ser ímpares

    def coerce(self, value):
        value = int(min(max(int(value), self.minimum), self.maximum))
        if self.odd and value % 2 == 0:
            value = value + 1 if value < self.maximum else value - 1
        return value


@dataclass(kw_only=True)
class FloatParam(Param):
    minimum: float = 0.0
    maximum: float = 1.0
    step: float = 0.1
    decimals: int = 2

    def coerce(self, value):
        return round(min(max(float(value), self.minimum), self.maximum), self.decimals)


@dataclass(kw_only=True)
class ChoiceParam(Param):
    options: dict  # rótulo exibido -> valor usado pela operação

    def coerce(self, value):
        return value if value in self.options else self.default


@dataclass(kw_only=True)
class BoolParam(Param):
    def coerce(self, value):
        return bool(value)


INPUT_REF = -1  # MatRefParam: "a entrada desta etapa" (Mat[i-1])


@dataclass(kw_only=True)
class MatRefParam(Param):
    """Escolhe um Mat anterior do vetor (ex.: subtrair Mat[0] do Mat atual)."""

    def coerce(self, value):
        return int(value)


# ----------------------------------------------------------------------------
# Utilidades comuns às operações
# ----------------------------------------------------------------------------

GRAY_LINE = "gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)"


def is_color(mat: np.ndarray) -> bool:
    return mat.ndim == 3 and mat.shape[2] >= 3


def to_gray(mat: np.ndarray) -> np.ndarray:
    """Operações que exigem 1 canal (limiar, Canny...) convertem como nos slides."""
    return cv.cvtColor(mat, cv.COLOR_BGR2GRAY) if is_color(mat) else mat


def gray_source(src: np.ndarray) -> tuple[list[str], str]:
    """Linhas de código para obter a imagem cinza e o nome da variável resultante."""
    return ([GRAY_LINE], "gray") if is_color(src) else ([], "src")


def fmt(value) -> str:
    """Formata números para o código exibido (3 -> '3', 0.5 -> '0.5')."""
    if isinstance(value, float):
        return f"{value:g}"
    return repr(value)


def kernel_text(kernel: np.ndarray) -> str:
    rows = ["[" + " ".join(f"{v:>3g}" for v in row) + " ]" for row in kernel]
    return "\n".join(rows)


def kernel_code(kernel: np.ndarray, dtype="np.float32") -> str:
    rows = ", ".join("[" + ", ".join(f"{v:g}" for v in row) + "]" for row in kernel)
    return f"np.array([{rows}], dtype={dtype})"


class Operation(ABC):
    """Uma etapa do pipeline: recebe o Mat anterior e devolve um novo Mat."""

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    function: ClassVar[str] = ""  # função OpenCV principal (exibida no catálogo)
    params: ClassVar[tuple[Param, ...]] = ()

    def __init__(self):
        self.values = {p.key: p.default for p in self.params}
        self.enabled = True
        self.source = INPUT_REF  # Mat de entrada: o anterior ou qualquer Mat[k] do vetor
        self.src_space = "BGR"  # espaço de cor da entrada na última execução
        self.error: str | None = None
        self.info: str | None = None  # resultado didático (ex.: limiar do Otsu)

    def __getitem__(self, key):
        return self.values[key]

    def param(self, key: str) -> Param:
        return next(p for p in self.params if p.key == key)

    def choice(self, key: str):
        """Valor associado ao rótulo escolhido em um ChoiceParam."""
        return self.param(key).options[self.values[key]]

    def set_value(self, key: str, value):
        self.values[key] = self.param(key).coerce(value)

    def run(self, src: np.ndarray, mats: MatVector, src_space: str = "BGR") -> np.ndarray:
        self.error = None
        self.info = None
        self.src_space = src_space
        return self.apply(src, mats)

    @abstractmethod
    def apply(self, src: np.ndarray, mats: MatVector) -> np.ndarray:
        """Processa ``src`` (= Mat[i-1]); ``mats`` dá acesso aos Mats anteriores."""

    @abstractmethod
    def code(self, src: np.ndarray, mats: MatVector) -> str:
        """Código Python/OpenCV equivalente, com os valores atuais dos parâmetros.

        Convenção: ``src`` é o Mat de entrada, ``mats`` o vetor e ``dst`` a saída.
        """

    def output_space(self, src_space: str, dst: np.ndarray) -> str:
        if dst.ndim == 2:
            return "GRAY"
        return src_space if src_space != "GRAY" else "BGR"

    def title(self) -> str:
        """Rótulo curto do Mat gerado, exibido no vetor de Mats."""
        return self.name

    def summary(self) -> str:
        return ", ".join(f"{p.label}: {self.values[p.key]}" for p in self.params)


def short_label(option: str) -> str:
    """'Abertura (erosão → dilatação)' -> 'Abertura' (para títulos curtos)."""
    return option.split(" (")[0]
