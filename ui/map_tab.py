import io
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel

FOLIUM_ERROR = None
try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError as e:
    FOLIUM_AVAILABLE = False
    FOLIUM_ERROR = str(e)

WEB_ENGINE_ERROR = None
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError as e:
    WEB_ENGINE_AVAILABLE = False
    WEB_ENGINE_ERROR = str(e)

class MapTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        if not WEB_ENGINE_AVAILABLE:
            self.layout.addWidget(QLabel(f"Error importing 'PyQt6-WebEngine': {WEB_ENGINE_ERROR}"))
            return

        if not FOLIUM_AVAILABLE:
            self.layout.addWidget(QLabel(f"Error importing 'folium': {FOLIUM_ERROR}"))
            return

        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)
        
        # Initialize with a default map
        self.update_map()

    def update_map(self, coords=None):
        """
        Generates a Folium map and displays it in the QWebEngineView.
        coords: List of (lat, lon) tuples.
        """
        if not FOLIUM_AVAILABLE:
            return

        # Default center (0, 0) or center of points
        if coords and len(coords) > 0:
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lon = sum(c[1] for c in coords) / len(coords)
            start_loc = [avg_lat, avg_lon]
            zoom = 18
        else:
            start_loc = [0, 0]
            zoom = 2

        m = folium.Map(location=start_loc, zoom_start=zoom)

        # Add Google Maps Layers
        folium.TileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', attr='Google', name='Google Maps (Roads)').add_to(m)
        folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Maps (Satellite)').add_to(m)

        folium.LayerControl().add_to(m)

        # Save map to bytes and display
        data = io.BytesIO()
        m.save(data, close_file=False)
        self.browser.setHtml(data.getvalue().decode())