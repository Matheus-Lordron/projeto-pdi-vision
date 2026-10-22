"""Faixa inferior: o vetor de Mats exibido como uma sequência de miniaturas.

Cada cartão é um Mat[i]; clicar nele seleciona a etapa que o gerou. A faixa
também é o lugar para reordenar, desativar e remover etapas do pipeline.
"""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListView, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout,
)

from core.mat_vector import describe
from core.operation import INPUT_REF
from core.pipeline import Pipeline

from . import theme
from .qt_image import mat_to_qpixmap

THUMB = QSize(136, 96)


class MatStrip(QFrame):
    selected = pyqtSignal(int)
    move_requested = pyqtSignal(int, int)
    toggle_requested = pyqtSignal(int)
    remove_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Vetor de Mats")
        title.setObjectName("PanelTitle")
        subtitle = QLabel("Mat[0] é a original; Mat[i] é a saída da etapa i")
        subtitle.setObjectName("Muted")
        self.left_button = QPushButton("◀  Mover")
        self.right_button = QPushButton("Mover  ▶")
        self.toggle_button = QPushButton("Desativar")
        self.remove_button = QPushButton("Remover")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch(1)
        for button in (self.left_button, self.right_button, self.toggle_button, self.remove_button):
            header.addWidget(button)
        layout.addLayout(header)

        self.list = QListWidget()
        self.list.setViewMode(QListView.ViewMode.IconMode)
        self.list.setFlow(QListView.Flow.LeftToRight)
        self.list.setWrapping(False)
        self.list.setMovement(QListView.Movement.Static)
        self.list.setIconSize(THUMB)
        self.list.setGridSize(QSize(THUMB.width() + 28, THUMB.height() + 64))
        self.list.setWordWrap(True)
        self.list.setHorizontalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.list.setFixedHeight(THUMB.height() + 86)
        layout.addWidget(self.list)

        self._placeholder = QPixmap(THUMB)
        self._placeholder.fill(QColor(theme.BG))

        self.list.currentRowChanged.connect(self._on_row)
        self.left_button.clicked.connect(lambda: self.move_requested.emit(self.list.currentRow(), -1))
        self.right_button.clicked.connect(lambda: self.move_requested.emit(self.list.currentRow(), +1))
        self.toggle_button.clicked.connect(lambda: self.toggle_requested.emit(self.list.currentRow()))
        self.remove_button.clicked.connect(self._request_remove)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self.list, self._request_remove,
                  context=Qt.ShortcutContext.WidgetShortcut)
        self._pipeline: Pipeline | None = None

    def refresh(self, pipeline: Pipeline, selected: int, first: int = 0):
        """Atualiza os cartões a partir de Mat[first] (os anteriores não mudaram)."""
        self._pipeline = pipeline
        count = len(pipeline.steps) + 1
        self.list.blockSignals(True)
        while self.list.count() > count:
            self.list.takeItem(self.list.count() - 1)
        while self.list.count() < count:
            self.list.addItem(QListWidgetItem())
        for i in range(max(0, first), count):
            self._update_item(i)
        self.list.setCurrentRow(selected)
        self.list.blockSignals(False)
        self.list.scrollToItem(self.list.item(selected))
        self._update_buttons()

    def _update_item(self, i: int):
        pipeline = self._pipeline
        item = self.list.item(i)
        entry = pipeline.entry(i)
        op = pipeline.step(i) if i else None

        marker = ""
        color = QColor(theme.TEXT)
        if op and not op.enabled:
            marker, color = "  ⏸", QColor(theme.DISABLED)
        elif op and op.error:
            marker, color = "  ⚠", QColor(theme.ERROR)
        lines = [f"Mat[{i}]{marker}", pipeline.label(i)]
        if op and op.source != INPUT_REF:
            lines.append(f"entrada: Mat[{op.source}]")
        item.setText("\n".join(lines))
        item.setForeground(color)
        item.setIcon(QIcon(mat_to_qpixmap(entry.mat, (THUMB.width(), THUMB.height()))
                           if entry else self._placeholder))

        tooltip = [f"Mat[{i}] · {pipeline.label(i)}"]
        if entry:
            tooltip.append(describe(entry.mat) + f" · espaço {entry.space}")
        if op:
            if op.params:
                tooltip.append(op.summary())
            if op.error:
                tooltip.append(f"⚠ {op.error}")
        item.setToolTip("\n".join(tooltip))

    def _update_buttons(self):
        row, count = self.list.currentRow(), self.list.count()
        is_step = row >= 1
        self.left_button.setEnabled(row >= 2)
        self.right_button.setEnabled(is_step and row < count - 1)
        self.toggle_button.setEnabled(is_step)
        self.remove_button.setEnabled(is_step)
        enabled = is_step and self._pipeline.step(row).enabled
        self.toggle_button.setText("Desativar" if enabled or not is_step else "Ativar")

    def _on_row(self, row: int):
        if row >= 0:
            self._update_buttons()
            self.selected.emit(row)

    def _request_remove(self):
        if self.list.currentRow() >= 1:
            self.remove_requested.emit(self.list.currentRow())
