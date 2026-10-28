import cv2 as cv
import numpy as np

from nucleo.operacao import Operacao, ParametroEscolha, eh_colorida, rotulo_curto
from nucleo.vetor_mats import NOMES_CANAIS, num_canais

# texto do combobox -> (código do cvtColor, espaço de cor que sai)
CONVERSOES = {
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


class ConversaoCor(Operacao):
    # REQUISITO: conversão de cor -> cvtColor (Aula 1)
    nome = "Conversão de espaço de cor"
    funcao = "cv.cvtColor"
    descricao = (
        "O imread carrega a imagem em BGR. O cvtColor a converte para outro espaço de cor "
        "(GRAY, HSV, HLS, Lab, Luv, XYZ, YCrCb) ou de volta para BGR. Mats de 3 canais fora "
        "do BGR aparecem com 'cores falsas', exatamente como no cv.imshow."
    )
    parametros = (
        ParametroEscolha(chave="conversao", rotulo="Conversão", padrao="BGR → HSV", opcoes=CONVERSOES),
    )

    def aplicar(self, src, mats):
        conversao, _ = self.escolha("conversao")
        espera_cinza = conversao.startswith("COLOR_GRAY")
        # evita o erro feio do OpenCV quando o número de canais não bate
        if espera_cinza == eh_colorida(src):
            esperado = "1 canal" if espera_cinza else "3 canais"
            raise ValueError(f"Esta conversão espera um Mat de {esperado}; a entrada tem {num_canais(src)}.")
        return cv.cvtColor(src, getattr(cv, conversao))

    def espaco_saida(self, espaco_entrada, dst):
        return self.escolha("conversao")[1]

    def titulo(self):
        return rotulo_curto(self["conversao"])


class SepararCanal(Operacao):
    # split: pega um canal só (ex: o H depois de converter pra HSV)
    nome = "Separar canal (split)"
    funcao = "cv.split / cv.merge"
    descricao = (
        "Divide um Mat de 3 canais em 3 Mats de 1 canal (split) e mantém o escolhido. "
        "No modo '3 canais', o canal é juntado (merge) com zeros nos demais, mostrando "
        "sua contribuição na cor. Use depois de uma conversão para ver H, S, V etc."
    )
    parametros = (
        ParametroEscolha(chave="canal", rotulo="Canal", padrao="Canal 0",
                         opcoes={"Canal 0": 0, "Canal 1": 1, "Canal 2": 2}),
        ParametroEscolha(chave="modo", rotulo="Exibir como", padrao="1 canal (tons de cinza)",
                         opcoes={"1 canal (tons de cinza)": False, "3 canais (merge com zeros)": True}),
    )

    def aplicar(self, src, mats):
        if not eh_colorida(src):
            raise ValueError("A entrada já tem 1 canal; não há canais para separar.")
        c = self.escolha("canal")
        nomes = NOMES_CANAIS.get(self.espaco_entrada, ("c0", "c1", "c2"))
        self.info = f"Canal {c} de um Mat {self.espaco_entrada} = {nomes[c]}"
        canais = cv.split(src)
        if self.escolha("modo"):
            # merge com zeros nos outros canais pra ver a "cor" daquele canal
            zeros = np.zeros_like(canais[c])
            return cv.merge([canais[i] if i == c else zeros for i in range(3)])
        return canais[c]

    def titulo(self):
        return f"Split · canal {self.escolha('canal')}"


# fórmulas do slide "Conversão RGB - Tons de Cinza" (pesos de R, G, B)
FORMULAS_CINZA = {
    "Média: (R + G + B) / 3": None,
    "Clássica: 0,3R + 0,59G + 0,11B": (0.3, 0.59, 0.11),
    "Imagens escuras: 0,23R + 0,65G + 0,12B": (0.23, 0.65, 0.12),
}


class CinzaPorFormula(Operacao):
    # cinza "na mão", pixel a pixel, com as fórmulas da Aula 1
    nome = "Tons de cinza por fórmula"
    funcao = "cv.split + aritmética"
    descricao = (
        "Calcula o cinza pixel a pixel a partir dos canais R, G e B. A média simples "
        "costuma escurecer a imagem, pois o olho é mais sensível ao verde e menos ao azul; "
        "as fórmulas ponderadas compensam isso."
    )
    parametros = (
        ParametroEscolha(chave="formula", rotulo="Fórmula", padrao="Clássica: 0,3R + 0,59G + 0,11B",
                         opcoes=FORMULAS_CINZA),
    )

    def aplicar(self, src, mats):
        if not eh_colorida(src):
            raise ValueError("A fórmula precisa de um Mat BGR de 3 canais.")
        # float32 pra soma não estourar o limite de 255 do uint8
        b, g, r = cv.split(src.astype(np.float32))
        pesos = self.escolha("formula")
        if pesos is None:
            cinza = (r + g + b) / 3
        else:
            pr, pg, pb = pesos
            cinza = pr * r + pg * g + pb * b
        return np.clip(cinza, 0, 255).astype(np.uint8)
