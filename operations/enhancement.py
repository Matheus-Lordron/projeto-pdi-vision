"""Realce por transformações pontuais (Aula 2): B(x, y) = f[A(x, y)]."""

import cv2 as cv
import numpy as np

from core.operation import BoolParam, ChoiceParam, FloatParam, IntParam, Operation, fmt, is_color, to_gray


class BrightnessContrast(Operation):
    name = "Brilho e contraste"
    function = "cv.addWeighted"
    description = (
        "Aplica g(x) = α·f(x) + β: α (contraste) multiplica cada pixel e β (brilho) soma um "
        "valor, saturando em 0..255 como o convertTo do C++. O convertScaleAbs dos slides "
        "tira o valor absoluto, o que faria pixels escuros 'refletirem' com brilho negativo."
    )
    params = (
        FloatParam(key="alpha", label="Contraste (α)", default=1.0, minimum=0.0, maximum=3.0, step=0.05),
        IntParam(key="beta", label="Brilho (β)", default=0, minimum=-255, maximum=255),
    )

    def apply(self, src, mats):
        return cv.addWeighted(src, self["alpha"], src, 0, self["beta"])

    def code(self, src, mats):
        return (
            "# g(x) = α·f(x) + β com saturação (src entra com peso α e peso 0)\n"
            f"dst = cv.addWeighted(src, {fmt(self['alpha'])}, src, 0, {self['beta']})"
        )


class Negative(Operation):
    name = "Negativo"
    function = "255 - src"
    description = (
        "Inverte a imagem: subtrai cada pixel da intensidade máxima do canal (255). "
        "Regiões claras ficam escuras e vice-versa."
    )

    def apply(self, src, mats):
        return 255 - src

    def code(self, src, mats):
        return "dst = 255 - src"


class ContrastStretch(Operation):
    name = "Alargamento de contraste"
    function = "aritmética NumPy"
    description = (
        "Leva a faixa de interesse [min1, max1] para uma nova faixa [min2, max2]: "
        "f(N) = (N − min1)(max2 − min2) / (max1 − min1) + min2. Com 'automático', "
        "min1 e max1 são o menor e o maior valor da imagem (normalização)."
    )
    params = (
        BoolParam(key="auto", label="min1/max1 automáticos", default=True,
                  help="Usa o menor e o maior valor presentes na imagem"),
        IntParam(key="min1", label="min1 (entrada)", default=0),
        IntParam(key="max1", label="max1 (entrada)", default=255),
        IntParam(key="min2", label="min2 (saída)", default=0),
        IntParam(key="max2", label="max2 (saída)", default=255),
    )

    def _window(self, src):
        if self["auto"]:
            return int(src.min()), int(src.max())
        return self["min1"], self["max1"]

    def apply(self, src, mats):
        min1, max1 = self._window(src)
        if max1 <= min1:
            raise ValueError("max1 precisa ser maior que min1.")
        min2, max2 = self["min2"], self["max2"]
        self.info = f"Faixa de entrada usada: [{min1}, {max1}] → [{min2}, {max2}]"
        n = src.astype(np.float32)
        dst = (n - min1) * (max2 - min2) / (max1 - min1) + min2
        return np.clip(dst, min(min2, max2), max(min2, max2)).astype(np.uint8)

    def code(self, src, mats):
        min2, max2 = self["min2"], self["max2"]
        window = ("int(src.min()), int(src.max())" if self["auto"]
                  else f"{self['min1']}, {self['max1']}")
        return (
            f"min1, max1 = {window}\n"
            f"min2, max2 = {min2}, {max2}\n"
            "n = src.astype(np.float32)\n"
            "dst = (n - min1) * (max2 - min2) / (max1 - min1) + min2\n"
            f"dst = np.clip(dst, {min(min2, max2)}, {max(min2, max2)}).astype(np.uint8)"
        )


class EqualizeHist(Operation):
    name = "Equalização de histograma"
    function = "cv.equalizeHist"
    description = (
        "Redistribui os níveis de cinza de forma mais uniforme no histograma, aumentando "
        "o contraste geral. O equalizeHist trabalha com 1 canal: imagens coloridas são "
        "convertidas para cinza ou equalizadas canal a canal."
    )
    params = (
        ChoiceParam(key="modo", label="Se a entrada for colorida", default="Converter para cinza",
                    options={"Converter para cinza": "gray",
                             "Cada canal (split → equalizeHist → merge)": "split"}),
    )

    def apply(self, src, mats):
        if is_color(src) and self.choice("modo") == "split":
            return cv.merge([cv.equalizeHist(c) for c in cv.split(src)])
        return cv.equalizeHist(to_gray(src))

    def code(self, src, mats):
        if not is_color(src):
            return "dst = cv.equalizeHist(src)"
        if self.choice("modo") == "split":
            return "dst = cv.merge([cv.equalizeHist(c) for c in cv.split(src)])"
        return "gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)\ndst = cv.equalizeHist(gray)"
