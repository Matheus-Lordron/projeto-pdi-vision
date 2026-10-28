import cv2 as cv

from nucleo.operacao import (
    Operacao, ParametroEscolha, ParametroInteiro, eh_colorida, para_cinza, rotulo_curto,
)
from nucleo.vetor_mats import NOMES_CANAIS

# REQUISITO: binarização / limiarização (Aulas 2 e 3)

TIPOS_LIMIAR = {
    "BINARY: > limiar → máximo, senão 0": "THRESH_BINARY",
    "BINARY_INV: > limiar → 0, senão máximo": "THRESH_BINARY_INV",
    "TRUNC: > limiar → limiar": "THRESH_TRUNC",
    "TOZERO: > limiar mantém, senão 0": "THRESH_TOZERO",
    "TOZERO_INV: > limiar → 0, senão mantém": "THRESH_TOZERO_INV",
}

METODOS_AUTOMATICOS = {
    "Manual (usa o limiar acima)": None,
    "Otsu (automático)": "THRESH_OTSU",
    "Triângulo (automático)": "THRESH_TRIANGLE",
}


class LimiarGlobal(Operacao):
    # Otsu/Triângulo: soma a flag no tipo e passa limiar 0, como no slide.
    # O threshold devolve o limiar que ele usou -> mostro na tela
    nome = "Limiarização global"
    funcao = "cv.threshold"
    descricao = (
        "Compara cada pixel com um único limiar para a imagem toda. Com Otsu ou Triângulo o "
        "limiar é calculado automaticamente a partir do histograma (o limiar informado é "
        "ignorado) e o valor encontrado aparece abaixo."
    )
    parametros = (
        ParametroInteiro(chave="limiar", rotulo="Limiar", padrao=127, minimo=0, maximo=255),
        ParametroInteiro(chave="maximo", rotulo="Valor máximo", padrao=255, minimo=0, maximo=255),
        ParametroEscolha(chave="tipo", rotulo="Tipo", padrao="BINARY: > limiar → máximo, senão 0",
                         opcoes=TIPOS_LIMIAR),
        ParametroEscolha(chave="metodo", rotulo="Cálculo do limiar", padrao="Manual (usa o limiar acima)",
                         opcoes=METODOS_AUTOMATICOS),
    )

    def aplicar(self, src, mats):
        automatico = self.escolha("metodo")
        flags = getattr(cv, self.escolha("tipo")) + (getattr(cv, automatico) if automatico else 0)
        limiar, dst = cv.threshold(para_cinza(src), 0 if automatico else self["limiar"], self["maximo"], flags)
        self.info = f"Limiar utilizado: {limiar:g}"
        return dst

    def titulo(self):
        if self.escolha("metodo"):
            return f"Limiar · {rotulo_curto(self['metodo'])}"
        return f"Limiar · {self['limiar']}"


class LimiarAdaptativo(Operacao):
    # limiar diferente pra cada pixel (média da vizinhança - C). Bom com iluminação desigual
    nome = "Limiarização adaptativa"
    funcao = "cv.adaptiveThreshold"
    descricao = (
        "Em vez de um limiar único, calcula um limiar para cada pixel a partir da sua "
        "vizinhança (média ou média gaussiana) menos a constante C. Funciona bem com "
        "iluminação desigual."
    )
    parametros = (
        ParametroEscolha(chave="metodo", rotulo="Método", padrao="Média (MEAN_C)",
                         opcoes={"Média (MEAN_C)": "ADAPTIVE_THRESH_MEAN_C",
                                 "Gaussiano (GAUSSIAN_C)": "ADAPTIVE_THRESH_GAUSSIAN_C"}),
        ParametroEscolha(chave="tipo", rotulo="Tipo", padrao="BINARY",
                         opcoes={"BINARY": "THRESH_BINARY", "BINARY_INV": "THRESH_BINARY_INV"}),
        ParametroInteiro(chave="bloco", rotulo="Tamanho do bloco", padrao=11, minimo=3, maximo=99, impar=True),
        ParametroInteiro(chave="c", rotulo="Constante C", padrao=2, minimo=-50, maximo=50),
        ParametroInteiro(chave="maximo", rotulo="Valor máximo", padrao=255, minimo=0, maximo=255),
    )

    def aplicar(self, src, mats):
        return cv.adaptiveThreshold(para_cinza(src), self["maximo"], getattr(cv, self.escolha("metodo")),
                                    getattr(cv, self.escolha("tipo")), self["bloco"], self["c"])


class FaixaValores(Operacao):
    # inRange: dentro da faixa = 255, fora = 0.
    # Em 3 canais dá pra segmentar cor no HSV (ex: verde da folha)
    nome = "Faixa de valores (inRange)"
    funcao = "cv.inRange"
    descricao = (
        "Pixels dentro da faixa [mínimo, máximo] viram 255 e o resto 0 (limiarização com "
        "dois limiares). Em 3 canais, cada canal tem sua faixa: após converter para HSV dá "
        "para segmentar uma cor, como o verde de uma folha."
    )
    parametros = (
        ParametroEscolha(chave="modo", rotulo="Aplicar em", padrao="1 canal (tons de cinza)",
                         opcoes={"1 canal (tons de cinza)": 1, "3 canais (ex.: HSV ou BGR)": 3}),
        ParametroInteiro(chave="min0", rotulo="Canal 0 — mínimo", padrao=0),
        ParametroInteiro(chave="max0", rotulo="Canal 0 — máximo", padrao=127),
        ParametroInteiro(chave="min1", rotulo="Canal 1 — mínimo", padrao=0),
        ParametroInteiro(chave="max1", rotulo="Canal 1 — máximo", padrao=255),
        ParametroInteiro(chave="min2", rotulo="Canal 2 — mínimo", padrao=0),
        ParametroInteiro(chave="max2", rotulo="Canal 2 — máximo", padrao=255),
    )

    def _limites(self):
        return (self["min0"], self["min1"], self["min2"]), (self["max0"], self["max1"], self["max2"])

    def aplicar(self, src, mats):
        if self.escolha("modo") == 1:
            return cv.inRange(para_cinza(src), self["min0"], self["max0"])
        if not eh_colorida(src):
            raise ValueError("O modo '3 canais' precisa de um Mat de 3 canais.")
        baixo, alto = self._limites()
        nomes = NOMES_CANAIS.get(self.espaco_entrada, ("c0", "c1", "c2"))
        self.info = "Faixas: " + ", ".join(f"{n} {b}..{a}" for n, b, a in zip(nomes, baixo, alto))
        return cv.inRange(src, baixo, alto)
