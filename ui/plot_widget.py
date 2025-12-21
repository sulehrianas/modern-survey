"""
A custom PyQt6 widget to display a matplotlib plot, designed for survey data.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PlotWidget(QWidget):
    """
    A custom widget that embeds a matplotlib FigureCanvas.
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)

        # Initial setup
        self.clear_plot()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def plot_traverse(self, points, title="Traverse Plot"):
        """
        Plots the traverse points and the lines connecting them.

        Args:
            points (list of tuples): A list of (easting, northing) coordinates.
            title (str): The title for the plot.
        """
        self.axes.clear()

        if not points or len(points) < 2:
            self.axes.set_title("Not enough data to plot")
            self.canvas.draw()
            return

        # Unzip points into separate lists for easting (x) and northing (y)
        eastings, northings = zip(*points)

        # Plot the traverse lines and points
        self.axes.plot(eastings, northings, 'b-o', label='Traverse Path') # Blue line with circle markers

        # Label the points with their names and coordinates
        for i, (e, n) in enumerate(points):
            label = "Start" if i == 0 else f"P{i}"
            self.axes.text(e, n, f' {label}\n E: {e:.3f}\n N: {n:.3f}', fontsize=8, va='bottom', ha='left')

        self.axes.set_xlabel("Easting (m)")
        self.axes.set_ylabel("Northing (m)")
        self.axes.set_title(title)
        self.axes.grid(True)
        self.axes.legend()
        self.axes.set_aspect('equal', adjustable='box') # Ensures correct geometric representation

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_triangulation(self, pA, pB, points, title="Triangulation Plot"):
        """
        Plots the baseline and calculated intersection points.
        pA, pB: tuples (easting, northing) for stations A and B.
        points: list of tuples (name, easting, northing) for target points.
        """
        self.axes.clear()
        
        # Plot Baseline A-B
        self.axes.plot([pA[0], pB[0]], [pA[1], pB[1]], 'k-s', linewidth=2, label='Baseline (A-B)', markersize=8)
        self.axes.text(pA[0], pA[1], " Stn A", fontsize=10, fontweight='bold', va='bottom')
        self.axes.text(pB[0], pB[1], " Stn B", fontsize=10, fontweight='bold', va='bottom')

        # Plot Target Points and Sight Lines
        for name, e, n in points:
            # Dashed lines from A and B to the target
            self.axes.plot([pA[0], e], [pA[1], n], 'g--', alpha=0.5)
            self.axes.plot([pB[0], e], [pB[1], n], 'g--', alpha=0.5)
            # The target point marker
            self.axes.plot(e, n, 'r^', markersize=8)
            self.axes.text(e, n, f" {name}\n ({e:.2f}, {n:.2f})", fontsize=9)

        self.axes.set_xlabel("Easting (m)")
        self.axes.set_ylabel("Northing (m)")
        self.axes.set_title(title)
        self.axes.grid(True)
        self.axes.legend()
        self.axes.set_aspect('equal', adjustable='box')
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_network(self, stations, observations, title="Network Plot"):
        """
        Plots a generic survey network.
        stations: dict {name: {'e': x, 'n': y, ...}}
        observations: list of dicts (used to draw lines)
        """
        self.axes.clear()
        
        # Plot Stations
        for name, data in stations.items():
            marker = 'r^' if data.get('fixed') else 'bo'
            self.axes.plot(data['e'], data['n'], marker, markersize=8)
            self.axes.text(data['e'], data['n'], f" {name}", fontsize=9, fontweight='bold')

        # Plot Observations (Lines)
        for obs in observations:
            if obs['type'] == 'distance' or obs['type'] == 'azimuth':
                s_from = stations.get(obs['from'])
                s_to = stations.get(obs['to'])
                if s_from and s_to:
                    self.axes.plot([s_from['e'], s_to['e']], [s_from['n'], s_to['n']], 'k-', alpha=0.3)

        self.axes.set_title(title)
        self.axes.set_aspect('equal', adjustable='box')
        self.canvas.draw()

    def clear_plot(self):
        """Clears the plot and resets the title."""
        self.axes.clear()
        self.axes.set_title("Traverse Plot (Awaiting Calculation)")
        self.axes.grid(True)
        self.canvas.draw()