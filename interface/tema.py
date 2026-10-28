from PyQt6.QtGui import QColor, QFont, QPalette

# tema escuro: estilo Fusion + paleta de cores + alguns ajustes em QSS

FUNDO = "#15171c"
PAINEL = "#1d2027"
CAMPO = "#262a33"
BORDA = "#323743"
TEXTO = "#e6e8ec"
APAGADO = "#9aa3b2"
DESABILITADO = "#5c6370"
DESTAQUE = "#4c8dff"
DESTAQUE_SUAVE = "#28406b"
ERRO = "#ff6b6b"
FUNDO_IMAGEM = "#101216"

ESTILO = f"""
QFrame#Painel {{
    background: {PAINEL};
    border: 1px solid {BORDA};
    border-radius: 8px;
}}
QFrame#Painel QLabel {{ background: transparent; }}
QLabel#TituloPainel {{ font-size: 11pt; font-weight: 600; }}
QLabel#Apagado {{ color: {APAGADO}; }}
QLabel#Erro {{ color: {ERRO}; }}
QLabel#CaixaInfo {{
    background: {CAMPO};
    border: 1px solid {BORDA};
    border-radius: 6px;
    padding: 8px;
    font-family: Consolas, monospace;
}}
QTreeWidget, QListWidget, QLineEdit {{
    background: {CAMPO};
    border: 1px solid {BORDA};
    border-radius: 6px;
}}
QLineEdit {{ padding: 5px 8px; }}
QTreeWidget::item {{ padding: 3px 2px; }}
QTreeWidget::item:selected, QListWidget::item:selected {{
    background: {DESTAQUE_SUAVE};
    color: white;
    border-radius: 4px;
}}
QPushButton {{
    background: {CAMPO};
    border: 1px solid {BORDA};
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton:hover {{ border-color: {DESTAQUE}; }}
QPushButton:disabled {{ color: {DESABILITADO}; border-color: {BORDA}; }}
QPushButton#Principal {{
    background: {DESTAQUE};
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton#Principal:disabled {{ background: {DESTAQUE_SUAVE}; color: {APAGADO}; }}
QToolBar {{
    background: {PAINEL};
    border: none;
    border-bottom: 1px solid {BORDA};
    padding: 4px 8px;
    spacing: 4px;
}}
QToolBar QToolButton {{ padding: 6px 10px; border-radius: 6px; }}
QToolBar QToolButton:hover {{ background: {CAMPO}; }}
QStatusBar {{
    background: {PAINEL};
    border-top: 1px solid {BORDA};
    color: {APAGADO};
}}
QStatusBar QLabel {{ color: {APAGADO}; padding: 0 8px; }}
QSplitter::handle {{ background: {FUNDO}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""


def aplicar_tema(app):
    app.setStyle("Fusion")
    paleta = QPalette()
    cores = {
        QPalette.ColorRole.Window: FUNDO,
        QPalette.ColorRole.WindowText: TEXTO,
        QPalette.ColorRole.Base: CAMPO,
        QPalette.ColorRole.AlternateBase: PAINEL,
        QPalette.ColorRole.ToolTipBase: PAINEL,
        QPalette.ColorRole.ToolTipText: TEXTO,
        QPalette.ColorRole.Text: TEXTO,
        QPalette.ColorRole.Button: CAMPO,
        QPalette.ColorRole.ButtonText: TEXTO,
        QPalette.ColorRole.BrightText: "#ffffff",
        QPalette.ColorRole.Highlight: DESTAQUE,
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.Link: DESTAQUE,
        QPalette.ColorRole.PlaceholderText: APAGADO,
        QPalette.ColorRole.Mid: BORDA,
        QPalette.ColorRole.Dark: FUNDO,
    }
    for papel, cor in cores.items():
        paleta.setColor(papel, QColor(cor))
    for papel in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        paleta.setColor(QPalette.ColorGroup.Disabled, papel, QColor(DESABILITADO))
    app.setPalette(paleta)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(ESTILO)
