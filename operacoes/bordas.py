import cv2 as cv
import numpy as np

from nucleo.operacao import (
    Operacao, ParametroBooleano, ParametroEscolha, ParametroInteiro,
    para_cinza, texto_kernel,
)

# REQUISITO: detector de borda (passa-alta, Aula 2)
# igual nos exemplos da aula, converto pra cinza antes de detectar borda


def _k(linhas):
    return np.array(linhas, dtype=np.float32)


class _GradienteDuplo(Operacao):
    # base pros operadores com 2 máscaras (Gx e Gy): Sobel, Prewitt e Roberts.
    # Mesmo esquema do slide do Sobel:
    #   CV_64F (guarda negativo) -> convertScaleAbs -> addWeighted(|Gx|, 0.5, |Gy|, 0.5)

    KX = None
    KY = None
    DIRECOES = {}

    def _gradientes(self, cinza):
        raise NotImplementedError

    def aplicar(self, src, mats):
        cinza = para_cinza(src)
        grad_x, grad_y = self._gradientes(cinza)
        direcao = self.escolha("direcao")
        abs_grad_x = cv.convertScaleAbs(grad_x)
        abs_grad_y = cv.convertScaleAbs(grad_y)
        if direcao == "x":
            return abs_grad_x
        if direcao == "y":
            return abs_grad_y
        return cv.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)


_DIRECOES_EIXOS = {
    "Gx e Gy (magnitude)": "xy",
    "Somente Gx (mudanças verticais)": "x",
    "Somente Gy (mudanças horizontais)": "y",
}


class Sobel(_GradienteDuplo):
    nome = "Sobel"
    funcao = "cv.Sobel"
    descricao = (
        "Calcula o gradiente (1ª derivada) nas direções x e y. Os resultados em CV_64F "
        "guardam valores negativos; o convertScaleAbs tira o valor absoluto e volta para "
        "8 bits; por fim, addWeighted junta |Gx| e |Gy|."
    )
    DIRECOES = _DIRECOES_EIXOS
    parametros = (
        ParametroInteiro(chave="tamanho", rotulo="Tamanho do kernel", padrao=3, minimo=1, maximo=7, impar=True),
        ParametroEscolha(chave="direcao", rotulo="Gradiente", padrao="Gx e Gy (magnitude)", opcoes=DIRECOES),
    )

    def _gradientes(self, cinza):
        k = self["tamanho"]
        grad_x = cv.Sobel(cinza, cv.CV_64F, 1, 0, ksize=k, borderType=cv.BORDER_REPLICATE)
        grad_y = cv.Sobel(cinza, cv.CV_64F, 0, 1, ksize=k, borderType=cv.BORDER_REPLICATE)
        return grad_x, grad_y


class Prewitt(_GradienteDuplo):
    # mesma ideia do Sobel, mas com as máscaras de Prewitt via filter2D
    nome = "Prewitt"
    funcao = "cv.filter2D"
    descricao = (
        "Gradiente com as máscaras de Prewitt (pesos iguais em cada coluna/linha), aplicadas "
        "por convolução com filter2D. Semelhante ao Sobel, porém sem dar peso maior ao "
        "pixel central."
    )
    KX = _k([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
    KY = _k([[1, 1, 1], [0, 0, 0], [-1, -1, -1]])
    DIRECOES = {
        "Vertical e horizontal (magnitude)": "xy",
        "Somente vertical": "x",
        "Somente horizontal": "y",
    }
    parametros = (
        ParametroEscolha(chave="direcao", rotulo="Máscara", padrao="Vertical e horizontal (magnitude)",
                         opcoes=DIRECOES),
    )

    def _gradientes(self, cinza):
        return cv.filter2D(cinza, cv.CV_64F, self.KX), cv.filter2D(cinza, cv.CV_64F, self.KY)


class Roberts(Prewitt):
    # só troca as máscaras: 2x2 nas diagonais
    nome = "Roberts"
    descricao = (
        "Operador de Roberts: duas máscaras 2×2 que calculam diferenças nas diagonais. "
        "Simples e rápido, porém mais sensível a ruído."
    )
    KX = _k([[1, 0], [0, -1]])
    KY = _k([[0, 1], [-1, 0]])
    DIRECOES = {
        "As duas diagonais (magnitude)": "xy",
        "Somente diagonal [1 0; 0 -1]": "x",
        "Somente diagonal [0 1; -1 0]": "y",
    }
    parametros = (
        ParametroEscolha(chave="direcao", rotulo="Máscara", padrao="As duas diagonais (magnitude)",
                         opcoes=DIRECOES),
    )


class Laplace(Operacao):
    # 2ª derivada. Deixei opção do CV_8U (como no slide) pra mostrar que ele corta os negativos
    nome = "Laplace"
    funcao = "cv.Laplacian"
    descricao = (
        "Usa a 2ª derivada e detecta bordas em todas as direções de uma vez. Com CV_8U "
        "(como no slide) as respostas negativas são cortadas para 0; com CV_64F elas são "
        "mantidas e o convertScaleAbs as transforma em valor absoluto."
    )
    parametros = (
        ParametroInteiro(chave="tamanho", rotulo="Tamanho do kernel", padrao=3, minimo=1, maximo=7, impar=True),
        ParametroEscolha(chave="profundidade", rotulo="Profundidade (ddepth)", padrao="CV_64F (mantém negativos)",
                         opcoes={"CV_64F (mantém negativos)": "CV_64F", "CV_8U (como no slide)": "CV_8U"}),
    )

    def aplicar(self, src, mats):
        dst = cv.Laplacian(para_cinza(src), getattr(cv, self.escolha("profundidade")), ksize=self["tamanho"],
                           borderType=cv.BORDER_REPLICATE)
        return cv.convertScaleAbs(dst)


class Canny(Operacao):
    # 2 limiares: acima do superior é borda, abaixo do inferior descarta,
    # no meio só é borda se estiver ligado a um pixel forte
    nome = "Canny"
    funcao = "cv.Canny"
    descricao = (
        "Um dos melhores detectores: suaviza com Gaussiano, calcula o gradiente, afina as "
        "bordas e usa 2 limiares. Acima do superior é borda; abaixo do inferior é descartado; "
        "entre os dois só é borda se estiver ligado a um pixel forte."
    )
    parametros = (
        ParametroInteiro(chave="limiar1", rotulo="Limiar inferior", padrao=50, minimo=0, maximo=500),
        ParametroInteiro(chave="limiar2", rotulo="Limiar superior", padrao=150, minimo=0, maximo=500),
        ParametroInteiro(chave="abertura", rotulo="Kernel do Sobel", padrao=3, minimo=3, maximo=7, impar=True),
        ParametroBooleano(chave="l2", rotulo="L2gradient", padrao=False,
                          dica="Usa √(Gx² + Gy²) em vez de |Gx| + |Gy| para a força do gradiente"),
    )

    def aplicar(self, src, mats):
        return cv.Canny(para_cinza(src), self["limiar1"], self["limiar2"], apertureSize=self["abertura"],
                        L2gradient=self["l2"])


# máscaras dos slides "Filtros passa alta" (direcionais e não direcionais) e "Line Masks"
MASCARAS_PASSA_ALTA = {
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


class MascaraPassaAlta(Operacao):
    # convolução com filter2D e ddepth = -1, igual o exemplo do slide
    nome = "Máscara passa-alta (filter2D)"
    funcao = "cv.filter2D"
    descricao = (
        "Convolução com as máscaras 3×3 vistas em aula: não direcionais (realçam bordas em "
        "qualquer direção), direcionais (realçam uma direção) e line masks (detectam linhas). "
        "Com ddepth = -1 a saída é 8 bits e valores negativos viram 0."
    )
    parametros = (
        ParametroEscolha(chave="mascara", rotulo="Máscara", padrao="Não direcional — Alta",
                         opcoes=MASCARAS_PASSA_ALTA),
    )

    def aplicar(self, src, mats):
        kernel = self.escolha("mascara")
        self.info = "Máscara:\n" + texto_kernel(kernel)
        return cv.filter2D(para_cinza(src), -1, kernel)


# 8 máscaras de Kirsch, uma para cada direção
MASCARAS_KIRSCH = [
    _k([[5, 5, 5], [-3, 0, -3], [-3, -3, -3]]),
    _k([[-3, 5, 5], [-3, 0, 5], [-3, -3, -3]]),
    _k([[-3, -3, 5], [-3, 0, 5], [-3, -3, 5]]),
    _k([[-3, -3, -3], [-3, 0, 5], [-3, 5, 5]]),
    _k([[-3, -3, -3], [-3, 0, -3], [5, 5, 5]]),
    _k([[-3, -3, -3], [5, 0, -3], [5, 5, -3]]),
    _k([[5, -3, -3], [5, 0, -3], [5, -3, -3]]),
    _k([[5, 5, -3], [5, 0, -3], [-3, -3, -3]]),
]


class Kirsch(Operacao):
    # aplica as 8 máscaras e fica com a maior resposta em cada pixel
    nome = "Kirsch"
    funcao = "cv.filter2D"
    descricao = (
        "Aplica as 8 máscaras de Kirsch (uma para cada direção) e, em cada pixel, fica com "
        "a maior resposta. Detecta bordas em qualquer direção."
    )

    def aplicar(self, src, mats):
        cinza = para_cinza(src)
        respostas = [cv.filter2D(cinza, cv.CV_32F, k) for k in MASCARAS_KIRSCH]
        return cv.convertScaleAbs(np.max(respostas, axis=0))
