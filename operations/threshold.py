"""Binarização / limiarização (Aulas 2 e 3): threshold, adaptiveThreshold e inRange."""

import cv2 as cv

from core.mat_vector import CHANNEL_NAMES
from core.operation import ChoiceParam, IntParam, Operation, gray_source, is_color, short_label, to_gray

THRESHOLD_TYPES = {
    "BINARY: > limiar → máximo, senão 0": "THRESH_BINARY",
    "BINARY_INV: > limiar → 0, senão máximo": "THRESH_BINARY_INV",
    "TRUNC: > limiar → limiar": "THRESH_TRUNC",
    "TOZERO: > limiar mantém, senão 0": "THRESH_TOZERO",
    "TOZERO_INV: > limiar → 0, senão mantém": "THRESH_TOZERO_INV",
}

AUTO_METHODS = {
    "Manual (usa o limiar acima)": None,
    "Otsu (automático)": "THRESH_OTSU",
    "Triângulo (automático)": "THRESH_TRIANGLE",
}


class Threshold(Operation):
    name = "Limiarização global"
    function = "cv.threshold"
    description = (
        "Compara cada pixel com um único limiar para a imagem toda. Com Otsu ou Triângulo o "
        "limiar é calculado automaticamente a partir do histograma (o limiar informado é "
        "ignorado) e o valor encontrado aparece abaixo."
    )
    params = (
        IntParam(key="limiar", label="Limiar", default=127, minimum=0, maximum=255),
        IntParam(key="maximo", label="Valor máximo", default=255, minimum=0, maximum=255),
        ChoiceParam(key="tipo", label="Tipo", default="BINARY: > limiar → máximo, senão 0",
                    options=THRESHOLD_TYPES),
        ChoiceParam(key="metodo", label="Cálculo do limiar", default="Manual (usa o limiar acima)",
                    options=AUTO_METHODS),
    )

    def apply(self, src, mats):
        auto = self.choice("metodo")
        flags = getattr(cv, self.choice("tipo")) + (getattr(cv, auto) if auto else 0)
        limiar, dst = cv.threshold(to_gray(src), 0 if auto else self["limiar"], self["maximo"], flags)
        self.info = f"Limiar utilizado: {limiar:g}"
        return dst

    def code(self, src, mats):
        lines, g = gray_source(src)
        auto = self.choice("metodo")
        flags = f"cv.{self.choice('tipo')}" + (f" + cv.{auto}" if auto else "")
        thresh = 0 if auto else self["limiar"]
        lines.append(f"limiar, dst = cv.threshold({g}, {thresh}, {self['maximo']}, {flags})")
        return "\n".join(lines)

    def title(self):
        method = short_label(self["metodo"])
        return f"Limiar · {method}" if self.choice("metodo") else f"Limiar · {self['limiar']}"


class AdaptiveThreshold(Operation):
    name = "Limiarização adaptativa"
    function = "cv.adaptiveThreshold"
    description = (
        "Em vez de um limiar único, calcula um limiar para cada pixel a partir da sua "
        "vizinhança (média ou média gaussiana) menos a constante C. Funciona bem com "
        "iluminação desigual."
    )
    params = (
        ChoiceParam(key="metodo", label="Método", default="Média (MEAN_C)",
                    options={"Média (MEAN_C)": "ADAPTIVE_THRESH_MEAN_C",
                             "Gaussiano (GAUSSIAN_C)": "ADAPTIVE_THRESH_GAUSSIAN_C"}),
        ChoiceParam(key="tipo", label="Tipo", default="BINARY",
                    options={"BINARY": "THRESH_BINARY", "BINARY_INV": "THRESH_BINARY_INV"}),
        IntParam(key="bloco", label="Tamanho do bloco", default=11, minimum=3, maximum=99, odd=True),
        IntParam(key="c", label="Constante C", default=2, minimum=-50, maximum=50),
        IntParam(key="maximo", label="Valor máximo", default=255, minimum=0, maximum=255),
    )

    def apply(self, src, mats):
        return cv.adaptiveThreshold(to_gray(src), self["maximo"], getattr(cv, self.choice("metodo")),
                                    getattr(cv, self.choice("tipo")), self["bloco"], self["c"])

    def code(self, src, mats):
        lines, g = gray_source(src)
        lines.append(f"dst = cv.adaptiveThreshold({g}, {self['maximo']}, cv.{self.choice('metodo')}, "
                     f"cv.{self.choice('tipo')}, {self['bloco']}, {self['c']})")
        return "\n".join(lines)


class InRange(Operation):
    name = "Faixa de valores (inRange)"
    function = "cv.inRange"
    description = (
        "Pixels dentro da faixa [mínimo, máximo] viram 255 e o resto 0 (limiarização com "
        "dois limiares). Em 3 canais, cada canal tem sua faixa: após converter para HSV dá "
        "para segmentar uma cor, como o verde de uma folha."
    )
    params = (
        ChoiceParam(key="modo", label="Aplicar em", default="1 canal (tons de cinza)",
                    options={"1 canal (tons de cinza)": 1, "3 canais (ex.: HSV ou BGR)": 3}),
        IntParam(key="min0", label="Canal 0 — mínimo", default=0),
        IntParam(key="max0", label="Canal 0 — máximo", default=127),
        IntParam(key="min1", label="Canal 1 — mínimo", default=0),
        IntParam(key="max1", label="Canal 1 — máximo", default=255),
        IntParam(key="min2", label="Canal 2 — mínimo", default=0),
        IntParam(key="max2", label="Canal 2 — máximo", default=255),
    )

    def _bounds(self):
        return (self["min0"], self["min1"], self["min2"]), (self["max0"], self["max1"], self["max2"])

    def apply(self, src, mats):
        if self.choice("modo") == 1:
            return cv.inRange(to_gray(src), self["min0"], self["max0"])
        if not is_color(src):
            raise ValueError("O modo '3 canais' precisa de um Mat de 3 canais.")
        low, high = self._bounds()
        names = CHANNEL_NAMES.get(self.src_space, ("c0", "c1", "c2"))
        self.info = "Faixas: " + ", ".join(f"{n} {lo}..{hi}" for n, lo, hi in zip(names, low, high))
        return cv.inRange(src, low, high)

    def code(self, src, mats):
        if self.choice("modo") == 1:
            lines, g = gray_source(src)
            lines.append(f"dst = cv.inRange({g}, {self['min0']}, {self['max0']})")
            return "\n".join(lines)
        low, high = self._bounds()
        return f"dst = cv.inRange(src, {low}, {high})"
