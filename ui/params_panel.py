"""Painel direito: parâmetros da etapa selecionada, gerados a partir de ``op.params``.

Também mostra o resultado didático da operação (ex.: limiar do Otsu, elemento
estruturante) e o código Python/OpenCV equivalente, já com o vetor de Mats.
"""

import os

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QPlainTextEdit, QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from core.mat_vector import describe
from core.operation import (
    INPUT_REF, BoolParam, ChoiceParam, FloatParam, IntParam, MatRefParam, Operation,
)
from core.pipeline import Pipeline

_PLACEHOLDER_SRC = np.zeros((1, 1, 3), np.uint8)  # para gerar o código antes de abrir uma imagem


def _combo() -> QComboBox:
    """Combobox que pode encolher com o painel (o texto completo aparece ao abrir a lista)."""
    combo = QComboBox()
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(8)
    return combo


class ParamsPanel(QFrame):
    changed = pyqtSignal(int)  # índice do Mat cuja etapa mudou (reprocessar a partir dele)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self._pipeline: Pipeline | None = None
        self._index = 0
        self._original_name = "imagem.png"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        self.title = QLabel()
        self.title.setObjectName("PanelTitle")
        self.title.setWordWrap(True)
        self.function = QLabel()
        self.function.setObjectName("Muted")
        self.description = QLabel()
        self.description.setObjectName("Muted")
        self.description.setWordWrap(True)

        self.enabled_box = QCheckBox("Etapa ativa")
        self.enabled_box.toggled.connect(self._on_enabled)
        self.source_combo = _combo()
        self.source_combo.currentIndexChanged.connect(self._on_source)
        self.source_row = QWidget()
        source_layout = QFormLayout(self.source_row)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addRow("Entrada (src):", self.source_combo)

        self.form_host = QWidget()
        self.form = QFormLayout(self.form_host)
        self.form.setContentsMargins(0, 4, 0, 4)
        self.form.setVerticalSpacing(10)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.info = QLabel()
        self.info.setObjectName("InfoBox")
        self.info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.error = QLabel()
        self.error.setObjectName("Error")
        self.error.setWordWrap(True)

        code_title = QLabel("Código Python/OpenCV equivalente")
        code_title.setObjectName("Muted")
        self.code = QPlainTextEdit()
        self.code.setObjectName("Code")
        self.code.setReadOnly(True)
        self.code.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.code.setMinimumHeight(150)

        for widget in (self.title, self.function, self.description, self.enabled_box,
                       self.source_row, self.form_host, self.info, self.error, code_title, self.code):
            layout.addWidget(widget)
        layout.addStretch(1)

    # ------------------------------------------------------------------ exibição

    def show_index(self, pipeline: Pipeline, index: int, source_path: str | None = None):
        """Reconstrói o painel para Mat[index] (0 = imagem original)."""
        self._pipeline = pipeline
        self._index = index
        self._clear_form()
        if index == 0:
            self._show_original(source_path)
        else:
            self._show_step(pipeline.step(index))
        self.refresh()

    def _show_original(self, source_path):
        name = os.path.basename(source_path) if source_path else "imagem.png"
        self.title.setText("Mat[0] · Original")
        self.function.setText("cv.imread")
        self.description.setText(
            "Início do vetor de Mats: a imagem lida do disco, em BGR. Cada operação adicionada "
            "gera um novo Mat; selecione-os no vetor abaixo para ver e ajustar cada etapa."
        )
        self.enabled_box.hide()
        self.source_row.hide()
        self.form_host.hide()
        self._original_name = name

    def _show_step(self, op: Operation):
        self.title.setText(f"Mat[{self._index}] · {op.name}")
        self.function.setText(op.function)
        self.description.setText(op.description)
        self.enabled_box.show()
        self.enabled_box.blockSignals(True)
        self.enabled_box.setChecked(op.enabled)
        self.enabled_box.blockSignals(False)
        self._fill_source_combo(op)
        self.source_row.show()
        for param in op.params:
            label = QLabel(param.label)
            label.setToolTip(param.help)
            field = self._make_field(op, param)
            field.setToolTip(param.help)
            self.form.addRow(label, field)
        self.form_host.setVisible(bool(op.params))

    def refresh(self):
        """Atualiza só o retorno da operação (info, erro, código) sem recriar os controles."""
        pipeline, index = self._pipeline, self._index
        if pipeline is None:
            return
        if index == 0:
            self._set_info(describe(pipeline.mats[0]) if pipeline.has_image else None)
            self._set_error(None)
            self.code.setPlainText(
                "mats = []  # vetor de Mats\n"
                f"mats.append(cv.imread({self._original_name!r}))  # Mat[0]"
            )
            return
        op = pipeline.step(index)
        self._set_info(op.info)
        self._set_error(op.error)
        self.code.setPlainText(self._step_code(pipeline, index, op))

    def _step_code(self, pipeline: Pipeline, index: int, op: Operation) -> str:
        k = pipeline.source_index(index)
        entry = pipeline.entry(k) if 0 <= k < index else None
        src = entry.mat if entry is not None else _PLACEHOLDER_SRC
        label = pipeline.label(k) if 0 <= k < index else "inválido"
        lines = [f"src = mats[{k}]  # {label}", op.code(src, pipeline.mats), f"mats.append(dst)  # Mat[{index}]"]
        if not op.enabled:
            lines = ["# etapa desativada: o Mat anterior é repassado sem alteração",
                     f"mats.append(mats[{index - 1}])  # Mat[{index}]"]
        return "\n".join(lines)

    def _set_info(self, text):
        self.info.setText(text or "")
        self.info.setVisible(bool(text))

    def _set_error(self, text):
        self.error.setText(f"⚠ {text}" if text else "")
        self.error.setVisible(bool(text))

    def _clear_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)

    # ------------------------------------------------------------------ controles

    def _fill_source_combo(self, op: Operation):
        combo, pipeline, index = self.source_combo, self._pipeline, self._index
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(f"Mat anterior → Mat[{index - 1}] · {pipeline.label(index - 1)}", INPUT_REF)
        for k in range(index - 1):
            combo.addItem(f"Mat[{k}] · {pipeline.label(k)}", k)
        self._select_data(combo, op.source)
        combo.blockSignals(False)

    @staticmethod
    def _select_data(combo: QComboBox, value):
        position = combo.findData(value)
        if position < 0:  # referência que ficou inválida após mover/remover etapas
            combo.addItem(f"Mat[{value}] (inválido)", value)
            position = combo.count() - 1
        combo.setCurrentIndex(position)

    def _make_field(self, op: Operation, param) -> QWidget:
        if isinstance(param, IntParam):
            return self._number_field(op, param, integer=True)
        if isinstance(param, FloatParam):
            return self._number_field(op, param, integer=False)
        if isinstance(param, ChoiceParam):
            combo = _combo()
            combo.addItems(list(param.options))
            combo.setCurrentText(op[param.key])
            combo.currentTextChanged.connect(lambda v, k=param.key: self._set(op, k, v))
            return combo
        if isinstance(param, BoolParam):
            box = QCheckBox()
            box.setChecked(op[param.key])
            box.toggled.connect(lambda v, k=param.key: self._set(op, k, v))
            return box
        if isinstance(param, MatRefParam):
            combo = _combo()
            combo.addItem("Entrada da etapa (src)", INPUT_REF)
            for k in range(self._index):
                combo.addItem(f"Mat[{k}] · {self._pipeline.label(k)}", k)
            self._select_data(combo, op[param.key])
            combo.currentIndexChanged.connect(lambda _i, c=combo, k=param.key: self._set(op, k, c.currentData()))
            return combo
        raise TypeError(f"Parâmetro sem controle na interface: {type(param).__name__}")

    def _number_field(self, op: Operation, param, integer: bool) -> QWidget:
        """Slider + caixa numérica sincronizados (o valor fica sempre visível)."""
        field = QWidget()
        layout = QHBoxLayout(field)
        layout.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        if integer:
            spin = QSpinBox()
            spin.setRange(param.minimum, param.maximum)
            spin.setSingleStep(2 if param.odd else param.step)
            slider.setRange(param.minimum, param.maximum)
            to_slider, from_slider = int, int
        else:
            spin = QDoubleSpinBox()
            spin.setDecimals(param.decimals)
            spin.setRange(param.minimum, param.maximum)
            spin.setSingleStep(param.step)
            slider.setRange(0, round((param.maximum - param.minimum) / param.step))
            to_slider = lambda v: round((v - param.minimum) / param.step)  # noqa: E731
            from_slider = lambda i: param.minimum + i * param.step  # noqa: E731
        spin.setFixedWidth(76)
        spin.setValue(op[param.key])
        slider.setValue(to_slider(op[param.key]))

        def on_spin(value):
            coerced = param.coerce(value)
            if coerced != value:  # ex.: kernel par -> ajusta para ímpar
                spin.setValue(coerced)
                return
            slider.blockSignals(True)
            slider.setValue(to_slider(value))
            slider.blockSignals(False)
            self._set(op, param.key, coerced)

        slider.valueChanged.connect(lambda i: spin.setValue(from_slider(i)))
        spin.valueChanged.connect(on_spin)
        layout.addWidget(slider, 1)
        layout.addWidget(spin)
        return field

    # ------------------------------------------------------------------ eventos

    def _set(self, op: Operation, key: str, value):
        if op[key] == value:
            return
        op.set_value(key, value)
        self.changed.emit(self._index)

    def _on_enabled(self, checked: bool):
        if self._index > 0:
            self._pipeline.step(self._index).enabled = checked
            self.changed.emit(self._index)

    def _on_source(self, _position: int):
        if self._index > 0:
            self._pipeline.step(self._index).source = self.source_combo.currentData()
            self.changed.emit(self._index)
