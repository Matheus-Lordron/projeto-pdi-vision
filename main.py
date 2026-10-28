import sys

from PyQt6.QtWidgets import QApplication

from interface.janela_principal import JanelaPrincipal
from interface.tema import aplicar_tema


def main():
    app = QApplication(sys.argv)
    aplicar_tema(app)
    janela = JanelaPrincipal()
    if len(sys.argv) > 1:  # dá pra abrir já com uma imagem: python main.py imagem.png
        janela.carregar_imagem(sys.argv[1])
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
