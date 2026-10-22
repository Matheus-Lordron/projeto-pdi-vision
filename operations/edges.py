"""Detectores de borda / filtros passa-alta (Aula 2).

Como nos exemplos da aula, os detectores trabalham sobre a imagem em tons de
cinza: se a entrada for colorida, ela é convertida com cvtColor(BGR2GRAY).
"""

import cv2 as cv
import numpy as np

from core.operation import (
    BoolParam, ChoiceParam, IntParam, Operation, gray_source, kernel_code, kernel_text, to_gray,
)


def _k(rows) -> np.ndarray:
    return np.array(rows, dtype=np.float32)


class _GradientPair(Operation):
    """Base dos operadores com duas máscaras (Gx e Gy) combinadas por addWeighted."""

    KX: np.ndarray
    KY: np.ndarray
    DIRECTIONS: dict  # rótulo -> "xy" | "x" | "y"

    def _gradients(self, gray):
        raise NotImplementedError

    def _gradient_lines(self, g: str, axis: str) -> list[str]:
        """Linhas de código que calculam ``grad_x`` ou ``grad_y`` a partir de ``g``."""
        raise NotImplementedError

    def apply(self, src, mats):
        gray = to_gray(src)
        grad_x, grad_y = self._gradients(gray)
        direction = self.choice("direcao")
        abs_grad_x = cv.convertScaleAbs(grad_x)
        abs_grad_y = cv.convertScaleAbs(grad_y)
        if direction == "x":
            return abs_grad_x
        if direction == "y":
            return abs_grad_y
        return cv.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    def code(self, src, mats):
        lines, g = gray_source(src)
        direction = self.choice("direcao")
        for axis in ("x", "y"):
            if axis in direction:
                lines += self._gradient_lines(g, axis)
                lines.append(f"abs_grad_{axis} = cv.convertScaleAbs(grad_{axis})")
        if direction == "xy":
            lines.append("dst = cv.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)")
        else:
            lines.append(f"dst = abs_grad_{direction}")
        return "\n".join(lines)


_AXIS_DIRECTIONS = {
    "Gx e Gy (magnitude)": "xy",
    "Somente Gx (mudanças verticais)": "x",
    "Somente Gy (mudanças horizontais)": "y",
}


class Sobel(_GradientPair):
    name = "Sobel"
    function = "cv.Sobel"
    description = (
        "Calcula o gradiente (1ª derivada) nas direções x e y. Os resultados em CV_64F "
        "guardam valores negativos; o convertScaleAbs tira o valor absoluto e volta para "
        "8 bits; por fim, addWeighted junta |Gx| e |Gy|."
    )
    DIRECTIONS = _AXIS_DIRECTIONS
    params = (
        IntParam(key="ksize", label="Tamanho do kernel", default=3, minimum=1, maximum=7, odd=True),
        ChoiceParam(key="direcao", label="Gradiente", default="Gx e Gy (magnitude)", options=DIRECTIONS),
    )

    def _gradients(self, gray):
        k = self["ksize"]
        grad_x = cv.Sobel(gray, cv.CV_64F, 1, 0, ksize=k, borderType=cv.BORDER_REPLICATE)
        grad_y = cv.Sobel(gray, cv.CV_64F, 0, 1, ksize=k, borderType=cv.BORDER_REPLICATE)
        return grad_x, grad_y

    def _gradient_lines(self, g, axis):
        dx, dy = (1, 0) if axis == "x" else (0, 1)
        return [f"grad_{axis} = cv.Sobel({g}, cv.CV_64F, {dx}, {dy}, ksize={self['ksize']}, "
                "borderType=cv.BORDER_REPLICATE)"]


class Prewitt(_GradientPair):
    name = "Prewitt"
    function = "cv.filter2D"
    description = (
        "Gradiente com as máscaras de Prewitt (pesos iguais em cada coluna/linha), aplicadas "
        "por convolução com filter2D. Semelhante ao Sobel, porém sem dar peso maior ao "
        "pixel central."
    )
    KX = _k([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
    KY = _k([[1, 1, 1], [0, 0, 0], [-1, -1, -1]])
    DIRECTIONS = {
        "Vertical e horizontal (magnitude)": "xy",
        "Somente vertical": "x",
        "Somente horizontal": "y",
    }
    params = (
        ChoiceParam(key="direcao", label="Máscara", default="Vertical e horizontal (magnitude)",
                    options=DIRECTIONS),
    )

    def _gradients(self, gray):
        return cv.filter2D(gray, cv.CV_64F, self.KX), cv.filter2D(gray, cv.CV_64F, self.KY)

    def _gradient_lines(self, g, axis):
        kernel = self.KX if axis == "x" else self.KY
        return [f"k{axis} = {kernel_code(kernel)}", f"grad_{axis} = cv.filter2D({g}, cv.CV_64F, k{axis})"]


class Roberts(Prewitt):
    name = "Roberts"
    description = (
        "Operador de Roberts: duas máscaras 2×2 que calculam diferenças nas diagonais. "
        "Simples e rápido, porém mais sensível a ruído."
    )
    KX = _k([[1, 0], [0, -1]])
    KY = _k([[0, 1], [-1, 0]])
    DIRECTIONS = {
        "As duas diagonais (magnitude)": "xy",
        "Somente diagonal [1 0; 0 -1]": "x",
        "Somente diagonal [0 1; -1 0]": "y",
    }
    params = (
        ChoiceParam(key="direcao", label="Máscara", default="As duas diagonais (magnitude)",
                    options=DIRECTIONS),
    )


class Laplacian(Operation):
    name = "Laplace"
    function = "cv.Laplacian"
    description = (
        "Usa a 2ª derivada e detecta bordas em todas as direções de uma vez. Com CV_8U "
        "(como no slide) as respostas negativas são cortadas para 0; com CV_64F elas são "
        "mantidas e o convertScaleAbs as transforma em valor absoluto."
    )
    params = (
        IntParam(key="ksize", label="Tamanho do kernel", default=3, minimum=1, maximum=7, odd=True),
        ChoiceParam(key="ddepth", label="Profundidade (ddepth)", default="CV_64F (mantém negativos)",
                    options={"CV_64F (mantém negativos)": "CV_64F",
                             "CV_8U (como no slide)": "CV_8U"}),
    )

    def apply(self, src, mats):
        dst = cv.Laplacian(to_gray(src), getattr(cv, self.choice("ddepth")), ksize=self["ksize"],
                           borderType=cv.BORDER_REPLICATE)
        return cv.convertScaleAbs(dst)

    def code(self, src, mats):
        lines, g = gray_source(src)
        lines += [
            f"lap = cv.Laplacian({g}, cv.{self.choice('ddepth')}, ksize={self['ksize']}, "
            "borderType=cv.BORDER_REPLICATE)",
            "dst = cv.convertScaleAbs(lap)",
        ]
        return "\n".join(lines)


class Canny(Operation):
    name = "Canny"
    function = "cv.Canny"
    description = (
        "Um dos melhores detectores: suaviza com Gaussiano, calcula o gradiente, afina as "
        "bordas e usa 2 limiares. Acima do superior é borda; abaixo do inferior é descartado; "
        "entre os dois só é borda se estiver ligado a um pixel forte."
    )
    params = (
        IntParam(key="t1", label="Limiar inferior", default=50, minimum=0, maximum=500),
        IntParam(key="t2", label="Limiar superior", default=150, minimum=0, maximum=500),
        IntParam(key="aperture", label="Kernel do Sobel", default=3, minimum=3, maximum=7, odd=True),
        BoolParam(key="l2", label="L2gradient", default=False,
                  help="Usa √(Gx² + Gy²) em vez de |Gx| + |Gy| para a força do gradiente"),
    )

    def apply(self, src, mats):
        return cv.Canny(to_gray(src), self["t1"], self["t2"], apertureSize=self["aperture"],
                        L2gradient=self["l2"])

    def code(self, src, mats):
        lines, g = gray_source(src)
        lines.append(f"dst = cv.Canny({g}, {self['t1']}, {self['t2']}, "
                     f"apertureSize={self['aperture']}, L2gradient={self['l2']})")
        return "\n".join(lines)


# Máscaras dos slides "Filtros passa alta" (direcionais e não direcionais) e "Line Masks"
HIGH_PASS_MASKS = {
    "Não direcional — Alta": _k([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]]),
    "Não direcional — Média": _k([[0, -1, 0], [-1, 4, -1], [0, -1, 0]]),
    "Não direcional — Baixa": _k([[1, -2, 1], [-2, 3, -2], [1, -2, 1]]),
    "Direcional — Norte": _k([[1, 1, 1], [1, -2, 1], [-1, -1, -1]]),
    "Direcional — Nordeste": _k([[1, 1, 1], [-1, -2, 1], [-1, -1, 1]]),
    "Direcional — Leste": _k([[-1, 1, 1], [-1, -2, 1], [-1, 1, 1]]),
    "Direcional — Sudeste": _k([[-1, -1, 1], [-1, -2, 1], [1, 1, 1]]),
    "Direcional — Sul": _k([[-1, -1, -1], [1, -2, 1], [1, 1, 1]]),
    "Direcional — Sudoeste": _k([[1, -1, -1], [1, -2, -1], [1, 1, 1]]),
    "Direcional — Oeste": _k([[1, 1, -1], [1, -2, -1], [1, 1, -1]]),
    "Direcional — Noroeste": _k([[1, 1, 1], [1, -2, -1], [1, -1, -1]]),
    "Line mask — Horizontal": _k([[-1, -1, -1], [2, 2, 2], [-1, -1, -1]]),
    "Line mask — Vertical": _k([[-1, 2, -1], [-1, 2, -1], [-1, 2, -1]]),
    "Line mask — +45°": _k([[-1, -1, 2], [-1, 2, -1], [2, -1, -1]]),
    "Line mask — −45°": _k([[2, -1, -1], [-1, 2, -1], [-1, -1, 2]]),
}


class HighPassMask(Operation):
    name = "Máscara passa-alta (filter2D)"
    function = "cv.filter2D"
    description = (
        "Convolução com as máscaras 3×3 vistas em aula: não direcionais (realçam bordas em "
        "qualquer direção), direcionais (realçam uma direção) e line masks (detectam linhas). "
        "Com ddepth = -1 a saída é 8 bits e valores negativos viram 0."
    )
    params = (
        ChoiceParam(key="mascara", label="Máscara", default="Não direcional — Alta",
                    options=HIGH_PASS_MASKS),
    )

    def apply(self, src, mats):
        kernel = self.choice("mascara")
        self.info = "Máscara:\n" + kernel_text(kernel)
        return cv.filter2D(to_gray(src), -1, kernel)

    def code(self, src, mats):
        lines, g = gray_source(src)
        lines += [f"filtro = {kernel_code(self.choice('mascara'))}", f"dst = cv.filter2D({g}, -1, filtro)"]
        return "\n".join(lines)


# As 8 máscaras de Kirsch (uma por direção da bússola)
KIRSCH_MASKS = [
    _k([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]]),
    _k([[-3, 5, 5], [-3, 0, 5], [-3, -3, -3]]),
    _k([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]]),
    _k([[-3, -3, -3], [-3, 0, 5], [-3, 5, 5]]),
    _k([[-3, -3, -3], [-3, 0, -3], [5, 5, 5]]),
    _k([[-3, -3, -3], [5, 0, -3], [5, 5, -3]]),
    _k([[5, -3, -3], [5, 0, -3], [5, -3, -3]]),
    _k([[5, 5, -3], [5, 0, -3], [-3, -3, -3]]),
]


class Kirsch(Operation):
    name = "Kirsch"
    function = "cv.filter2D"
    description = (
        "Aplica as 8 máscaras de Kirsch (uma para cada direção) e, em cada pixel, fica com "
        "a maior resposta. Detecta bordas em qualquer direção."
    )

    def apply(self, src, mats):
        gray = to_gray(src)
        respostas = [cv.filter2D(gray, cv.CV_32F, k) for k in KIRSCH_MASKS]
        return cv.convertScaleAbs(np.max(respostas, axis=0))

    def code(self, src, mats):
        lines, g = gray_source(src)
        masks = ",\n    ".join(kernel_code(k) for k in KIRSCH_MASKS)
        lines += [
            f"kirsch = [\n    {masks},\n]",
            f"respostas = [cv.filter2D({g}, cv.CV_32F, k) for k in kirsch]",
            "dst = cv.convertScaleAbs(np.max(respostas, axis=0))",
        ]
        return "\n".join(lines)
