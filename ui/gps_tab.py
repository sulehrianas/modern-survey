"""
UI for the GPS Surveying / Coordinate Conversion tab.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QTableWidget, QPushButton,
    QLabel, QHeaderView, QLineEdit, QMessageBox, QTableWidgetItem, QFileDialog,
    QScrollArea
)
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtCore import Qt, QUrl
import pandas as pd
import tempfile
import os

from data_services.csv_handler import import_csv_to_dataframe, export_dataframe_to_csv
from data_services.kml_exporter import export_to_kml
from core.coordinate_converter import convert_coords, get_utm_epsg_code

class GpsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Initializes the user interface for the tab."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)
        content_widget = QWidget()
        scroll.setWidget(content_widget)

        main_layout = QHBoxLayout(content_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Left Side: Data Table ---
        left_layout = QVBoxLayout()
        data_group = QGroupBox("Coordinate Data")
        data_layout = QVBoxLayout(data_group)
        self.table = QTableWidget()
        self.setup_table()
        data_layout.addWidget(self.table)

        row_mgmt_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Add Row")
        self.remove_row_button = QPushButton("Remove Selected Row")
        row_mgmt_layout.addStretch()
        row_mgmt_layout.addWidget(self.add_row_button)
        row_mgmt_layout.addWidget(self.remove_row_button)
        data_layout.addLayout(row_mgmt_layout)
        left_layout.addWidget(data_group)

        # --- Right Side: Controls ---
        right_layout = QVBoxLayout()
        controls_group = QGroupBox("Controls & Conversion")
        controls_group.setFixedWidth(300)
        controls_layout = QVBoxLayout(controls_group)

        # CRS Selection
        crs_layout = QHBoxLayout()
        self.from_crs_input = QLineEdit("4326")
        self.to_crs_input = QLineEdit("32632")
        crs_layout.addWidget(QLabel("From EPSG:"))
        crs_layout.addWidget(self.from_crs_input)
        crs_layout.addWidget(QLabel("To EPSG:"))
        crs_layout.addWidget(self.to_crs_input)
        
        self.swap_crs_button = QPushButton("⇄")
        self.swap_crs_button.setToolTip("Swap Input and Output CRS")
        self.swap_crs_button.setFixedWidth(30)
        self.swap_crs_button.clicked.connect(self.handle_swap_crs)
        crs_layout.addWidget(self.swap_crs_button)
        
        controls_layout.addLayout(crs_layout)
        
        # Helper button for UTM
        self.utm_helper_button = QPushButton("Find UTM Zone from Longitude")
        controls_layout.addWidget(self.utm_helper_button)
        controls_layout.addSpacing(20)

        # Action Buttons
        self.import_csv_button = self.create_styled_button("Import from CSV", "#007BFF")
        self.convert_button = self.create_styled_button("Convert Coordinates", "#28A745")
        self.clear_button = self.create_styled_button("Clear All", "#FFC107", text_color="#000000")
        controls_layout.addWidget(self.import_csv_button)
        controls_layout.addWidget(self.convert_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addSpacing(20)

        # Export Buttons
        export_label = QLabel("Export Results")
        export_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(export_label)
        self.export_csv_button = self.create_styled_button("Export to CSV", "#6C757D")
        self.export_kml_button = self.create_styled_button("Export to KML", "#FFC107", text_color="#000000")
        controls_layout.addWidget(self.export_csv_button)
        controls_layout.addWidget(self.export_kml_button)
        
        # New Button for Internet Link
        self.view_online_button = self.create_styled_button("View All on Google Earth", "#4285F4")
        controls_layout.addWidget(self.view_online_button)

        controls_layout.addStretch()
        right_layout.addWidget(controls_group)

        # --- Assemble Main Layout ---
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout)

        # --- Connect Signals ---
        self.add_row_button.clicked.connect(lambda: self.table.insertRow(self.table.rowCount()))
        self.remove_row_button.clicked.connect(self.remove_row)
        self.clear_button.clicked.connect(self.handle_clear)
        self.convert_button.clicked.connect(self.handle_convert)
        self.import_csv_button.clicked.connect(self.handle_import_csv)
        self.export_csv_button.clicked.connect(self.handle_export_csv)
        self.export_kml_button.clicked.connect(self.handle_export_kml)
        self.view_online_button.clicked.connect(self.handle_view_online)
        self.utm_helper_button.clicked.connect(self.handle_utm_helper)

    def setup_table(self):
        """Configures the properties of the data table."""
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Point Name", "Input Easting (X) / Lon", "Input Northing (Y) / Lat", "Input Elevation (Z)",
            "Output Easting (X) / Lon", "Output Northing (Y) / Lat", "Output Elevation (Z)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setRowCount(10)

    def handle_convert(self):
        """Performs the coordinate conversion."""
        try:
            from_epsg = int(self.from_crs_input.text())
            to_epsg = int(self.to_crs_input.text())
            
            points_to_convert = []
            rows_to_process = []
            for row in range(self.table.rowCount()):
                x_item = self.table.item(row, 1)
                y_item = self.table.item(row, 2)
                if x_item and x_item.text() and y_item and y_item.text():
                    x = float(x_item.text())
                    y = float(y_item.text())
                    z_item = self.table.item(row, 3)
                    z = float(z_item.text()) if z_item and z_item.text() else 0.0
                    points_to_convert.append((x, y, z))
                    rows_to_process.append(row)

            if not points_to_convert:
                QMessageBox.warning(self, "No Data", "No points were found to convert.")
                return

            converted_points = convert_coords(points_to_convert, from_epsg, to_epsg)

            for i, row_idx in enumerate(rows_to_process):
                x_out, y_out, z_out = converted_points[i]
                self.table.setItem(row_idx, 4, QTableWidgetItem(f"{x_out:.6f}"))
                self.table.setItem(row_idx, 5, QTableWidgetItem(f"{y_out:.6f}"))
                self.table.setItem(row_idx, 6, QTableWidgetItem(f"{z_out:.6f}"))

            QMessageBox.information(self, "Success", f"Successfully converted {len(converted_points)} points.")

        except ValueError as e:
            QMessageBox.critical(self, "Input Error", f"Invalid EPSG code or coordinate value. Please check your inputs.\n\nDetails: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", f"An error occurred during conversion: {e}")

    def handle_swap_crs(self):
        """Swaps the From and To EPSG codes."""
        from_val = self.from_crs_input.text()
        to_val = self.to_crs_input.text()
        self.from_crs_input.setText(to_val)
        self.to_crs_input.setText(from_val)

    def handle_utm_helper(self):
        from PyQt6.QtWidgets import QInputDialog
        lon, ok = QInputDialog.getDouble(self, "UTM Helper", "Enter a Longitude to find its UTM Zone EPSG:", -100.0, -180, 180, 6)
        if ok:
            try:
                epsg = get_utm_epsg_code(lon)
                self.to_crs_input.setText(str(epsg))
                QMessageBox.information(self, "UTM Zone Found", f"The EPSG code for longitude {lon}° is {epsg}.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def get_table_data_as_dataframe(self):
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = []
        for row in range(self.table.rowCount()):
            first_item = self.table.item(row, 0)
            if not (first_item and first_item.text()): continue
            row_data = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(self.table.columnCount())]
            data.append(row_data)
        return pd.DataFrame(data, columns=headers)

    def populate_table_from_dataframe(self, df):
        self.table.clearContents()
        self.table.setRowCount(len(df))
        
        # Define mapping for standard GPS headers to Table Columns
        # UI Columns: 0: Name, 1: X/Lon, 2: Y/Lat, 3: Z
        col_map = {
            0: ['Point', 'Pt', 'Name', 'ID', 'P', 'Point Name', 'PtID'],
            1: ['Easting', 'East', 'E', 'Longitude', 'Lon', 'Long', 'Input Easting (X) / Lon'],
            2: ['Northing', 'North', 'N', 'Latitude', 'Lat', 'Input Northing (Y) / Lat'],
            3: ['Elevation', 'Elev', 'Z', 'Height', 'H', 'Ellipsoid Height', 'Input Elevation (Z)']
        }

        # Normalize DF columns for easier matching
        df.columns = [str(c).strip() for c in df.columns]

        for row_idx, row_data in df.iterrows():
            for table_col_idx, aliases in col_map.items():
                val = ""
                for alias in aliases:
                    # Case-insensitive match
                    match = next((col for col in df.columns if col.lower() == alias.lower()), None)
                    if match:
                        raw_val = row_data[match]
                        if pd.notna(raw_val):
                            val = str(raw_val)
                        break
                
                if val:
                    self.table.setItem(row_idx, table_col_idx, QTableWidgetItem(val))

    def handle_import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not file_path: return
        df = import_csv_to_dataframe(file_path)
        if df is not None:
            self.populate_table_from_dataframe(df)
            QMessageBox.information(self, "Success", f"Successfully imported {len(df)} rows.")
        else:
            QMessageBox.critical(self, "Import Error", "Failed to read data from CSV file.")

    def handle_export_csv(self):
        df = self.get_table_data_as_dataframe()
        if df.empty:
            QMessageBox.warning(self, "Export Error", "There is no data to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "", "CSV Files (*.csv)")
        if not file_path: return
        if export_dataframe_to_csv(df, file_path):
            QMessageBox.information(self, "Success", f"Data successfully exported to {file_path}")
        else:
            QMessageBox.critical(self, "Export Error", "Failed to export data to CSV.")

    def handle_export_kml(self):
        try:
            from_epsg = int(self.from_crs_input.text())
            points_to_convert = []
            for row in range(self.table.rowCount()):
                name_item = self.table.item(row, 0)
                x_item = self.table.item(row, 1)
                y_item = self.table.item(row, 2)
                if all(item and item.text() for item in [name_item, x_item, y_item]):
                    z_item = self.table.item(row, 3)
                    z = float(z_item.text()) if z_item and z_item.text() else None
                    points_to_convert.append((name_item.text(), float(x_item.text()), float(y_item.text()), z))
            
            if not points_to_convert:
                QMessageBox.warning(self, "Export Error", "No valid points found to export.")
                return

            # Ensure points are in WGS84 (EPSG:4326) for KML
            if from_epsg != 4326:
                coords_only = [(p[1], p[2], p[3] if p[3] is not None else 0) for p in points_to_convert]
                wgs84_coords = convert_coords(coords_only, from_epsg, 4326)
                kml_points = [(points_to_convert[i][0], lon, lat, elev if elev is not None else 0) for i, (lon, lat, elev) in enumerate(wgs84_coords)]
            else:
                kml_points = [(p[0], p[1], p[2], p[3]) for p in points_to_convert]

            file_path, _ = QFileDialog.getSaveFileName(self, "Export to KML", "", "KML Files (*.kml)")
            if not file_path: return
            export_to_kml(file_path, kml_points)
            QMessageBox.information(self, "Success", f"KML file successfully saved to {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate KML file: {e}")

    def handle_view_online(self):
        """Generates a temporary KML of all points and opens it."""
        try:
            from_epsg = int(self.from_crs_input.text())
            points_to_convert = []
            
            # Gather all points
            for row in range(self.table.rowCount()):
                name_item = self.table.item(row, 0)
                x_item = self.table.item(row, 1)
                y_item = self.table.item(row, 2)
                
                if x_item and x_item.text() and y_item and y_item.text():
                    name = name_item.text() if name_item and name_item.text() else f"Point {row+1}"
                    try:
                        x = float(x_item.text())
                        y = float(y_item.text())
                        z_item = self.table.item(row, 3)
                        z = float(z_item.text()) if z_item and z_item.text() else 0.0
                        points_to_convert.append((name, x, y, z))
                    except ValueError:
                        continue

            if not points_to_convert:
                QMessageBox.warning(self, "No Data", "No valid points found to view.")
                return
            
            # Convert to WGS84
            coords_only = [(p[1], p[2], p[3]) for p in points_to_convert]
            wgs84_coords = convert_coords(coords_only, from_epsg, 4326)
            
            # Prepare KML data
            kml_points = []
            for i, (lon, lat, elev) in enumerate(wgs84_coords):
                name = points_to_convert[i][0]
                kml_points.append((name, lon, lat, elev))

            # Create temporary file
            fd, temp_path = tempfile.mkstemp(suffix='.kml', prefix='survey_view_')
            os.close(fd)
            
            export_to_kml(temp_path, kml_points)
            
            QDesktopServices.openUrl(QUrl.fromLocalFile(temp_path))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open map: {e}")

    def handle_clear(self):
        self.table.clearContents()
        self.table.setRowCount(10)

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0: self.table.removeRow(current_row)
        else: QMessageBox.information(self, "Information", "Please select a row to remove.")

    def create_styled_button(self, text, bg_color, text_color="#FFFFFF"):
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{ background-color: {bg_color}; color: {text_color}; border-radius: 5px;
                          padding: 10px; font-size: 14px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {self.darken_color(bg_color)}; }}""")
        return button

    def darken_color(self, color_str, factor=0.85):
        color = QColor(color_str)
        return color.darker(int(100 / factor)).name()