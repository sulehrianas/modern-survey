"""
Main window for the Modern Survey application. This file defines the main
container that holds all the different surveying modules as tabs.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget
)

# Import the tab widgets from their respective files
from .compass_tab import CompassTab
from .leveling_tab import LevelingTab
from .theodolite_tab import TheodoliteTab
from .trig_leveling_tab import TrigLevelingTab
from .triangulation_tab import TriangulationTab
from .gps_tab import GpsTab
from .map_tab import MapTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Survey")
        self.setGeometry(100, 100, 1200, 800) # Set a larger default size

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create a tab widget to hold the different modules
        self.tab_widget = QTabWidget()
        
        # Add the existing tabs to the tab widget
        self.tab_widget.addTab(CompassTab(), "Compass Traversing")
        self.tab_widget.addTab(TheodoliteTab(), "Theodolite Surveying")
        self.tab_widget.addTab(LevelingTab(), "Differential Leveling")
        self.tab_widget.addTab(TrigLevelingTab(), "Trigonometric Leveling")
        self.tab_widget.addTab(TriangulationTab(), "Triangulation")
        self.tab_widget.addTab(GpsTab(), "GPS / Conversion")
        self.tab_widget.addTab(MapTab(), "Map Viewer")

        # Set the main layout for the central widget
        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.tab_widget)