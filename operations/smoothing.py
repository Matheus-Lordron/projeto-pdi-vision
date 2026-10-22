"""Suavização / filtros passa-baixa (Aula 2): transformações locais por convolução."""

import cv2 as cv

from core.operation import FloatParam, IntParam, Operation, fmt


class MeanBlur(Operation):
    name = "Média (blur)"
    function = "cv.blur"
    description = (
        "Substitui cada pixel pela média da vizinhança k×k (máscara com todos os pesos 1/k²). "
        "Reduz ruído; quanto maior a máscara, maior o borramento."
    )
    params = (IntParam(key="ksize", label="Tamanho do kernel", default=5, minimum=1, maximum=51),)

    def apply(self, src, mats):
        k = self["ksize"]
        return cv.blur(src, (k, k))

    def code(self, src, mats):
        k = self["ksize"]
        return f"dst = cv.blur(src, ({k}, {k}))"


class GaussianBlur(Operation):
    name = "Gaussiano"
    function = "cv.GaussianBlur"
    description = (
        "Média ponderada em que o pixel central tem o maior peso e os pesos diminuem "
        "gradativamente (curva gaussiana). Borra preservando melhor a estrutura que a média. "
        "σ = 0 faz o OpenCV calcular o desvio padrão a partir do tamanho do kernel."
    )
    params = (
        IntParam(key="ksize", label="Tamanho do kernel", default=5, minimum=1, maximum=51, odd=True),
        FloatParam(key="sigma", label="σ (desvio padrão)", default=0.0, minimum=0.0, maximum=20.0,
                   step=0.5, decimals=1),
    )

    def apply(self, src, mats):
        k = self["ksize"]
        return cv.GaussianBlur(src, (k, k), self["sigma"])

    def code(self, src, mats):
        k = self["ksize"]
        return f"dst = cv.GaussianBlur(src, ({k}, {k}), {fmt(self['sigma'])})"


class MedianBlur(Operation):
    name = "Mediana"
    function = "cv.medianBlur"
    description = (
        "Ordena os vizinhos do pixel e pega o elemento do meio. Ótimo para ruído impulsivo "
        "(sal e pimenta), pois descarta valores extremos em vez de espalhá-los."
    )
    params = (IntParam(key="ksize", label="Tamanho do kernel", default=5, minimum=1, maximum=31, odd=True),)

    def apply(self, src, mats):
        return cv.medianBlur(src, self["ksize"])

    def code(self, src, mats):
        return f"dst = cv.medianBlur(src, {self['ksize']})"


class BilateralFilter(Operation):
    name = "Bilateral"
    function = "cv.bilateralFilter"
    description = (
        "Borra preservando as bordas: só mistura vizinhos próximos no espaço (σ espaço) "
        "e com cores parecidas (σ cor). Sigmas pequenos (< 10) têm pouco efeito; grandes "
        "(> 150) dão um efeito de 'cartoon'."
    )
    params = (
        IntParam(key="d", label="Diâmetro (d)", default=9, minimum=1, maximum=25),
        IntParam(key="sigma_color", label="σ cor", default=75, minimum=0, maximum=250),
        IntParam(key="sigma_space", label="σ espaço", default=75, minimum=0, maximum=250),
    )

    def apply(self, src, mats):
        return cv.bilateralFilter(src, self["d"], self["sigma_color"], self["sigma_space"])

    def code(self, src, mats):
        return f"dst = cv.bilateralFilter(src, {self['d']}, {self['sigma_color']}, {self['sigma_space']})"
