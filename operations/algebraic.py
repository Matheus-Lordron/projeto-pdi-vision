"""Operações algébricas e lógicas entre dois Mats do vetor (Aula 2).

Os operandos são escolhidos entre os Mats já calculados: a entrada da etapa
(Mat[i-1]) ou qualquer Mat[k] anterior. Assim dá para reproduzir os exemplos da
aula, como ``diferencaErosao = image - erosao`` ou o gradiente morfológico.
"""

import cv2 as cv

from core.mat_vector import channels
from core.operation import (
    INPUT_REF, BoolParam, ChoiceParam, FloatParam, MatRefParam, Operation, fmt, is_color, short_label,
)


class _TwoMats(Operation):
    def _mat(self, key, src, mats):
        ref = self[key]
        if ref == INPUT_REF:
            return src
        current = len(mats)  # índice do Mat que esta etapa vai gerar
        if not 0 <= ref < current:
            raise ValueError(f"Mat[{ref}] não existe antes desta etapa (use Mat[0]..Mat[{current - 1}]).")
        return mats[ref]

    @staticmethod
    def _var(ref) -> str:
        return "src" if ref == INPUT_REF else f"mats[{ref}]"

    @staticmethod
    def _match(a, b):
        """Iguala o número de canais de B ao de A (cinza ↔ BGR)."""
        if is_color(a) and not is_color(b):
            return cv.cvtColor(b, cv.COLOR_GRAY2BGR)
        if not is_color(a) and is_color(b):
            return cv.cvtColor(b, cv.COLOR_BGR2GRAY)
        return b

    def operands(self, src, mats):
        a = self._mat("a", src, mats)
        return a, self._match(a, self._mat("b", src, mats))

    def operand_code(self, src, mats) -> tuple[list[str], str, str]:
        """Linhas de preparo e nomes das variáveis A e B para o código exibido."""
        a_var, b_var = self._var(self["a"]), self._var(self["b"])
        try:
            a, b = self._mat("a", src, mats), self._mat("b", src, mats)
        except (ValueError, IndexError):
            return [], a_var, b_var
        if channels(a) == channels(b):
            return [], a_var, b_var
        code = "COLOR_GRAY2BGR" if is_color(a) else "COLOR_BGR2GRAY"
        return [f"b = cv.cvtColor({b_var}, cv.{code})  # iguala os canais de B aos de A"], a_var, "b"


ARITHMETIC = {
    "Soma (add)": "add",
    "Soma ponderada (addWeighted)": "addWeighted",
    "Subtração (subtract)": "subtract",
    "Multiplicação (multiply)": "multiply",
    "Divisão (divide)": "divide",
}


class Arithmetic(_TwoMats):
    name = "Aritmética entre Mats"
    function = "cv.add / subtract / multiply / divide"
    description = (
        "Combina dois Mats pixel a pixel, saturando o resultado em 0..255. A subtração "
        "destaca diferenças (ex.: imagem − erosão = contorno); a soma ponderada mistura "
        "duas imagens; multiplicação e divisão corrigem sombreamento."
    )
    params = (
        MatRefParam(key="a", label="Mat A", default=INPUT_REF),
        ChoiceParam(key="operacao", label="Operação", default="Subtração (subtract)", options=ARITHMETIC),
        MatRefParam(key="b", label="Mat B", default=0),
        FloatParam(key="alpha", label="Peso de A (ponderada)", default=0.5, minimum=0.0, maximum=1.0,
                   step=0.05),
        BoolParam(key="escalar", label="Escalar resultado", default=True,
                  help="Multiplicação: scale = 1/255 · Divisão: scale = 255 (evita saturar/zerar)"),
    )

    def _beta(self):
        return round(1.0 - self["alpha"], 4)

    def apply(self, src, mats):
        a, b = self.operands(src, mats)
        op = self.choice("operacao")
        if op == "add":
            return cv.add(a, b)
        if op == "addWeighted":
            return cv.addWeighted(a, self["alpha"], b, self._beta(), 0)
        if op == "subtract":
            return cv.subtract(a, b)
        if op == "multiply":
            return cv.multiply(a, b, scale=1 / 255 if self["escalar"] else 1)
        return cv.divide(a, b, scale=255 if self["escalar"] else 1)

    def title(self):
        return short_label(self["operacao"])

    def code(self, src, mats):
        lines, a, b = self.operand_code(src, mats)
        op = self.choice("operacao")
        if op == "addWeighted":
            call = f"cv.addWeighted({a}, {fmt(self['alpha'])}, {b}, {fmt(self._beta())}, 0)"
        elif op == "multiply":
            call = f"cv.multiply({a}, {b}, scale={'1 / 255' if self['escalar'] else '1'})"
        elif op == "divide":
            call = f"cv.divide({a}, {b}, scale={'255' if self['escalar'] else '1'})"
        else:
            call = f"cv.{op}({a}, {b})"
        return "\n".join(lines + [f"dst = {call}"])


LOGICAL = {
    "AND (bitwise_and)": "bitwise_and",
    "OR (bitwise_or)": "bitwise_or",
    "XOR (bitwise_xor)": "bitwise_xor",
    "NOT (bitwise_not, usa só A)": "bitwise_not",
}


class Logical(_TwoMats):
    name = "Lógica entre Mats"
    function = "cv.bitwise_and / or / xor / not"
    description = (
        "Operações lógicas bit a bit, muito usadas com imagens binárias: AND mantém só o "
        "que é branco nas duas (aplicar máscara), OR junta, XOR mostra onde diferem e NOT "
        "inverte."
    )
    params = (
        MatRefParam(key="a", label="Mat A", default=INPUT_REF),
        ChoiceParam(key="operacao", label="Operação", default="AND (bitwise_and)", options=LOGICAL),
        MatRefParam(key="b", label="Mat B", default=0),
    )

    def apply(self, src, mats):
        op = getattr(cv, self.choice("operacao"))
        if self.choice("operacao") == "bitwise_not":
            return op(self._mat("a", src, mats))
        return op(*self.operands(src, mats))

    def title(self):
        return f"Lógica {short_label(self['operacao'])}"

    def code(self, src, mats):
        op = self.choice("operacao")
        if op == "bitwise_not":
            return f"dst = cv.bitwise_not({self._var(self['a'])})"
        lines, a, b = self.operand_code(src, mats)
        return "\n".join(lines + [f"dst = cv.{op}({a}, {b})"])
