import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import apply_theme


def main():
    app = QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow()
    if len(sys.argv) > 1:  # opcional: python main.py caminho/da/imagem.png
        window.load_image(sys.argv[1])
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
