import cv2
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QListWidget, QLabel, QPushButton, QFileDialog,
    QScrollArea, QSplitter, QGroupBox, QComboBox, QSlider,
    QFormLayout
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from core.image_state import ImageState
from core.pipeline import ImagePipeline
from filters import FILTER_REGISTRY
from utils.cv_qt_conversion import cv_to_qpixmap

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e24;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTreeWidget, QListWidget, QScrollArea {
    background-color: #2b2b36;
    border: 1px solid #3d3d4d;
    border-radius: 4px;
    padding: 4px;
}
QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #4a5b7d;
    color: #ffffff;
}
QPushButton {
    background-color: #3b3f51;
    border: 1px solid #4f5368;
    padding: 6px 12px;
    border-radius: 4px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #4c5169;
}
QPushButton:pressed {
    background-color: #2a2c39;
}
QGroupBox {
    border: 1px solid #3d3d4d;
    border-radius: 6px;
    margin-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QComboBox {
    background-color: #3b3f51;
    border: 1px solid #4f5368;
    border-radius: 4px;
    padding: 4px;
    color: #ffffff;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDI Vision Studio - RoboRealm Style")
        self.resize(1280, 800)
        self.setStyleSheet(DARK_STYLE)

        self.image_state = ImageState()
        self.pipeline = ImagePipeline(self.image_state)

        self.init_ui()
        self.populate_module_tree()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # PAINEL ESQUERDO
        left_box = QGroupBox("Catálogo de Filtros")
        left_layout = QVBoxLayout(left_box)

        btn_open = QPushButton("📂 Abrir Imagem")
        btn_open.clicked.connect(self.open_image_dialog)
        left_layout.addWidget(btn_open)

        self.tree_modules = QTreeWidget()
        self.tree_modules.setHeaderHidden(True)
        self.tree_modules.itemDoubleClicked.connect(self.on_module_double_clicked)
        left_layout.addWidget(self.tree_modules)

        h_splitter.addWidget(left_box)

        # PAINEL CENTRAL
        center_box = QGroupBox("Visualizador")
        center_layout = QVBoxLayout(center_box)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_image = QLabel("Carregue uma imagem para começar...")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.lbl_image)
        center_layout.addWidget(self.scroll_area)

        h_splitter.addWidget(center_box)

        # PAINEL DIREITO
        right_box = QGroupBox("Pipeline de Processamento")
        right_layout = QVBoxLayout(right_box)

        self.list_pipeline = QListWidget()
        self.list_pipeline.currentRowChanged.connect(self.on_pipeline_item_selected)
        right_layout.addWidget(self.list_pipeline)

        btn_layout = QHBoxLayout()
        self.btn_up = QPushButton("▲")
        self.btn_up.clicked.connect(self.move_filter_up)
        self.btn_down = QPushButton("▼")
        self.btn_down.clicked.connect(self.move_filter_down)
        self.btn_toggle = QPushButton("Ativar/Desativar")
        self.btn_toggle.clicked.connect(self.toggle_filter)
        self.btn_remove = QPushButton("🗑 Remover")
        self.btn_remove.clicked.connect(self.remove_filter)

        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        btn_layout.addWidget(self.btn_toggle)
        btn_layout.addWidget(self.btn_remove)
        right_layout.addLayout(btn_layout)

        self.prop_box = QGroupBox("Propriedades do Filtro")
        self.prop_layout = QFormLayout(self.prop_box)
        right_layout.addWidget(self.prop_box)

        h_splitter.addWidget(right_box)
        h_splitter.setSizes([260, 680, 340])
        main_layout.addWidget(h_splitter)

    def populate_module_tree(self):
        self.tree_modules.clear()
        for category, filter_classes in FILTER_REGISTRY.items():
            cat_item = QTreeWidgetItem(self.tree_modules, [category])
            cat_item.setExpanded(True)
            for cls in filter_classes:
                temp_inst = cls()
                mod_item = QTreeWidgetItem(cat_item, [temp_inst.name])
                mod_item.setData(0, Qt.ItemDataRole.UserRole, cls)

    def open_image_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg *.bmp *.tif)"
        )
        if filepath:
            if self.image_state.load_image(filepath):
                self.update_view()

    def on_module_double_clicked(self, item: QTreeWidgetItem, column: int):
        cls = item.data(0, Qt.ItemDataRole.UserRole)
        if cls:
            new_filter = cls()
            self.pipeline.add_filter(new_filter)
            self.list_pipeline.addItem(f"● {new_filter.name}")
            self.list_pipeline.setCurrentRow(len(self.pipeline.filters) - 1)
            self.update_view()

    def move_filter_up(self):
        row = self.list_pipeline.currentRow()
        if row > 0:
            self.pipeline.move_filter(row, row - 1)
            item = self.list_pipeline.takeItem(row)
            self.list_pipeline.insertItem(row - 1, item)
            self.list_pipeline.setCurrentRow(row - 1)
            self.update_view()

    def move_filter_down(self):
        row = self.list_pipeline.currentRow()
        if 0 <= row < len(self.pipeline.filters) - 1:
            self.pipeline.move_filter(row, row + 1)
            item = self.list_pipeline.takeItem(row)
            self.list_pipeline.insertItem(row + 1, item)
            self.list_pipeline.setCurrentRow(row + 1)
            self.update_view()

    def toggle_filter(self):
        row = self.list_pipeline.currentRow()
        if 0 <= row < len(self.pipeline.filters):
            f = self.pipeline.filters[row]
            f.is_enabled = not f.is_enabled
            status = "●" if f.is_enabled else "○ (desativado)"
            self.list_pipeline.item(row).setText(f"{status} {f.name}")
            self.update_view()

    def remove_filter(self):
        row = self.list_pipeline.currentRow()
        if 0 <= row < len(self.pipeline.filters):
            self.pipeline.remove_filter(row)
            self.list_pipeline.takeItem(row)
            self.clear_properties_panel()
            self.update_view()

    def on_pipeline_item_selected(self, row: int):
        self.clear_properties_panel()
        if 0 <= row < len(self.pipeline.filters):
            active_filter = self.pipeline.filters[row]
            schema = active_filter.get_ui_schema()

            for param_key, config in schema.items():
                p_type = config.get('type')

                if p_type == 'combobox':
                    combo = QComboBox()
                    combo.addItems(config.get('options', []))
                    combo.setCurrentText(str(active_filter.params.get(param_key)))
                    combo.currentTextChanged.connect(
                        lambda val, key=param_key, f=active_filter: self.on_param_changed(f, key, val)
                    )
                    self.prop_layout.addRow(param_key.capitalize() + ":", combo)

                elif p_type == 'slider':
                    slider = QSlider(Qt.Orientation.Horizontal)
                    slider.setMinimum(config.get('min', 0))
                    slider.setMaximum(config.get('max', 255))
                    slider.setValue(active_filter.params.get(param_key, config.get('default', 0)))
                    slider.valueChanged.connect(
                        lambda val, key=param_key, f=active_filter: self.on_param_changed(f, key, val)
                    )
                    self.prop_layout.addRow(param_key.capitalize() + ":", slider)

    def clear_properties_panel(self):
        while self.prop_layout.count():
            item = self.prop_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def on_param_changed(self, target_filter, param_name, new_val):
        target_filter.update_param(param_name, new_val)
        self.update_view()

    def update_view(self):
        result = self.pipeline.process()
        if result is not None:
            pixmap = cv_to_qpixmap(result)
            vp_size = self.scroll_area.viewport().size()
            scaled_pixmap = pixmap.scaled(
                vp_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_image.setPixmap(scaled_pixmap)