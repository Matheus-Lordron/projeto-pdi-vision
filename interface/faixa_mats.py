from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListView, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout,
)

from nucleo.operacao import ENTRADA_ANTERIOR
from nucleo.vetor_mats import descrever

from . import tema
from .conversao_qt import mat_para_qpixmap

MINIATURA = QSize(136, 96)


class FaixaMats(QFrame):
    # faixa de baixo: o vetor de Mats desenhado como miniaturas.
    # Clicar num cartão seleciona a etapa; os botões mexem na ordem/ativa/remove.
    selecionou = pyqtSignal(int)
    pediu_mover = pyqtSignal(int, int)
    pediu_ativar = pyqtSignal(int)
    pediu_remover = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Painel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        cabecalho = QHBoxLayout()
        titulo = QLabel("Vetor de Mats")
        titulo.setObjectName("TituloPainel")
        subtitulo = QLabel("Mat[0] é a original; Mat[i] é a saída da etapa i")
        subtitulo.setObjectName("Apagado")
        self.botao_esquerda = QPushButton("◀  Mover")
        self.botao_direita = QPushButton("Mover  ▶")
        self.botao_ativar = QPushButton("Desativar")
        self.botao_remover = QPushButton("Remover")
        cabecalho.addWidget(titulo)
        cabecalho.addWidget(subtitulo)
        cabecalho.addStretch(1)
        for botao in (self.botao_esquerda, self.botao_direita, self.botao_ativar, self.botao_remover):
            cabecalho.addWidget(botao)
        layout.addLayout(cabecalho)

        self.lista = QListWidget()
        self.lista.setViewMode(QListView.ViewMode.IconMode)
        self.lista.setFlow(QListView.Flow.LeftToRight)
        self.lista.setWrapping(False)
        self.lista.setMovement(QListView.Movement.Static)
        self.lista.setIconSize(MINIATURA)
        self.lista.setGridSize(QSize(MINIATURA.width() + 28, MINIATURA.height() + 64))
        self.lista.setWordWrap(True)
        self.lista.setHorizontalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.lista.setFixedHeight(MINIATURA.height() + 86)
        layout.addWidget(self.lista)

        self._sem_imagem = QPixmap(MINIATURA)
        self._sem_imagem.fill(QColor(tema.FUNDO))

        self.lista.currentRowChanged.connect(self._ao_mudar_linha)
        self.botao_esquerda.clicked.connect(lambda: self.pediu_mover.emit(self.lista.currentRow(), -1))
        self.botao_direita.clicked.connect(lambda: self.pediu_mover.emit(self.lista.currentRow(), +1))
        self.botao_ativar.clicked.connect(lambda: self.pediu_ativar.emit(self.lista.currentRow()))
        self.botao_remover.clicked.connect(self._pedir_remover)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self.lista, self._pedir_remover,
                  context=Qt.ShortcutContext.WidgetShortcut)
        self._pipeline = None

    def atualizar(self, pipeline, selecionado, inicio=0):
        # só redesenha a partir de mats[inicio]; os anteriores não mudaram
        self._pipeline = pipeline
        total = len(pipeline.etapas) + 1
        self.lista.blockSignals(True)
        while self.lista.count() > total:
            self.lista.takeItem(self.lista.count() - 1)
        while self.lista.count() < total:
            self.lista.addItem(QListWidgetItem())
        for i in range(max(0, inicio), total):
            self._atualizar_cartao(i)
        self.lista.setCurrentRow(selecionado)
        self.lista.blockSignals(False)
        self.lista.scrollToItem(self.lista.item(selecionado))
        self._atualizar_botoes()

    def _atualizar_cartao(self, i):
        pipeline = self._pipeline
        cartao = self.lista.item(i)
        item = pipeline.item(i)
        op = pipeline.etapa(i) if i else None

        marcador = ""
        cor = QColor(tema.TEXTO)
        if op and not op.ativa:
            marcador, cor = "  ⏸", QColor(tema.DESABILITADO)
        elif op and op.erro:
            marcador, cor = "  ⚠", QColor(tema.ERRO)
        linhas = [f"Mat[{i}]{marcador}", pipeline.rotulo(i)]
        if op and op.fonte != ENTRADA_ANTERIOR:
            linhas.append(f"entrada: Mat[{op.fonte}]")
        cartao.setText("\n".join(linhas))
        cartao.setForeground(cor)
        cartao.setIcon(QIcon(mat_para_qpixmap(item.mat, (MINIATURA.width(), MINIATURA.height()))
                             if item else self._sem_imagem))

        dica = [f"Mat[{i}] · {pipeline.rotulo(i)}"]
        if item:
            dica.append(descrever(item.mat) + f" · espaço {item.espaco}")
        if op:
            if op.parametros:
                dica.append(op.resumo())
            if op.erro:
                dica.append(f"⚠ {op.erro}")
        cartao.setToolTip("\n".join(dica))

    def _atualizar_botoes(self):
        linha, total = self.lista.currentRow(), self.lista.count()
        eh_etapa = linha >= 1  # Mat[0] (original) não pode mover nem remover
        self.botao_esquerda.setEnabled(linha >= 2)
        self.botao_direita.setEnabled(eh_etapa and linha < total - 1)
        self.botao_ativar.setEnabled(eh_etapa)
        self.botao_remover.setEnabled(eh_etapa)
        ativa = eh_etapa and self._pipeline.etapa(linha).ativa
        self.botao_ativar.setText("Desativar" if ativa or not eh_etapa else "Ativar")

    def _ao_mudar_linha(self, linha):
        if linha >= 0:
            self._atualizar_botoes()
            self.selecionou.emit(linha)

    def _pedir_remover(self):
        if self.lista.currentRow() >= 1:
            self.pediu_remover.emit(self.lista.currentRow())
