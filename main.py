import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow

def exception_hook(exctype, value, tb):
    """Global function to catch unhandled exceptions and display a message box."""
    traceback_formated = traceback.format_exception(exctype, value, tb)
    traceback_string = "".join(traceback_formated)
    print(traceback_string, file=sys.stderr)
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("An unexpected error occurred")
    msg.setInformativeText(str(value))
    msg.setDetailedText(traceback_string)
    msg.setWindowTitle("Critical Error")
    msg.exec()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    print("Launching Modern Survey - Updated Version")

    # Load stylesheet for a modern look
    try:
        with open(resource_path("ui/style.qss"), "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Stylesheet 'ui/style.qss' not found, using default style.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()