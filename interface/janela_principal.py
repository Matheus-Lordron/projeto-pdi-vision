import os
import re
import unicodedata

import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QSplitter, QWidget,
)

from nucleo.arquivos import EXTENSOES, FILTRO_IMAGENS, ler_imagem, salvar_imagem
from nucleo.pipeline import Pipeline
from nucleo.vetor_mats import descrever
from operacoes import CATALOGO

from .faixa_mats import FaixaMats
from .painel_operacoes import PainelOperacoes
from .painel_parametros import PainelParametros
from .visualizador import Visualizador

# Layout:
#   [Operações] [Imagem (+ comparação)] [Parâmetros]
#   [-------------- Vetor de Mats --------------]
# A janela só liga os painéis ao Pipeline; o processamento em si fica no nucleo/.

MODOS_COMPARACAO = {
    "Sem comparação": None,
    "Entrada × saída da etapa": "entrada",
    "Original × Mat selecionado": "original",
}


def _nome_arquivo(texto):
    # 'Conversão de cor' -> 'conversao_de_cor'
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDI Vision")
        self.resize(1440, 900)
        self.setAcceptDrops(True)

        self.pipeline = Pipeline()
        self.selecionado = 0
        self.caminho_original = None
        self._pendente = None
        # junta várias mudanças seguidas (arrastar slider) num único reprocessamento
        self._temporizador = QTimer(self, singleShot=True, interval=15)
        self._temporizador.timeout.connect(self._processar_pendente)

        self._criar_barra()
        self._criar_layout()
        self._atualizar_tudo()

    # ---------------- montagem da tela ----------------

    def _criar_barra(self):
        barra = self.addToolBar("Principal")
        barra.setMovable(False)

        def acao(texto, funcao, atalho=None, dica=""):
            a = QAction(texto, self)
            a.triggered.connect(funcao)
            if atalho:
                a.setShortcut(QKeySequence(atalho))
            a.setToolTip(f"{dica} ({atalho})" if atalho else dica)
            barra.addAction(a)
            return a

        acao("📂  Abrir imagem", self.abrir_imagem, "Ctrl+O", "Carrega a imagem que vira o Mat[0]")
        self.acao_salvar = acao("💾  Salvar Mat", self.salvar_selecionado, "Ctrl+S", "Salva o Mat selecionado")
        self.acao_salvar_todos = acao("📁  Salvar todos", self.salvar_todos, "Ctrl+Shift+S",
                                      "Salva cada Mat do vetor como um arquivo")
        barra.addSeparator()
        self.acao_limpar = acao("🧹  Limpar pipeline", self.limpar_pipeline, dica="Remove todas as etapas")
        barra.addSeparator()

        barra.addWidget(QLabel("  Comparar:  "))
        self.combo_comparacao = QComboBox()
        self.combo_comparacao.addItems(list(MODOS_COMPARACAO))
        self.combo_comparacao.currentTextChanged.connect(lambda _t: self._mostrar_selecionado())
        barra.addWidget(self.combo_comparacao)

    def _criar_layout(self):
        self.painel_operacoes = PainelOperacoes(CATALOGO)
        self.painel_parametros = PainelParametros()
        self.faixa = FaixaMats()

        self.visualizador = Visualizador("Abra uma imagem (Ctrl+O) ou arraste um arquivo para cá.\n\n"
                                         "Ela será o Mat[0]; cada operação adicionada gera um novo Mat.")
        # segundo visualizador, só aparece no modo comparação (fica à esquerda)
        self.visualizador_ref = Visualizador()
        self.visualizador_ref.hide()
        self.divisor_imagens = QSplitter(Qt.Orientation.Horizontal)
        self.divisor_imagens.addWidget(self.visualizador_ref)
        self.divisor_imagens.addWidget(self.visualizador)
        painel_imagem = QFrame()
        painel_imagem.setObjectName("Painel")
        layout_imagem = QHBoxLayout(painel_imagem)
        layout_imagem.setContentsMargins(1, 1, 1, 1)
        layout_imagem.addWidget(self.divisor_imagens)

        topo = QSplitter(Qt.Orientation.Horizontal)
        topo.addWidget(self.painel_operacoes)
        topo.addWidget(painel_imagem)
        topo.addWidget(self.painel_parametros)
        topo.setStretchFactor(1, 1)
        topo.setSizes([290, 800, 350])
        topo.setChildrenCollapsible(False)

        principal = QSplitter(Qt.Orientation.Vertical)
        principal.addWidget(topo)
        principal.addWidget(self.faixa)
        principal.setStretchFactor(0, 1)
        principal.setChildrenCollapsible(False)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(principal)
        self.setCentralWidget(central)

        self.rotulo_pixel = QLabel()
        self.rotulo_mat = QLabel()
        self.statusBar().addWidget(self.rotulo_pixel, 1)
        self.statusBar().addPermanentWidget(self.rotulo_mat)

        self.painel_operacoes.pediu_adicionar.connect(self.adicionar_operacao)
        self.painel_parametros.alterou.connect(self._agendar_processamento)
        self.faixa.selecionou.connect(self.selecionar)
        self.faixa.pediu_mover.connect(self.mover_etapa)
        self.faixa.pediu_ativar.connect(self.ativar_desativar_etapa)
        self.faixa.pediu_remover.connect(self.remover_etapa)
        self.visualizador.mouse_sobre_pixel.connect(self._mostrar_pixel)
        self.visualizador_ref.mouse_sobre_pixel.connect(self._mostrar_pixel)

    # ---------------- ações do pipeline ----------------

    def adicionar_operacao(self, classe):
        # nova etapa entra logo depois do Mat selecionado (não só no final)
        self.selecionado = self.pipeline.inserir(self.selecionado + 1, classe())
        self._atualizar_tudo(self.selecionado)

    def selecionar(self, indice):
        # "voltar" pra uma etapa anterior: só seleciono o Mat dela, que já está guardado no vetor
        self.selecionado = indice
        self.painel_parametros.mostrar_indice(self.pipeline, indice, self.caminho_original)
        self._mostrar_selecionado()

    def mover_etapa(self, indice, deslocamento):
        destino = self.pipeline.mover(indice, deslocamento)
        self.selecionado = destino
        self._atualizar_tudo(min(indice, destino))

    def ativar_desativar_etapa(self, indice):
        op = self.pipeline.etapa(indice)
        op.ativa = not op.ativa
        self.pipeline.processar(indice)
        self._atualizar_tudo(indice)

    def remover_etapa(self, indice):
        self.pipeline.remover(indice)
        self.selecionado = indice - 1
        self._atualizar_tudo(indice)

    def limpar_pipeline(self):
        if not self.pipeline.etapas:
            return
        resposta = QMessageBox.question(self, "Limpar pipeline",
                                        f"Remover as {len(self.pipeline.etapas)} etapas do pipeline?")
        if resposta == QMessageBox.StandardButton.Yes:
            self.pipeline.limpar()
            self.selecionado = 0
            self._atualizar_tudo()

    def _agendar_processamento(self, indice):
        # guarda a menor etapa alterada e espera 15 ms antes de processar
        self._pendente = indice if self._pendente is None else min(self._pendente, indice)
        self._temporizador.start()

    def _processar_pendente(self):
        inicio, self._pendente = self._pendente, None
        self.pipeline.processar(inicio)
        self.faixa.atualizar(self.pipeline, self.selecionado, inicio)
        self.painel_parametros.atualizar()
        self._mostrar_selecionado()

    def _atualizar_tudo(self, inicio=0):
        # usado quando muda a estrutura do pipeline (adicionar, remover, mover...)
        self.selecionado = max(0, min(self.selecionado, len(self.pipeline.etapas)))
        self.faixa.atualizar(self.pipeline, self.selecionado, inicio)
        self.painel_parametros.mostrar_indice(self.pipeline, self.selecionado, self.caminho_original)
        self._mostrar_selecionado()
        tem_imagem = self.pipeline.tem_imagem
        self.acao_salvar.setEnabled(tem_imagem)
        self.acao_salvar_todos.setEnabled(tem_imagem)
        self.acao_limpar.setEnabled(bool(self.pipeline.etapas))

    # ---------------- visualização / comparação ----------------

    def _indice_referencia(self):
        # qual Mat aparece do lado esquerdo na comparação
        modo = MODOS_COMPARACAO[self.combo_comparacao.currentText()]
        if modo is None or self.selecionado == 0 or not self.pipeline.tem_imagem:
            return None
        if modo == "original":
            return 0
        # "entrada × saída": a entrada é o Mat que a etapa leu (normalmente mats[i-1])
        entrada = self.pipeline.indice_entrada(self.selecionado)
        return entrada if 0 <= entrada < self.selecionado else self.selecionado - 1

    def _mostrar_selecionado(self):
        item = self.pipeline.item(self.selecionado)
        if item is None:
            self.visualizador.limpar()
            self.visualizador_ref.hide()
            self.rotulo_mat.setText("")
            return
        self.visualizador.mostrar(item.mat, f"Mat[{self.selecionado}] · {item.rotulo}")
        self.rotulo_mat.setText(f"Mat[{self.selecionado}]  ·  {descrever(item.mat)}  ·  espaço {item.espaco}")
        referencia = self._indice_referencia()
        if referencia is None:
            self.visualizador_ref.hide()
        else:
            item_ref = self.pipeline.item(referencia)
            self.visualizador_ref.mostrar(item_ref.mat, f"Mat[{referencia}] · {item_ref.rotulo}")
            if self.visualizador_ref.isHidden():
                self.visualizador_ref.show()
                metade = self.divisor_imagens.width() // 2
                self.divisor_imagens.setSizes([metade, metade])

    def _mostrar_pixel(self, x, y):
        # barra de status: valor do pixel em cada canal (dos dois Mats, se estiver comparando)
        if x < 0 or not self.pipeline.tem_imagem:
            self.rotulo_pixel.setText("")
            return
        indices = [self.selecionado]
        referencia = self._indice_referencia()
        if referencia is not None:
            indices.insert(0, referencia)
        partes = [f"x = {x}, y = {y}"]
        for indice in indices:
            item = self.pipeline.item(indice)
            if item is None or y >= item.mat.shape[0] or x >= item.mat.shape[1]:
                continue
            valores = np.atleast_1d(item.mat[y, x])
            canais = "  ".join(f"{n} = {v}" for n, v in zip(item.nomes_canais, valores))
            partes.append(f"Mat[{indice}]: {canais}")
        self.rotulo_pixel.setText("     │     ".join(partes))

    # ---------------- arquivos ----------------

    def _pasta_inicial(self):
        return os.path.dirname(self.caminho_original) if self.caminho_original else ""

    def abrir_imagem(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Abrir imagem", self._pasta_inicial(), FILTRO_IMAGENS)
        if caminho:
            self.carregar_imagem(caminho)

    def carregar_imagem(self, caminho):
        mat = ler_imagem(caminho)
        if mat is None:
            QMessageBox.warning(self, "Abrir imagem", f"Não foi possível ler a imagem:\n{caminho}")
            return
        self.caminho_original = caminho
        # as etapas continuam; só troca o Mat[0] e reprocessa tudo
        self.pipeline.definir_original(mat)
        self.setWindowTitle(f"PDI Vision — {os.path.basename(caminho)}")
        self._atualizar_tudo()

    def _nome_mat(self, indice):
        return f"mat_{indice:02d}_{_nome_arquivo(self.pipeline.rotulo(indice))}.png"

    def salvar_selecionado(self):
        item = self.pipeline.item(self.selecionado)
        if item is None:
            return
        sugestao = os.path.join(self._pasta_inicial(), self._nome_mat(self.selecionado))
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Mat", sugestao,
                                                 "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;TIFF (*.tif)")
        if not caminho:
            return
        if salvar_imagem(caminho, item.mat):
            self.statusBar().showMessage(f"Mat[{self.selecionado}] salvo em {caminho}", 5000)
        else:
            QMessageBox.warning(self, "Salvar Mat", f"Não foi possível salvar em:\n{caminho}")

    def salvar_todos(self):
        pasta = QFileDialog.getExistingDirectory(self, "Salvar todos os Mats em…", self._pasta_inicial())
        if not pasta:
            return
        salvos = sum(salvar_imagem(os.path.join(pasta, self._nome_mat(i)), mat)
                     for i, mat in enumerate(self.pipeline.mats))
        self.statusBar().showMessage(f"{salvos} Mats salvos em {pasta}", 5000)

    # arrastar e soltar imagem na janela
    def dragEnterEvent(self, event):
        if any(url.toLocalFile().lower().endswith(EXTENSOES) for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.toLocalFile().lower().endswith(EXTENSOES):
                self.carregar_imagem(url.toLocalFile())
                break
