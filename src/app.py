import sys
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from src.game_window import GameWindow

def main():
    app = QApplication(sys.argv)
    game_window = GameWindow()
    apply_stylesheet(app, theme='dark_teal.xml')
    game_window.show()
    game_window.center_window()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
