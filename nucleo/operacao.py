from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

import cv2 as cv

# Cada operação só declara a lista de parâmetros; a interface lê essa lista
# e cria sozinha o slider / combobox / checkbox certo.


@dataclass(kw_only=True)
class Parametro:
    chave: str
    rotulo: str
    padrao: Any
    dica: str = ""

    def ajustar(self, valor):
        return valor


@dataclass(kw_only=True)
class ParametroInteiro(Parametro):
    minimo: int = 0
    maximo: int = 255
    passo: int = 1
    impar: bool = False  # tamanho de kernel no OpenCV quase sempre precisa ser ímpar

    def ajustar(self, valor):
        valor = int(min(max(int(valor), self.minimo), self.maximo))
        if self.impar and valor % 2 == 0:
            valor = valor + 1 if valor < self.maximo else valor - 1
        return valor


@dataclass(kw_only=True)
class ParametroReal(Parametro):
    minimo: float = 0.0
    maximo: float = 1.0
    passo: float = 0.1
    casas: int = 2

    def ajustar(self, valor):
        return round(min(max(float(valor), self.minimo), self.maximo), self.casas)


@dataclass(kw_only=True)
class ParametroEscolha(Parametro):
    opcoes: dict  # texto que aparece na tela -> valor usado no código

    def ajustar(self, valor):
        return valor if valor in self.opcoes else self.padrao


@dataclass(kw_only=True)
class ParametroBooleano(Parametro):
    def ajustar(self, valor):
        return bool(valor)


ENTRADA_ANTERIOR = -1  # -1 = usa o Mat anterior (mats[i-1])


@dataclass(kw_only=True)
class ParametroMat(Parametro):
    # escolhe um Mat que já existe no vetor (ex: subtrair mats[0] do atual)
    def ajustar(self, valor):
        return int(valor)


# ---------------- funções de apoio usadas pelas operações ----------------

def eh_colorida(mat):
    return mat.ndim == 3 and mat.shape[2] >= 3


def para_cinza(mat):
    # limiar, Canny, Sobel... trabalham em cinza, igual nos exemplos da aula
    return cv.cvtColor(mat, cv.COLOR_BGR2GRAY) if eh_colorida(mat) else mat


def texto_kernel(kernel):
    # mostra a matriz (máscara / elemento estruturante) no painel
    linhas = ["[" + " ".join(f"{v:>3g}" for v in linha) + " ]" for linha in kernel]
    return "\n".join(linhas)


def rotulo_curto(opcao):
    # 'Abertura (erosão → dilatação)' -> 'Abertura'
    return opcao.split(" (")[0]


class Operacao(ABC):
    # classe base: toda operação recebe um Mat e devolve um Mat novo

    nome: ClassVar[str] = ""
    descricao: ClassVar[str] = ""
    funcao: ClassVar[str] = ""  # função principal do OpenCV (só pra mostrar na tela)
    parametros: ClassVar[tuple] = ()
    mostrar_histograma: ClassVar[bool] = False  # painel mostra histograma de entrada e saída

    def __init__(self):
        self.valores = {p.chave: p.padrao for p in self.parametros}
        self.ativa = True
        self.fonte = ENTRADA_ANTERIOR  # de qual Mat do vetor essa etapa lê
        self.espaco_entrada = "BGR"
        self.erro = None
        self.info = None  # algum resultado pra mostrar (ex: limiar que o Otsu achou)

    def __getitem__(self, chave):
        return self.valores[chave]

    def parametro(self, chave):
        return next(p for p in self.parametros if p.chave == chave)

    def escolha(self, chave):
        # devolve o valor "de verdade" da opção escolhida no combobox
        return self.parametro(chave).opcoes[self.valores[chave]]

    def definir(self, chave, valor):
        self.valores[chave] = self.parametro(chave).ajustar(valor)

    def executar(self, src, mats, espaco_entrada="BGR"):
        self.erro = None
        self.info = None
        self.espaco_entrada = espaco_entrada
        return self.aplicar(src, mats)

    @abstractmethod
    def aplicar(self, src, mats):
        """Processa src e devolve o Mat de saída."""

    def espaco_saida(self, espaco_entrada, dst):
        if dst.ndim == 2:
            return "GRAY"
        return espaco_entrada if espaco_entrada != "GRAY" else "BGR"

    def titulo(self):
        # nome curto que aparece embaixo da miniatura no vetor de Mats
        return self.nome

    def resumo(self):
        return ", ".join(f"{p.rotulo}: {self.valores[p.chave]}" for p in self.parametros)
