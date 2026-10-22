"""Painel esquerdo: catálogo de operações agrupadas por tema, com busca e descrição."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

ROLE = Qt.ItemDataRole.UserRole


class CatalogPanel(QFrame):
    add_requested = pyqtSignal(type)

    def __init__(self, catalog, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Operações")
        title.setObjectName("PanelTitle")
        hint = QLabel("Duplo clique para adicionar após o Mat selecionado")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar operação…")
        self.search.setClearButtonEnabled(True)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self._populate(catalog)

        self.info_title = QLabel()
        self.info_title.setStyleSheet("font-weight: 600;")
        self.info_title.setWordWrap(True)
        self.info_function = QLabel()
        self.info_function.setObjectName("Muted")
        self.info_text = QLabel()
        self.info_text.setWordWrap(True)
        info = QFrame()
        info.setObjectName("InfoCard")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(10, 8, 10, 8)
        for widget in (self.info_title, self.info_function, self.info_text):
            info_layout.addWidget(widget)

        self.add_button = QPushButton("＋  Adicionar ao pipeline")
        self.add_button.setObjectName("Primary")
        self.add_button.setEnabled(False)

        for widget in (title, hint, self.search):
            layout.addWidget(widget)
        layout.addWidget(self.tree, 1)
        layout.addWidget(info)
        layout.addWidget(self.add_button)

        self.search.textChanged.connect(self._filter)
        self.tree.currentItemChanged.connect(self._show_info)
        self.tree.itemDoubleClicked.connect(self._request_add)
        self.add_button.clicked.connect(lambda: self._request_add(self.tree.currentItem()))
        self._show_info(None)

    def _populate(self, catalog):
        bold = self.tree.font()
        bold.setBold(True)
        for category in catalog:
            cat_item = QTreeWidgetItem(self.tree, [category.name])
            cat_item.setFont(0, bold)
            cat_item.setData(0, ROLE, category)
            cat_item.setExpanded(True)
            for cls in category.operations:
                item = QTreeWidgetItem(cat_item, [cls.name])
                item.setData(0, ROLE, cls)
                item.setToolTip(0, cls.description)

    def _filter(self, text: str):
        text = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            visible = 0
            for j in range(cat_item.childCount()):
                item = cat_item.child(j)
                cls = item.data(0, ROLE)
                match = not text or text in cls.name.lower() or text in cls.description.lower()
                item.setHidden(not match)
                visible += match
            cat_item.setHidden(visible == 0)

    def _show_info(self, item, _previous=None):
        data = item.data(0, ROLE) if item else None
        is_operation = isinstance(data, type)
        self.add_button.setEnabled(is_operation)
        if data is None:
            title, function, text = ("Selecione uma operação", "",
                                     "A descrição e a função OpenCV usada aparecem aqui.")
        elif is_operation:
            title, function, text = data.name, data.function, data.description
        else:
            title, function, text = data.name, f"{len(data.operations)} operações", data.description
        self.info_title.setText(title)
        self.info_function.setText(function)
        self.info_function.setVisible(bool(function))
        self.info_text.setText(text)

    def _request_add(self, item, _column=0):
        data = item.data(0, ROLE) if item else None
        if isinstance(data, type):
            self.add_requested.emit(data)
