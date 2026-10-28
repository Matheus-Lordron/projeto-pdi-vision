from html import escape

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout

DADO = Qt.ItemDataRole.UserRole


class PainelOperacoes(QFrame):
    # painel da esquerda: lista de operações por categoria + busca
    pediu_adicionar = pyqtSignal(type)

    def __init__(self, catalogo, parent=None):
        super().__init__(parent)
        self.setObjectName("Painel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        titulo = QLabel("Operações")
        titulo.setObjectName("TituloPainel")
        dica = QLabel("Duplo clique para adicionar após o Mat selecionado")
        dica.setObjectName("Apagado")
        dica.setWordWrap(True)

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar operação…")
        self.busca.setClearButtonEnabled(True)

        self.arvore = QTreeWidget()
        self.arvore.setHeaderHidden(True)
        self.arvore.setIndentation(14)
        self._preencher(catalogo)

        self.botao_adicionar = QPushButton("＋  Adicionar ao pipeline")
        self.botao_adicionar.setObjectName("Principal")
        self.botao_adicionar.setEnabled(False)

        for widget in (titulo, dica, self.busca):
            layout.addWidget(widget)
        layout.addWidget(self.arvore, 1)
        layout.addWidget(self.botao_adicionar)

        self.busca.textChanged.connect(self._filtrar)
        self.arvore.currentItemChanged.connect(self._ao_selecionar)
        self.arvore.itemDoubleClicked.connect(self._pedir_adicionar)
        self.botao_adicionar.clicked.connect(lambda: self._pedir_adicionar(self.arvore.currentItem()))

    def _preencher(self, catalogo):
        negrito = self.arvore.font()
        negrito.setBold(True)
        for categoria in catalogo:
            item_categoria = QTreeWidgetItem(self.arvore, [categoria.nome])
            item_categoria.setFont(0, negrito)
            item_categoria.setData(0, DADO, categoria)
            item_categoria.setToolTip(0, categoria.descricao)
            item_categoria.setExpanded(True)
            for classe in categoria.operacoes:
                item = QTreeWidgetItem(item_categoria, [classe.nome])
                item.setData(0, DADO, classe)  # guardo a classe; a instância é criada ao adicionar
                # descrição fica só na dica (tooltip) pra não poluir o painel
                item.setToolTip(0, f"<b>{escape(classe.nome)}</b> · <i>{escape(classe.funcao)}</i>"
                                   f"<br>{escape(classe.descricao)}")

    def _filtrar(self, texto):
        texto = texto.strip().lower()
        for i in range(self.arvore.topLevelItemCount()):
            item_categoria = self.arvore.topLevelItem(i)
            visiveis = 0
            for j in range(item_categoria.childCount()):
                item = item_categoria.child(j)
                classe = item.data(0, DADO)
                combina = not texto or texto in classe.nome.lower() or texto in classe.descricao.lower()
                item.setHidden(not combina)
                visiveis += combina
            item_categoria.setHidden(visiveis == 0)

    def _ao_selecionar(self, item, _anterior=None):
        self.botao_adicionar.setEnabled(item is not None and isinstance(item.data(0, DADO), type))

    def _pedir_adicionar(self, item, _coluna=0):
        dado = item.data(0, DADO) if item else None
        if isinstance(dado, type):
            self.pediu_adicionar.emit(dado)
