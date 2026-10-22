"""Janela principal: liga o pipeline (core) aos painéis da interface.

    ┌────────────┬──────────────────────────┬──────────────┐
    │ Operações  │ Visualizador do Mat      │ Parâmetros + │
    │ (catálogo) │ selecionado (± compar.)  │ código OpenCV│
    ├────────────┴──────────────────────────┴──────────────┤
    │ Vetor de Mats: Mat[0] → Mat[1] → Mat[2] → …          │
    └──────────────────────────────────────────────────────┘
"""

import os
import re
import unicodedata

import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QSplitter,
    QWidget,
)

from core.image_io import IMAGE_EXTENSIONS, IMAGE_FILTER, imread, imwrite
from core.mat_vector import describe
from core.pipeline import Pipeline
from operations import CATALOG

from .catalog_panel import CatalogPanel
from .image_viewer import ImageViewer
from .mat_strip import MatStrip
from .params_panel import ParamsPanel

COMPARE_MODES = {
    "Sem comparação": None,
    "Entrada × saída da etapa": "input",
    "Original × Mat selecionado": "original",
}


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDI Vision")
        self.resize(1440, 900)
        self.setAcceptDrops(True)

        self.pipeline = Pipeline()
        self.selected = 0
        self.source_path: str | None = None
        self._pending: int | None = None
        # Agrupa mudanças rápidas (arrastar um slider) em um único reprocessamento
        self._timer = QTimer(self, singleShot=True, interval=15)
        self._timer.timeout.connect(self._process_pending)

        self._build_toolbar()
        self._build_layout()
        self._refresh()

    # ------------------------------------------------------------------ construção

    def _build_toolbar(self):
        toolbar = self.addToolBar("Principal")
        toolbar.setMovable(False)

        def action(text, slot, shortcut=None, tip=""):
            act = QAction(text, self)
            act.triggered.connect(slot)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            act.setToolTip(f"{tip} ({shortcut})" if shortcut else tip)
            toolbar.addAction(act)
            return act

        action("📂  Abrir imagem", self.open_image, "Ctrl+O", "Carrega a imagem que vira o Mat[0]")
        self.save_action = action("💾  Salvar Mat", self.save_selected, "Ctrl+S", "Salva o Mat selecionado")
        self.save_all_action = action("📁  Salvar todos", self.save_all, "Ctrl+Shift+S",
                                      "Salva cada Mat do vetor como um arquivo")
        toolbar.addSeparator()
        self.clear_action = action("🧹  Limpar pipeline", self.clear_pipeline, tip="Remove todas as etapas")
        toolbar.addSeparator()

        toolbar.addWidget(QLabel("  Comparar:  "))
        self.compare_combo = QComboBox()
        self.compare_combo.addItems(list(COMPARE_MODES))
        self.compare_combo.currentTextChanged.connect(lambda _text: self._show_selected())
        toolbar.addWidget(self.compare_combo)

    def _build_layout(self):
        self.catalog = CatalogPanel(CATALOG)
        self.params = ParamsPanel()
        self.strip = MatStrip()

        self.viewer = ImageViewer("Abra uma imagem (Ctrl+O) ou arraste um arquivo para cá.\n\n"
                                  "Ela será o Mat[0]; cada operação adicionada gera um novo Mat.")
        self.reference_viewer = ImageViewer()
        self.reference_viewer.hide()
        self.viewers = viewers = QSplitter(Qt.Orientation.Horizontal)
        viewers.addWidget(self.reference_viewer)
        viewers.addWidget(self.viewer)
        viewer_panel = QFrame()
        viewer_panel.setObjectName("Panel")
        viewer_layout = QHBoxLayout(viewer_panel)
        viewer_layout.setContentsMargins(1, 1, 1, 1)
        viewer_layout.addWidget(viewers)

        top = QSplitter(Qt.Orientation.Horizontal)
        top.addWidget(self.catalog)
        top.addWidget(viewer_panel)
        top.addWidget(self.params)
        top.setStretchFactor(1, 1)
        top.setSizes([290, 800, 350])
        top.setChildrenCollapsible(False)

        main = QSplitter(Qt.Orientation.Vertical)
        main.addWidget(top)
        main.addWidget(self.strip)
        main.setStretchFactor(0, 1)
        main.setChildrenCollapsible(False)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(main)
        self.setCentralWidget(central)

        self.pixel_label = QLabel()
        self.mat_label = QLabel()
        self.statusBar().addWidget(self.pixel_label, 1)
        self.statusBar().addPermanentWidget(self.mat_label)

        self.catalog.add_requested.connect(self.add_operation)
        self.params.changed.connect(self._schedule_run)
        self.strip.selected.connect(self.select)
        self.strip.move_requested.connect(self.move_step)
        self.strip.toggle_requested.connect(self.toggle_step)
        self.strip.remove_requested.connect(self.remove_step)
        self.viewer.hovered.connect(self._show_pixel)
        self.reference_viewer.hovered.connect(self._show_pixel)

    # ------------------------------------------------------------------ pipeline

    def add_operation(self, op_class):
        """Insere a operação logo depois do Mat selecionado e seleciona o novo Mat."""
        self.selected = self.pipeline.insert(self.selected + 1, op_class())
        self._refresh(self.selected)

    def select(self, index: int):
        self.selected = index
        self.params.show_index(self.pipeline, index, self.source_path)
        self._show_selected()

    def move_step(self, index: int, delta: int):
        target = self.pipeline.move(index, delta)
        self.selected = target
        self._refresh(min(index, target))

    def toggle_step(self, index: int):
        op = self.pipeline.step(index)
        op.enabled = not op.enabled
        self.pipeline.run(index)
        self._refresh(index)

    def remove_step(self, index: int):
        self.pipeline.remove(index)
        self.selected = index - 1
        self._refresh(index)

    def clear_pipeline(self):
        if not self.pipeline.steps:
            return
        answer = QMessageBox.question(self, "Limpar pipeline",
                                      f"Remover as {len(self.pipeline.steps)} etapas do pipeline?")
        if answer == QMessageBox.StandardButton.Yes:
            self.pipeline.clear()
            self.selected = 0
            self._refresh()

    def _schedule_run(self, index: int):
        self._pending = index if self._pending is None else min(self._pending, index)
        self._timer.start()

    def _process_pending(self):
        first, self._pending = self._pending, None
        self.pipeline.run(first)
        self.strip.refresh(self.pipeline, self.selected, first)
        self.params.refresh()
        self._show_selected()

    def _refresh(self, first: int = 0):
        """Atualiza toda a interface após uma mudança na estrutura do pipeline."""
        self.selected = max(0, min(self.selected, len(self.pipeline.steps)))
        self.strip.refresh(self.pipeline, self.selected, first)
        self.params.show_index(self.pipeline, self.selected, self.source_path)
        self._show_selected()
        has_image = self.pipeline.has_image
        self.save_action.setEnabled(has_image)
        self.save_all_action.setEnabled(has_image)
        self.clear_action.setEnabled(bool(self.pipeline.steps))

    # ------------------------------------------------------------------ visualização

    def _reference_index(self) -> int | None:
        mode = COMPARE_MODES[self.compare_combo.currentText()]
        if mode is None or self.selected == 0 or not self.pipeline.has_image:
            return None
        if mode == "original":
            return 0
        source = self.pipeline.source_index(self.selected)
        return source if 0 <= source < self.selected else self.selected - 1

    def _show_selected(self):
        entry = self.pipeline.entry(self.selected)
        if entry is None:
            self.viewer.clear()
            self.reference_viewer.hide()
            self.mat_label.setText("")
            return
        self.viewer.show_mat(entry.mat, f"Mat[{self.selected}] · {entry.label}")
        self.mat_label.setText(f"Mat[{self.selected}]  ·  {describe(entry.mat)}  ·  espaço {entry.space}")
        reference = self._reference_index()
        if reference is None:
            self.reference_viewer.hide()
        else:
            ref_entry = self.pipeline.entry(reference)
            self.reference_viewer.show_mat(ref_entry.mat, f"Mat[{reference}] · {ref_entry.label}")
            if self.reference_viewer.isHidden():
                self.reference_viewer.show()
                half = self.viewers.width() // 2
                self.viewers.setSizes([half, half])

    def _show_pixel(self, x: int, y: int):
        if x < 0 or not self.pipeline.has_image:
            self.pixel_label.setText("")
            return
        indices = [self.selected]
        reference = self._reference_index()
        if reference is not None:
            indices.insert(0, reference)
        parts = [f"x = {x}, y = {y}"]
        for index in indices:
            entry = self.pipeline.entry(index)
            if entry is None or y >= entry.mat.shape[0] or x >= entry.mat.shape[1]:
                continue
            values = np.atleast_1d(entry.mat[y, x])
            channels = "  ".join(f"{n} = {v}" for n, v in zip(entry.channel_names, values))
            parts.append(f"Mat[{index}]: {channels}")
        self.pixel_label.setText("     │     ".join(parts))

    # ------------------------------------------------------------------ arquivos

    def _start_dir(self) -> str:
        return os.path.dirname(self.source_path) if self.source_path else ""

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir imagem", self._start_dir(), IMAGE_FILTER)
        if path:
            self.load_image(path)

    def load_image(self, path: str):
        mat = imread(path)
        if mat is None:
            QMessageBox.warning(self, "Abrir imagem", f"Não foi possível ler a imagem:\n{path}")
            return
        self.source_path = path
        self.pipeline.set_source(mat)
        self.setWindowTitle(f"PDI Vision — {os.path.basename(path)}")
        self._refresh()

    def _mat_filename(self, index: int) -> str:
        return f"mat_{index:02d}_{_slug(self.pipeline.label(index))}.png"

    def save_selected(self):
        entry = self.pipeline.entry(self.selected)
        if entry is None:
            return
        default = os.path.join(self._start_dir(), self._mat_filename(self.selected))
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Mat", default,
                                              "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;TIFF (*.tif)")
        if not path:
            return
        if imwrite(path, entry.mat):
            self.statusBar().showMessage(f"Mat[{self.selected}] salvo em {path}", 5000)
        else:
            QMessageBox.warning(self, "Salvar Mat", f"Não foi possível salvar em:\n{path}")

    def save_all(self):
        folder = QFileDialog.getExistingDirectory(self, "Salvar todos os Mats em…", self._start_dir())
        if not folder:
            return
        saved = sum(imwrite(os.path.join(folder, self._mat_filename(i)), mat)
                    for i, mat in enumerate(self.pipeline.mats))
        self.statusBar().showMessage(f"{saved} Mats salvos em {folder}", 5000)

    def dragEnterEvent(self, event):
        if any(url.toLocalFile().lower().endswith(IMAGE_EXTENSIONS) for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.toLocalFile().lower().endswith(IMAGE_EXTENSIONS):
                self.load_image(url.toLocalFile())
                break
