import cv2 as cv

from nucleo.operacao import (
    ENTRADA_ANTERIOR, Operacao, ParametroBooleano, ParametroEscolha, ParametroMat, ParametroReal,
    eh_colorida, rotulo_curto,
)

# Operações entre 2 Mats do vetor (Aula 2). A e B podem ser qualquer Mat já calculado,
# então dá pra fazer o exemplo da aula: diferencaErosao = image - erosao


class _DoisMats(Operacao):

    def _mat(self, chave, src, mats):
        ref = self[chave]
        if ref == ENTRADA_ANTERIOR:
            return src
        atual = len(mats)  # índice do Mat que essa etapa vai gerar
        if not 0 <= ref < atual:
            raise ValueError(f"Mat[{ref}] não existe antes desta etapa (use Mat[0]..Mat[{atual - 1}]).")
        return mats[ref]

    @staticmethod
    def _igualar_canais(a, b):
        # cinza com colorido não opera, então converto o B pro mesmo nº de canais do A
        if eh_colorida(a) and not eh_colorida(b):
            return cv.cvtColor(b, cv.COLOR_GRAY2BGR)
        if not eh_colorida(a) and eh_colorida(b):
            return cv.cvtColor(b, cv.COLOR_BGR2GRAY)
        return b

    def operandos(self, src, mats):
        a = self._mat("a", src, mats)
        return a, self._igualar_canais(a, self._mat("b", src, mats))


ARITMETICAS = {
    "Soma (add)": "add",
    "Soma ponderada (addWeighted)": "addWeighted",
    "Subtração (subtract)": "subtract",
    "Multiplicação (multiply)": "multiply",
    "Divisão (divide)": "divide",
}


class Aritmetica(_DoisMats):
    # cv.add / subtract saturam em 0..255 (não dá overflow como no numpy puro)
    nome = "Aritmética entre Mats"
    funcao = "cv.add / subtract / multiply / divide"
    descricao = (
        "Combina dois Mats pixel a pixel, saturando o resultado em 0..255. A subtração "
        "destaca diferenças (ex.: imagem − erosão = contorno); a soma ponderada mistura "
        "duas imagens; multiplicação e divisão corrigem sombreamento."
    )
    parametros = (
        ParametroMat(chave="a", rotulo="Mat A", padrao=ENTRADA_ANTERIOR),
        ParametroEscolha(chave="operacao", rotulo="Operação", padrao="Subtração (subtract)", opcoes=ARITMETICAS),
        ParametroMat(chave="b", rotulo="Mat B", padrao=0),
        ParametroReal(chave="alfa", rotulo="Peso de A (ponderada)", padrao=0.5, minimo=0.0, maximo=1.0, passo=0.05),
        ParametroBooleano(chave="escalar", rotulo="Escalar resultado", padrao=True,
                          dica="Multiplicação: scale = 1/255 · Divisão: scale = 255 (evita saturar/zerar)"),
    )

    def _beta(self):
        return round(1.0 - self["alfa"], 4)

    def aplicar(self, src, mats):
        a, b = self.operandos(src, mats)
        op = self.escolha("operacao")
        if op == "add":
            return cv.add(a, b)
        if op == "addWeighted":
            return cv.addWeighted(a, self["alfa"], b, self._beta(), 0)
        if op == "subtract":
            return cv.subtract(a, b)
        # sem a escala a multiplicação estoura tudo pra 255 e a divisão zera quase tudo
        if op == "multiply":
            return cv.multiply(a, b, scale=1 / 255 if self["escalar"] else 1)
        return cv.divide(a, b, scale=255 if self["escalar"] else 1)

    def titulo(self):
        return rotulo_curto(self["operacao"])


LOGICAS = {
    "AND (bitwise_and)": "bitwise_and",
    "OR (bitwise_or)": "bitwise_or",
    "XOR (bitwise_xor)": "bitwise_xor",
    "NOT (bitwise_not, usa só A)": "bitwise_not",
}


class Logica(_DoisMats):
    # AND serve pra aplicar máscara binária na imagem
    nome = "Lógica entre Mats"
    funcao = "cv.bitwise_and / or / xor / not"
    descricao = (
        "Operações lógicas bit a bit, muito usadas com imagens binárias: AND mantém só o "
        "que é branco nas duas (aplicar máscara), OR junta, XOR mostra onde diferem e NOT "
        "inverte."
    )
    parametros = (
        ParametroMat(chave="a", rotulo="Mat A", padrao=ENTRADA_ANTERIOR),
        ParametroEscolha(chave="operacao", rotulo="Operação", padrao="AND (bitwise_and)", opcoes=LOGICAS),
        ParametroMat(chave="b", rotulo="Mat B", padrao=0),
    )

    def aplicar(self, src, mats):
        funcao = getattr(cv, self.escolha("operacao"))
        if self.escolha("operacao") == "bitwise_not":
            return funcao(self._mat("a", src, mats))
        return funcao(*self.operandos(src, mats))

    def titulo(self):
        return f"Lógica {rotulo_curto(self['operacao'])}"
