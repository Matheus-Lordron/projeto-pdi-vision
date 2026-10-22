"""Conversão de cor (Aula 1): cvtColor, split/merge e fórmulas de tons de cinza."""

import cv2 as cv
import numpy as np

from core.mat_vector import CHANNEL_NAMES, channels
from core.operation import ChoiceParam, Operation, is_color, short_label

# rótulo -> (código do cvtColor, espaço de cor resultante)
CONVERSIONS = {
    "BGR → GRAY (tons de cinza)": ("COLOR_BGR2GRAY", "GRAY"),
    "BGR → HSV": ("COLOR_BGR2HSV", "HSV"),
    "BGR → HLS": ("COLOR_BGR2HLS", "HLS"),
    "BGR → Lab": ("COLOR_BGR2Lab", "Lab"),
    "BGR → Luv": ("COLOR_BGR2Luv", "Luv"),
    "BGR → XYZ": ("COLOR_BGR2XYZ", "XYZ"),
    "BGR → YCrCb": ("COLOR_BGR2YCrCb", "YCrCb"),
    "BGR → RGB": ("COLOR_BGR2RGB", "RGB"),
    "GRAY → BGR": ("COLOR_GRAY2BGR", "BGR"),
    "HSV → BGR": ("COLOR_HSV2BGR", "BGR"),
    "HLS → BGR": ("COLOR_HLS2BGR", "BGR"),
    "Lab → BGR": ("COLOR_Lab2BGR", "BGR"),
    "Luv → BGR": ("COLOR_Luv2BGR", "BGR"),
    "XYZ → BGR": ("COLOR_XYZ2BGR", "BGR"),
    "YCrCb → BGR": ("COLOR_YCrCb2BGR", "BGR"),
}


class ConvertColor(Operation):
    name = "Conversão de espaço de cor"
    function = "cv.cvtColor"
    description = (
        "O imread carrega a imagem em BGR. O cvtColor a converte para outro espaço de cor "
        "(GRAY, HSV, HLS, Lab, Luv, XYZ, YCrCb) ou de volta para BGR. Mats de 3 canais fora "
        "do BGR aparecem com 'cores falsas', exatamente como no cv.imshow."
    )
    params = (
        ChoiceParam(key="conversao", label="Conversão", default="BGR → HSV", options=CONVERSIONS),
    )

    def apply(self, src, mats):
        code, _ = self.choice("conversao")
        expects_gray = code.startswith("COLOR_GRAY")
        if expects_gray == is_color(src):
            wanted = "1 canal" if expects_gray else "3 canais"
            raise ValueError(f"Esta conversão espera um Mat de {wanted}; a entrada tem {channels(src)}.")
        return cv.cvtColor(src, getattr(cv, code))

    def code(self, src, mats):
        return f"dst = cv.cvtColor(src, cv.{self.choice('conversao')[0]})"

    def output_space(self, src_space, dst):
        return self.choice("conversao")[1]

    def title(self):
        return short_label(self["conversao"])


class SplitChannel(Operation):
    name = "Separar canal (split)"
    function = "cv.split / cv.merge"
    description = (
        "Divide um Mat de 3 canais em 3 Mats de 1 canal (split) e mantém o escolhido. "
        "No modo '3 canais', o canal é juntado (merge) com zeros nos demais, mostrando "
        "sua contribuição na cor. Use depois de uma conversão para ver H, S, V etc."
    )
    params = (
        ChoiceParam(key="canal", label="Canal", default="Canal 0",
                    options={"Canal 0": 0, "Canal 1": 1, "Canal 2": 2}),
        ChoiceParam(key="modo", label="Exibir como", default="1 canal (tons de cinza)",
                    options={"1 canal (tons de cinza)": False, "3 canais (merge com zeros)": True}),
    )

    def apply(self, src, mats):
        if not is_color(src):
            raise ValueError("A entrada já tem 1 canal; não há canais para separar.")
        c = self.choice("canal")
        names = CHANNEL_NAMES.get(self.src_space, ("c0", "c1", "c2"))
        self.info = f"Canal {c} de um Mat {self.src_space} = {names[c]}"
        canais = cv.split(src)
        if self.choice("modo"):
            zeros = np.zeros_like(canais[c])
            return cv.merge([canais[i] if i == c else zeros for i in range(3)])
        return canais[c]

    def code(self, src, mats):
        c = self.choice("canal")
        lines = ["canais = cv.split(src)"]
        if self.choice("modo"):
            merged = ", ".join(f"canais[{i}]" if i == c else "zeros" for i in range(3))
            lines += [f"zeros = np.zeros_like(canais[{c}])", f"dst = cv.merge([{merged}])"]
        else:
            lines.append(f"dst = canais[{c}]")
        return "\n".join(lines)

    def title(self):
        return f"Split · canal {self.choice('canal')}"


# rótulo -> pesos (R, G, B) da fórmula (slide "Conversão RGB - Tons de Cinza")
GRAY_FORMULAS = {
    "Média: (R + G + B) / 3": None,
    "Clássica: 0,3R + 0,59G + 0,11B": (0.3, 0.59, 0.11),
    "Imagens escuras: 0,23R + 0,65G + 0,12B": (0.23, 0.65, 0.12),
}


class GrayFormula(Operation):
    name = "Tons de cinza por fórmula"
    function = "cv.split + aritmética"
    description = (
        "Calcula o cinza pixel a pixel a partir dos canais R, G e B. A média simples "
        "costuma escurecer a imagem, pois o olho é mais sensível ao verde e menos ao azul; "
        "as fórmulas ponderadas compensam isso."
    )
    params = (
        ChoiceParam(key="formula", label="Fórmula", default="Clássica: 0,3R + 0,59G + 0,11B",
                    options=GRAY_FORMULAS),
    )

    def apply(self, src, mats):
        if not is_color(src):
            raise ValueError("A fórmula precisa de um Mat BGR de 3 canais.")
        b, g, r = cv.split(src.astype(np.float32))
        weights = self.choice("formula")
        if weights is None:
            gray = (r + g + b) / 3
        else:
            wr, wg, wb = weights
            gray = wr * r + wg * g + wb * b
        return np.clip(gray, 0, 255).astype(np.uint8)

    def code(self, src, mats):
        weights = self.choice("formula")
        if weights is None:
            expr = "(r + g + b) / 3"
        else:
            wr, wg, wb = weights
            expr = f"{wr:g} * r + {wg:g} * g + {wb:g} * b"
        return (
            "b, g, r = cv.split(src.astype(np.float32))\n"
            f"gray = {expr}\n"
            "dst = np.clip(gray, 0, 255).astype(np.uint8)"
        )
