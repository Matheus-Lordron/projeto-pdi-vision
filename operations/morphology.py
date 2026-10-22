"""Morfologia matemática (Aula 3): erosão, dilatação e morphologyEx.

Funciona em imagens binárias, em tons de cinza e coloridas, sempre a partir de
um elemento estruturante (EE) criado com getStructuringElement.
"""

import cv2 as cv

from core.operation import ChoiceParam, IntParam, Operation, kernel_text, short_label

SHAPES = {
    "Retângulo (MORPH_RECT)": "MORPH_RECT",
    "Elipse (MORPH_ELLIPSE)": "MORPH_ELLIPSE",
    "Cruz (MORPH_CROSS)": "MORPH_CROSS",
}

ELEMENT_PARAMS = (
    ChoiceParam(key="forma", label="Elemento estruturante", default="Retângulo (MORPH_RECT)",
                options=SHAPES),
    IntParam(key="tamanho", label="Tamanho do EE", default=3, minimum=1, maximum=31, odd=True),
    IntParam(key="iteracoes", label="Iterações", default=1, minimum=1, maximum=20),
)


class _Morphology(Operation):
    def element(self):
        k = self["tamanho"]
        return cv.getStructuringElement(getattr(cv, self.choice("forma")), (k, k))

    def apply(self, src, mats):
        element = self.element()
        self.info = "Elemento estruturante:\n" + kernel_text(element)
        return self.transform(src, element)

    def transform(self, src, element):
        raise NotImplementedError

    def call_code(self) -> str:
        raise NotImplementedError

    def code(self, src, mats):
        k = self["tamanho"]
        return (
            f"elemento = cv.getStructuringElement(cv.{self.choice('forma')}, ({k}, {k}))\n"
            f"dst = {self.call_code()}"
        )


class Erode(_Morphology):
    name = "Erosão"
    function = "cv.erode"
    description = (
        "A região escura cresce sobre a clara: elimina picos positivos (detalhes claros) "
        "mais finos que o elemento estruturante. Em imagens binárias, afina os objetos "
        "brancos, separa objetos encostados e remove ruídos pequenos."
    )
    params = ELEMENT_PARAMS

    def transform(self, src, element):
        return cv.erode(src, element, iterations=self["iteracoes"])

    def call_code(self):
        return f"cv.erode(src, elemento, iterations={self['iteracoes']})"


class Dilate(_Morphology):
    name = "Dilatação"
    function = "cv.dilate"
    description = (
        "A região clara cresce sobre a escura: elimina picos negativos (buracos e falhas "
        "escuras) menores que o elemento estruturante e 'engorda' os objetos claros."
    )
    params = ELEMENT_PARAMS

    def transform(self, src, element):
        return cv.dilate(src, element, iterations=self["iteracoes"])

    def call_code(self):
        return f"cv.dilate(src, elemento, iterations={self['iteracoes']})"


MORPH_OPERATIONS = {
    "Abertura (erosão → dilatação)": "MORPH_OPEN",
    "Fechamento (dilatação → erosão)": "MORPH_CLOSE",
    "Gradiente (dilatação − erosão)": "MORPH_GRADIENT",
    "Top-hat (original − abertura)": "MORPH_TOPHAT",
    "Black-hat (fechamento − original)": "MORPH_BLACKHAT",
}


class MorphologyEx(_Morphology):
    name = "Abertura, fechamento, gradiente…"
    function = "cv.morphologyEx"
    description = (
        "Combinações de erosão e dilatação. Abertura remove ruídos e suaviza contornos; "
        "fechamento preenche buracos e fendas; gradiente realça as bordas; top-hat destaca "
        "picos (detalhes claros) e black-hat destaca vales (detalhes escuros)."
    )
    params = (
        ChoiceParam(key="operacao", label="Operação", default="Abertura (erosão → dilatação)",
                    options=MORPH_OPERATIONS),
    ) + ELEMENT_PARAMS

    def transform(self, src, element):
        return cv.morphologyEx(src, getattr(cv, self.choice("operacao")), element,
                               iterations=self["iteracoes"])

    def call_code(self):
        return (f"cv.morphologyEx(src, cv.{self.choice('operacao')}, elemento, "
                f"iterations={self['iteracoes']})")

    def title(self):
        return short_label(self["operacao"])
