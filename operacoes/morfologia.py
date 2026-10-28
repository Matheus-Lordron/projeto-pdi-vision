import cv2 as cv

from nucleo.operacao import Operacao, ParametroEscolha, ParametroInteiro, rotulo_curto, texto_kernel

# REQUISITO: morfologia matemática (Aula 3)
# todas usam um elemento estruturante (EE) do getStructuringElement

FORMAS = {
    "Retângulo (MORPH_RECT)": "MORPH_RECT",
    "Elipse (MORPH_ELLIPSE)": "MORPH_ELLIPSE",
    "Cruz (MORPH_CROSS)": "MORPH_CROSS",
}

PARAMETROS_ELEMENTO = (
    ParametroEscolha(chave="forma", rotulo="Elemento estruturante", padrao="Retângulo (MORPH_RECT)", opcoes=FORMAS),
    ParametroInteiro(chave="tamanho", rotulo="Tamanho do EE", padrao=3, minimo=1, maximo=31, impar=True),
    ParametroInteiro(chave="iteracoes", rotulo="Iterações", padrao=1, minimo=1, maximo=20),
)


class _Morfologia(Operacao):
    # parte comum: cria o EE e mostra a matriz dele na tela

    def elemento(self):
        k = self["tamanho"]
        return cv.getStructuringElement(getattr(cv, self.escolha("forma")), (k, k))

    def aplicar(self, src, mats):
        elemento = self.elemento()
        self.info = "Elemento estruturante:\n" + texto_kernel(elemento)
        return self.transformar(src, elemento)

    def transformar(self, src, elemento):
        raise NotImplementedError


class Erosao(_Morfologia):
    # escuro cresce sobre o claro: some com detalhe branco menor que o EE
    nome = "Erosão"
    funcao = "cv.erode"
    descricao = (
        "A região escura cresce sobre a clara: elimina picos positivos (detalhes claros) "
        "mais finos que o elemento estruturante. Em imagens binárias, afina os objetos "
        "brancos, separa objetos encostados e remove ruídos pequenos."
    )
    parametros = PARAMETROS_ELEMENTO

    def transformar(self, src, elemento):
        return cv.erode(src, elemento, iterations=self["iteracoes"])


class Dilatacao(_Morfologia):
    # claro cresce sobre o escuro: fecha buraco preto e "engorda" o objeto
    nome = "Dilatação"
    funcao = "cv.dilate"
    descricao = (
        "A região clara cresce sobre a escura: elimina picos negativos (buracos e falhas "
        "escuras) menores que o elemento estruturante e 'engorda' os objetos claros."
    )
    parametros = PARAMETROS_ELEMENTO

    def transformar(self, src, elemento):
        return cv.dilate(src, elemento, iterations=self["iteracoes"])


OPERACOES_MORFOLOGICAS = {
    "Abertura (erosão → dilatação)": "MORPH_OPEN",
    "Fechamento (dilatação → erosão)": "MORPH_CLOSE",
    "Gradiente (dilatação − erosão)": "MORPH_GRADIENT",
    "Top-hat (original − abertura)": "MORPH_TOPHAT",
    "Black-hat (fechamento − original)": "MORPH_BLACKHAT",
}


class MorfologiaAvancada(_Morfologia):
    # morphologyEx = combinações de erosão e dilatação
    nome = "Abertura, fechamento, gradiente…"
    funcao = "cv.morphologyEx"
    descricao = (
        "Combinações de erosão e dilatação. Abertura remove ruídos e suaviza contornos; "
        "fechamento preenche buracos e fendas; gradiente realça as bordas; top-hat destaca "
        "picos (detalhes claros) e black-hat destaca vales (detalhes escuros)."
    )
    parametros = (
        ParametroEscolha(chave="operacao", rotulo="Operação", padrao="Abertura (erosão → dilatação)",
                         opcoes=OPERACOES_MORFOLOGICAS),
    ) + PARAMETROS_ELEMENTO

    def transformar(self, src, elemento):
        return cv.morphologyEx(src, getattr(cv, self.escolha("operacao")), elemento,
                               iterations=self["iteracoes"])

    def titulo(self):
        return rotulo_curto(self["operacao"])
