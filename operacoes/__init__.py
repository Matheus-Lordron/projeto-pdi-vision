from dataclasses import dataclass

from .bordas import Canny, Kirsch, Laplace, MascaraPassaAlta, Prewitt, Roberts, Sobel
from .cor import CinzaPorFormula, ConversaoCor, SepararCanal
from .entre_mats import Aritmetica, Logica
from .limiarizacao import FaixaValores, LimiarAdaptativo, LimiarGlobal
from .morfologia import Dilatacao, Erosao, MorfologiaAvancada
from .realce import AlargamentoContraste, BrilhoContraste, EqualizacaoHistograma, Negativo
from .suavizacao import FiltroBilateral, FiltroGaussiano, FiltroMedia, FiltroMediana


@dataclass(frozen=True)
class Categoria:
    nome: str
    descricao: str
    operacoes: tuple


# catálogo que aparece no painel da esquerda, na ordem dos requisitos do trabalho.
# pra criar uma operação nova é só fazer a classe e colocar ela aqui
CATALOGO = (
    Categoria("Conversão de cor",
              "Aula 1 — espaços de cor (BGR, HSV, Lab...), separação de canais e tons de cinza.",
              (ConversaoCor, SepararCanal, CinzaPorFormula)),
    Categoria("Realce (transformações pontuais)",
              "Aula 2 — cada pixel de saída depende só do pixel de entrada: B(x,y) = f[A(x,y)].",
              (BrilhoContraste, Negativo, AlargamentoContraste, EqualizacaoHistograma)),
    Categoria("Suavização (passa-baixa)",
              "Aula 2 — convolução com a vizinhança para reduzir ruído; borra a imagem.",
              (FiltroMedia, FiltroGaussiano, FiltroMediana, FiltroBilateral)),
    Categoria("Detecção de bordas (passa-alta)",
              "Aula 2 — realça as transições entre regiões: gradientes e máscaras passa-alta.",
              (Sobel, Laplace, Canny, Prewitt, Roberts, Kirsch, MascaraPassaAlta)),
    Categoria("Binarização (limiarização)",
              "Aulas 2 e 3 — separa a imagem em preto e branco a partir de limiares.",
              (LimiarGlobal, LimiarAdaptativo, FaixaValores)),
    Categoria("Morfologia matemática",
              "Aula 3 — transformações pela forma, usando um elemento estruturante.",
              (Erosao, Dilatacao, MorfologiaAvancada)),
    Categoria("Operações entre Mats",
              "Aula 2 — aritmética e lógica pixel a pixel entre dois Mats do vetor.",
              (Aritmetica, Logica)),
)
