import cv2 as cv
import numpy as np

from nucleo.operacao import (
    Operacao, ParametroBooleano, ParametroEscolha, ParametroInteiro, ParametroReal,
    eh_colorida, para_cinza,
)

# Transformações pontuais (Aula 2): cada pixel de saída só depende do mesmo pixel de entrada.


class BrilhoContraste(Operacao):
    # REQUISITO: filtro de realce
    # g(x) = alfa*f(x) + beta. Não usei convertScaleAbs (do slide) porque ele tira o
    # valor absoluto: com brilho negativo o pixel escuro "voltaria" a ficar claro.
    nome = "Brilho e contraste"
    funcao = "cv.addWeighted"
    descricao = (
        "Aplica g(x) = α·f(x) + β: α (contraste) multiplica cada pixel e β (brilho) soma um "
        "valor, saturando em 0..255 como o convertTo do C++. O convertScaleAbs dos slides "
        "tira o valor absoluto, o que faria pixels escuros 'refletirem' com brilho negativo."
    )
    parametros = (
        ParametroReal(chave="alfa", rotulo="Contraste (α)", padrao=1.0, minimo=0.0, maximo=3.0, passo=0.05),
        ParametroInteiro(chave="beta", rotulo="Brilho (β)", padrao=0, minimo=-255, maximo=255),
    )

    def aplicar(self, src, mats):
        # truque: src com peso alfa + src com peso 0 + beta -> satura certinho em 0..255
        return cv.addWeighted(src, self["alfa"], src, 0, self["beta"])


class Negativo(Operacao):
    nome = "Negativo"
    funcao = "255 - src"
    descricao = (
        "Inverte a imagem: subtrai cada pixel da intensidade máxima do canal (255). "
        "Regiões claras ficam escuras e vice-versa."
    )

    def aplicar(self, src, mats):
        return 255 - src


class AlargamentoContraste(Operacao):
    # fórmula do slide: f(N) = (N - min1)(max2 - min2)/(max1 - min1) + min2
    nome = "Alargamento de contraste"
    funcao = "aritmética NumPy"
    descricao = (
        "Leva a faixa de interesse [min1, max1] para uma nova faixa [min2, max2]: "
        "f(N) = (N − min1)(max2 − min2) / (max1 − min1) + min2. Com 'automático', "
        "min1 e max1 são o menor e o maior valor da imagem (normalização)."
    )
    parametros = (
        ParametroBooleano(chave="automatico", rotulo="min1/max1 automáticos", padrao=True,
                          dica="Usa o menor e o maior valor presentes na imagem"),
        ParametroInteiro(chave="min1", rotulo="min1 (entrada)", padrao=0),
        ParametroInteiro(chave="max1", rotulo="max1 (entrada)", padrao=255),
        ParametroInteiro(chave="min2", rotulo="min2 (saída)", padrao=0),
        ParametroInteiro(chave="max2", rotulo="max2 (saída)", padrao=255),
    )

    def _faixa_entrada(self, src):
        if self["automatico"]:
            return int(src.min()), int(src.max())
        return self["min1"], self["max1"]

    def aplicar(self, src, mats):
        min1, max1 = self._faixa_entrada(src)
        if max1 <= min1:
            raise ValueError("max1 precisa ser maior que min1.")
        min2, max2 = self["min2"], self["max2"]
        self.info = f"Faixa de entrada usada: [{min1}, {max1}] → [{min2}, {max2}]"
        n = src.astype(np.float32)
        dst = (n - min1) * (max2 - min2) / (max1 - min1) + min2
        # o que estava fora da faixa de interesse fica preso em min2/max2
        return np.clip(dst, min(min2, max2), max(min2, max2)).astype(np.uint8)


class EqualizacaoHistograma(Operacao):
    # equalizeHist só aceita 1 canal -> ou converto pra cinza ou faço canal a canal
    nome = "Equalização de histograma"
    funcao = "cv.equalizeHist"
    mostrar_histograma = True  # mostra o histograma antes/depois no painel
    descricao = (
        "Redistribui os níveis de cinza de forma mais uniforme no histograma, aumentando "
        "o contraste geral. O equalizeHist trabalha com 1 canal: imagens coloridas são "
        "convertidas para cinza ou equalizadas canal a canal."
    )
    parametros = (
        ParametroEscolha(chave="modo", rotulo="Se a entrada for colorida", padrao="Converter para cinza",
                         opcoes={"Converter para cinza": "cinza",
                                 "Cada canal (split → equalizeHist → merge)": "split"}),
    )

    def aplicar(self, src, mats):
        if eh_colorida(src) and self.escolha("modo") == "split":
            return cv.merge([cv.equalizeHist(c) for c in cv.split(src)])
        return cv.equalizeHist(para_cinza(src))
