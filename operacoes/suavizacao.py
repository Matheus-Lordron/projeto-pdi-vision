import cv2 as cv

from nucleo.operacao import Operacao, ParametroInteiro, ParametroReal

# REQUISITO: filtro de suavização (passa-baixa, Aula 2)
# todos trabalham por vizinhança (convolução), em cinza ou colorido


class FiltroMedia(Operacao):
    nome = "Média (blur)"
    funcao = "cv.blur"
    descricao = (
        "Substitui cada pixel pela média da vizinhança k×k (máscara com todos os pesos 1/k²). "
        "Reduz ruído; quanto maior a máscara, maior o borramento."
    )
    parametros = (ParametroInteiro(chave="tamanho", rotulo="Tamanho do kernel", padrao=5, minimo=1, maximo=51),)

    def aplicar(self, src, mats):
        k = self["tamanho"]
        return cv.blur(src, (k, k))


class FiltroGaussiano(Operacao):
    # sigma = 0 -> o OpenCV calcula o sigma pelo tamanho do kernel
    nome = "Gaussiano"
    funcao = "cv.GaussianBlur"
    descricao = (
        "Média ponderada em que o pixel central tem o maior peso e os pesos diminuem "
        "gradativamente (curva gaussiana). Borra preservando melhor a estrutura que a média. "
        "σ = 0 faz o OpenCV calcular o desvio padrão a partir do tamanho do kernel."
    )
    parametros = (
        ParametroInteiro(chave="tamanho", rotulo="Tamanho do kernel", padrao=5, minimo=1, maximo=51, impar=True),
        ParametroReal(chave="sigma", rotulo="σ (desvio padrão)", padrao=0.0, minimo=0.0, maximo=20.0,
                      passo=0.5, casas=1),
    )

    def aplicar(self, src, mats):
        k = self["tamanho"]
        return cv.GaussianBlur(src, (k, k), self["sigma"])


class FiltroMediana(Operacao):
    # bom pra ruído sal e pimenta
    nome = "Mediana"
    funcao = "cv.medianBlur"
    descricao = (
        "Ordena os vizinhos do pixel e pega o elemento do meio. Ótimo para ruído impulsivo "
        "(sal e pimenta), pois descarta valores extremos em vez de espalhá-los."
    )
    parametros = (ParametroInteiro(chave="tamanho", rotulo="Tamanho do kernel", padrao=5, minimo=1, maximo=31, impar=True),)

    def aplicar(self, src, mats):
        return cv.medianBlur(src, self["tamanho"])


class FiltroBilateral(Operacao):
    # borra mas preserva borda; sigma alto dá efeito "cartoon"
    nome = "Bilateral"
    funcao = "cv.bilateralFilter"
    descricao = (
        "Borra preservando as bordas: só mistura vizinhos próximos no espaço (σ espaço) "
        "e com cores parecidas (σ cor). Sigmas pequenos (< 10) têm pouco efeito; grandes "
        "(> 150) dão um efeito de 'cartoon'."
    )
    parametros = (
        ParametroInteiro(chave="diametro", rotulo="Diâmetro (d)", padrao=9, minimo=1, maximo=25),
        ParametroInteiro(chave="sigma_cor", rotulo="σ cor", padrao=75, minimo=0, maximo=250),
        ParametroInteiro(chave="sigma_espaco", rotulo="σ espaço", padrao=75, minimo=0, maximo=250),
    )

    def aplicar(self, src, mats):
        return cv.bilateralFilter(src, self["diametro"], self["sigma_cor"], self["sigma_espaco"])
