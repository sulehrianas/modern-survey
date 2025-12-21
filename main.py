import sys
from PyQt6.QtWidgets import QApplication
from ui.gps_tab import GpsTab

def main():
    app = QApplication(sys.argv)
    
    window = GpsTab()
    window.setWindowTitle("Modern Survey")
    window.resize(1200, 800)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()