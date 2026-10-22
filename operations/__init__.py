"""Catálogo de operações disponíveis, organizado na ordem dos requisitos do trabalho."""

from dataclasses import dataclass

from .algebraic import Arithmetic, Logical
from .color import ConvertColor, GrayFormula, SplitChannel
from .edges import Canny, HighPassMask, Kirsch, Laplacian, Prewitt, Roberts, Sobel
from .enhancement import BrightnessContrast, ContrastStretch, EqualizeHist, Negative
from .morphology import Dilate, Erode, MorphologyEx
from .smoothing import BilateralFilter, GaussianBlur, MeanBlur, MedianBlur
from .threshold import AdaptiveThreshold, InRange, Threshold


@dataclass(frozen=True)
class Category:
    name: str
    description: str
    operations: tuple


CATALOG = (
    Category("Conversão de cor",
             "Aula 1 — espaços de cor (BGR, HSV, Lab...), separação de canais e tons de cinza.",
             (ConvertColor, SplitChannel, GrayFormula)),
    Category("Realce (transformações pontuais)",
             "Aula 2 — cada pixel de saída depende só do pixel de entrada: B(x,y) = f[A(x,y)].",
             (BrightnessContrast, Negative, ContrastStretch, EqualizeHist)),
    Category("Suavização (passa-baixa)",
             "Aula 2 — convolução com a vizinhança para reduzir ruído; borra a imagem.",
             (MeanBlur, GaussianBlur, MedianBlur, BilateralFilter)),
    Category("Detecção de bordas (passa-alta)",
             "Aula 2 — realça as transições entre regiões: gradientes e máscaras passa-alta.",
             (Sobel, Laplacian, Canny, Prewitt, Roberts, Kirsch, HighPassMask)),
    Category("Binarização (limiarização)",
             "Aulas 2 e 3 — separa a imagem em preto e branco a partir de limiares.",
             (Threshold, AdaptiveThreshold, InRange)),
    Category("Morfologia matemática",
             "Aula 3 — transformações pela forma, usando um elemento estruturante.",
             (Erode, Dilate, MorphologyEx)),
    Category("Operações entre Mats",
             "Aula 2 — aritmética e lógica pixel a pixel entre dois Mats do vetor.",
             (Arithmetic, Logical)),
)
