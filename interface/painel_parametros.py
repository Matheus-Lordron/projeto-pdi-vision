from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from nucleo.operacao import (
    ENTRADA_ANTERIOR, ParametroBooleano, ParametroEscolha, ParametroInteiro, ParametroMat, ParametroReal,
)
from nucleo.vetor_mats import descrever

from .histograma import Histograma, resumo_histograma


def _combo():
    # deixa o combobox encolher junto com o painel (texto longo não estica o painel)
    combo = QComboBox()
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(8)
    return combo


class PainelParametros(QFrame):
    # painel da direita: controles da etapa selecionada, montados a partir de op.parametros
    alterou = pyqtSignal(int)  # índice do Mat cuja etapa mudou -> reprocessa a partir dele

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Painel")
        self._pipeline = None
        self._indice = 0

        externo = QVBoxLayout(self)
        externo.setContentsMargins(0, 0, 0, 0)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        externo.addWidget(rolagem)

        conteudo = QWidget()
        rolagem.setWidget(conteudo)
        layout = QVBoxLayout(conteudo)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        self.titulo = QLabel()
        self.titulo.setObjectName("TituloPainel")
        self.titulo.setWordWrap(True)
        self.funcao = QLabel()
        self.funcao.setObjectName("Apagado")

        self.caixa_ativa = QCheckBox("Etapa ativa")
        self.caixa_ativa.toggled.connect(self._ao_ativar)
        self.combo_entrada = _combo()
        self.combo_entrada.currentIndexChanged.connect(self._ao_mudar_entrada)
        self.linha_entrada = QWidget()
        layout_entrada = QFormLayout(self.linha_entrada)
        layout_entrada.setContentsMargins(0, 0, 0, 0)
        layout_entrada.addRow("Entrada (src):", self.combo_entrada)

        self.area_form = QWidget()
        self.form = QFormLayout(self.area_form)
        self.form.setContentsMargins(0, 4, 0, 4)
        self.form.setVerticalSpacing(10)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.info = QLabel()
        self.info.setObjectName("CaixaInfo")
        self.info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.erro = QLabel()
        self.erro.setObjectName("Erro")
        self.erro.setWordWrap(True)

        # histogramas de antes/depois (só aparecem nas operações com mostrar_histograma, ex: equalização)
        self.area_histogramas = QWidget()
        layout_hist = QVBoxLayout(self.area_histogramas)
        layout_hist.setContentsMargins(0, 6, 0, 0)
        layout_hist.setSpacing(6)
        self.hist_entrada = Histograma("Antes (entrada)")
        self.hist_saida = Histograma("Depois (saída)")
        layout_hist.addWidget(self.hist_entrada)
        layout_hist.addWidget(self.hist_saida)
        self.area_histogramas.hide()

        for widget in (self.titulo, self.funcao, self.caixa_ativa, self.linha_entrada,
                       self.area_form, self.info, self.erro, self.area_histogramas):
            layout.addWidget(widget)
        layout.addStretch(1)

    # ---------------- montar o painel ----------------

    def mostrar_indice(self, pipeline, indice, caminho_original=None):
        # reconstrói tudo pra mats[indice] (0 = original)
        self._pipeline = pipeline
        self._indice = indice
        self._limpar_form()
        if indice == 0:
            self._mostrar_original(caminho_original)
        else:
            self._mostrar_etapa(pipeline.etapa(indice))
        self.atualizar()

    def _mostrar_original(self, caminho):
        self.titulo.setText("Mat[0] · Original")
        self.titulo.setToolTip("Início do vetor de Mats: a imagem lida do disco, em BGR.")
        self.funcao.setText("cv.imread")
        self.caixa_ativa.hide()
        self.linha_entrada.hide()
        self.area_form.hide()

    def _mostrar_etapa(self, op):
        self.titulo.setText(f"Mat[{self._indice}] · {op.nome}")
        self.titulo.setToolTip(op.descricao)
        self.funcao.setText(op.funcao)
        self.caixa_ativa.show()
        self.caixa_ativa.blockSignals(True)
        self.caixa_ativa.setChecked(op.ativa)
        self.caixa_ativa.blockSignals(False)
        self._preencher_entradas(op)
        self.linha_entrada.show()
        # um controle pra cada parâmetro que a operação declarou
        for parametro in op.parametros:
            rotulo = QLabel(parametro.rotulo)
            rotulo.setToolTip(parametro.dica)
            campo = self._criar_campo(op, parametro)
            campo.setToolTip(parametro.dica)
            self.form.addRow(rotulo, campo)
        self.area_form.setVisible(bool(op.parametros))

    def atualizar(self):
        # atualiza só info/erro/histograma, sem recriar os controles
        # (se recriasse, o slider perderia o "arrastar" no meio do movimento)
        pipeline, indice = self._pipeline, self._indice
        if pipeline is None:
            return
        if indice == 0:
            self._definir_info(descrever(pipeline.mats[0]) if pipeline.tem_imagem else None)
            self._definir_erro(None)
            self.area_histogramas.hide()
            return
        op = pipeline.etapa(indice)
        self._definir_info(op.info)
        self._definir_erro(op.erro)
        self._atualizar_histogramas(pipeline, indice, op)

    def _atualizar_histogramas(self, pipeline, indice, op):
        k = pipeline.indice_entrada(indice)
        entrada, saida = pipeline.item(k) if 0 <= k < indice else None, pipeline.item(indice)
        if not op.mostrar_histograma or entrada is None or saida is None:
            self.area_histogramas.hide()
            return
        self.hist_entrada.mostrar(entrada.mat, f"Antes — Mat[{k}] · {resumo_histograma(entrada.mat)}")
        self.hist_saida.mostrar(saida.mat, f"Depois — Mat[{indice}] · {resumo_histograma(saida.mat)}")
        self.area_histogramas.show()

    def _definir_info(self, texto):
        self.info.setText(texto or "")
        self.info.setVisible(bool(texto))

    def _definir_erro(self, texto):
        self.erro.setText(f"⚠ {texto}" if texto else "")
        self.erro.setVisible(bool(texto))

    def _limpar_form(self):
        while self.form.rowCount():
            self.form.removeRow(0)

    # ---------------- controles ----------------

    def _preencher_entradas(self, op):
        # lista os Mats anteriores que podem ser a entrada dessa etapa
        combo, pipeline, indice = self.combo_entrada, self._pipeline, self._indice
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(f"Mat anterior → Mat[{indice - 1}] · {pipeline.rotulo(indice - 1)}", ENTRADA_ANTERIOR)
        for k in range(indice - 1):
            combo.addItem(f"Mat[{k}] · {pipeline.rotulo(k)}", k)
        self._selecionar_dado(combo, op.fonte)
        combo.blockSignals(False)

    @staticmethod
    def _selecionar_dado(combo, valor):
        posicao = combo.findData(valor)
        if posicao < 0:  # referência que ficou inválida depois de mover/remover etapas
            combo.addItem(f"Mat[{valor}] (inválido)", valor)
            posicao = combo.count() - 1
        combo.setCurrentIndex(posicao)

    def _criar_campo(self, op, parametro):
        if isinstance(parametro, ParametroInteiro):
            return self._campo_numerico(op, parametro, inteiro=True)
        if isinstance(parametro, ParametroReal):
            return self._campo_numerico(op, parametro, inteiro=False)
        if isinstance(parametro, ParametroEscolha):
            combo = _combo()
            combo.addItems(list(parametro.opcoes))
            combo.setCurrentText(op[parametro.chave])
            combo.currentTextChanged.connect(lambda v, c=parametro.chave: self._definir(op, c, v))
            return combo
        if isinstance(parametro, ParametroBooleano):
            caixa = QCheckBox()
            caixa.setChecked(op[parametro.chave])
            caixa.toggled.connect(lambda v, c=parametro.chave: self._definir(op, c, v))
            return caixa
        if isinstance(parametro, ParametroMat):
            combo = _combo()
            combo.addItem("Entrada da etapa (src)", ENTRADA_ANTERIOR)
            for k in range(self._indice):
                combo.addItem(f"Mat[{k}] · {self._pipeline.rotulo(k)}", k)
            self._selecionar_dado(combo, op[parametro.chave])
            combo.currentIndexChanged.connect(
                lambda _i, cb=combo, c=parametro.chave: self._definir(op, c, cb.currentData()))
            return combo
        raise TypeError(f"Parâmetro sem controle na interface: {type(parametro).__name__}")

    def _campo_numerico(self, op, parametro, inteiro):
        # slider + caixa de número sincronizados, pra sempre ver o valor
        campo = QWidget()
        layout = QHBoxLayout(campo)
        layout.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        if inteiro:
            caixa = QSpinBox()
            caixa.setRange(parametro.minimo, parametro.maximo)
            caixa.setSingleStep(2 if parametro.impar else parametro.passo)
            slider.setRange(parametro.minimo, parametro.maximo)
            para_slider, do_slider = int, int
        else:
            # o QSlider só trabalha com inteiro, então converto pelo passo
            caixa = QDoubleSpinBox()
            caixa.setDecimals(parametro.casas)
            caixa.setRange(parametro.minimo, parametro.maximo)
            caixa.setSingleStep(parametro.passo)
            slider.setRange(0, round((parametro.maximo - parametro.minimo) / parametro.passo))
            para_slider = lambda v: round((v - parametro.minimo) / parametro.passo)  # noqa: E731
            do_slider = lambda i: parametro.minimo + i * parametro.passo  # noqa: E731
        caixa.setFixedWidth(76)
        caixa.setValue(op[parametro.chave])
        slider.setValue(para_slider(op[parametro.chave]))

        def ao_mudar_caixa(valor):
            ajustado = parametro.ajustar(valor)
            if ajustado != valor:  # ex: kernel par -> pula pro ímpar
                caixa.setValue(ajustado)
                return
            slider.blockSignals(True)
            slider.setValue(para_slider(valor))
            slider.blockSignals(False)
            self._definir(op, parametro.chave, ajustado)

        slider.valueChanged.connect(lambda i: caixa.setValue(do_slider(i)))
        caixa.valueChanged.connect(ao_mudar_caixa)
        layout.addWidget(slider, 1)
        layout.addWidget(caixa)
        return campo

    # ---------------- eventos ----------------

    def _definir(self, op, chave, valor):
        if op[chave] == valor:
            return
        op.definir(chave, valor)
        self.alterou.emit(self._indice)

    def _ao_ativar(self, marcado):
        if self._indice > 0:
            self._pipeline.etapa(self._indice).ativa = marcado
            self.alterou.emit(self._indice)

    def _ao_mudar_entrada(self, _posicao):
        if self._indice > 0:
            self._pipeline.etapa(self._indice).fonte = self.combo_entrada.currentData()
            self.alterou.emit(self._indice)
