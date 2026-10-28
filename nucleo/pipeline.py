from .operacao import ENTRADA_ANTERIOR
from .vetor_mats import VetorMats

# Como funciona o "um filtro em cima do outro":
#  - self.etapas é a lista de operações, na ordem
#  - a etapa i lê mats[i-1] (ou outro Mat escolhido) e coloca o resultado em mats[i]
#  - a imagem original (mats[0]) nunca é alterada, então dá pra remover,
#    desativar ou reordenar etapas e simplesmente processar de novo


class Pipeline:
    def __init__(self):
        self.etapas = []
        self.mats = VetorMats()

    @property
    def tem_imagem(self):
        return not self.mats.empty()

    def definir_original(self, mat, rotulo="Original"):
        self.mats.clear()
        self.mats.push_back(mat, rotulo, "GRAY" if mat.ndim == 2 else "BGR")
        self.processar()

    def etapa(self, indice):
        # etapa que gera mats[indice] (indice começa em 1)
        return self.etapas[indice - 1]

    def rotulo(self, indice):
        if indice == 0:
            return self.mats.item(0).rotulo if self.tem_imagem else "Original"
        return self.etapa(indice).titulo()

    def item(self, indice):
        return self.mats.item(indice) if indice < len(self.mats) else None

    def indice_entrada(self, indice):
        fonte = self.etapa(indice).fonte
        return indice - 1 if fonte == ENTRADA_ANTERIOR else fonte

    def inserir(self, indice, operacao):
        indice = max(1, min(indice, len(self.etapas) + 1))
        self.etapas.insert(indice - 1, operacao)
        self.processar(indice)
        return indice

    def remover(self, indice):
        del self.etapas[indice - 1]
        self.processar(indice)

    def mover(self, indice, deslocamento):
        destino = indice + deslocamento
        if not 1 <= destino <= len(self.etapas):
            return indice
        self.etapas[indice - 1], self.etapas[destino - 1] = self.etapas[destino - 1], self.etapas[indice - 1]
        self.processar(min(indice, destino))
        return destino

    def limpar(self):
        self.etapas.clear()
        self.processar()

    def processar(self, inicio=1):
        # Reprocessa só a partir da etapa que mudou: mats[0..inicio-1] continuam válidos.
        # Isso deixa o slider fluido mesmo com várias etapas.
        if self.mats.empty():
            return
        inicio = max(1, min(inicio, len(self.mats)))
        self.mats.resize(inicio)

        for i in range(inicio, len(self.etapas) + 1):
            op = self.etapas[i - 1]
            anterior = self.mats.item(i - 1)
            # se a etapa estiver desativada (ou der erro) ela só repassa o Mat anterior
            dst, espaco = anterior.mat, anterior.espaco
            op.erro = op.info = None
            k = self.indice_entrada(i)

            if op.ativa and not 0 <= k < i:
                op.erro = f"A entrada Mat[{k}] não existe antes de Mat[{i}]; escolha outra entrada."
            elif op.ativa:
                entrada = self.mats.item(k)
                try:
                    dst = op.executar(entrada.mat, self.mats, entrada.espaco)
                    espaco = op.espaco_saida(entrada.espaco, dst)
                except Exception as exc:
                    # mostra o erro na tela em vez de fechar o programa
                    mensagem = str(exc).strip()
                    op.erro = mensagem.splitlines()[-1] if mensagem else type(exc).__name__

            self.mats.push_back(dst, op.titulo(), espaco)
