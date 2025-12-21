"""
UI for the Trigonometric Leveling tab.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QTableWidget, QPushButton,
    QLabel, QHeaderView, QLineEdit, QMessageBox, QComboBox, QDoubleSpinBox,
    QTableWidgetItem, QFileDialog, QInputDialog
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
import numpy as np
import pandas as pd
import math

from .plot_widget import PlotWidget
from core.calculations import dms_to_dd, dd_to_dms, calculate_lat_dep, calculate_coordinates
from data_services.csv_handler import import_csv_to_dataframe, export_dataframe_to_csv
from data_services.pdf_reporter import generate_trig_leveling_report
from data_services.kml_exporter import export_to_kml
from core.coordinate_converter import convert_to_global

class TrigLevelingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.calculation_summary = {}
        self.final_points_3d = [] # Store as (Easting, Northing, Elevation)
        self.setup_ui()

    def setup_ui(self):
        """Initializes the user interface for the tab."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Left Side: Data Input ---
        left_layout = QVBoxLayout()

        # Station Setup Group
        station_setup_group = QGroupBox("Instrument Station Setup")
        station_setup_layout = QHBoxLayout(station_setup_group)
        station_setup_layout.addWidget(QLabel("Northing:"))
        self.inst_northing = QDoubleSpinBox()
        self.inst_northing.setRange(0, 9999999.999); self.inst_northing.setValue(1000.0)
        station_setup_layout.addWidget(self.inst_northing)
        station_setup_layout.addWidget(QLabel("Easting:"))
        self.inst_easting = QDoubleSpinBox()
        self.inst_easting.setRange(0, 9999999.999); self.inst_easting.setValue(5000.0)
        station_setup_layout.addWidget(self.inst_easting)
        station_setup_layout.addWidget(QLabel("Elevation:"))
        self.inst_elevation = QDoubleSpinBox()
        self.inst_elevation.setRange(-999, 99999.999); self.inst_elevation.setValue(100.0)
        station_setup_layout.addWidget(self.inst_elevation)
        station_setup_layout.addWidget(QLabel("Instrument Height:"))
        self.inst_height = QDoubleSpinBox()
        self.inst_height.setRange(0, 10.0); self.inst_height.setValue(1.5)
        station_setup_layout.addWidget(self.inst_height)
        station_setup_layout.addStretch()
        left_layout.addWidget(station_setup_group)

        # Data Table Group
        data_group = QGroupBox("Observations")
        data_layout = QVBoxLayout(data_group)
        self.table = QTableWidget()
        data_layout.addWidget(self.table)
        
        row_mgmt_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Add Row")
        self.remove_row_button = QPushButton("Remove Selected Row")
        row_mgmt_layout.addStretch()
        row_mgmt_layout.addWidget(self.add_row_button)
        row_mgmt_layout.addWidget(self.remove_row_button)
        data_layout.addLayout(row_mgmt_layout)
        left_layout.addWidget(data_group)

        # --- Right Side: Controls & Results ---
        right_layout = QVBoxLayout()
        controls_group = QGroupBox("Controls & Results")
        controls_group.setFixedWidth(250)
        controls_layout = QVBoxLayout(controls_group)

        # Angle Input Options
        controls_layout.addWidget(QLabel("Angle Input Format:"))
        self.angle_format_combo = QComboBox()
        self.angle_format_combo.addItems(["DD.MMSS", "Decimal Degrees"])
        self.angle_format_combo.currentIndexChanged.connect(self.update_angle_headers)
        controls_layout.addWidget(self.angle_format_combo)
        controls_layout.addSpacing(20)

        # Action Buttons
        self.import_csv_button = self.create_styled_button("Import from CSV", "#007BFF")
        self.calculate_button = self.create_styled_button("Calculate Elevations", "#28A745")
        self.clear_button = self.create_styled_button("Clear All", "#FFC107", text_color="#000000")
        controls_layout.addWidget(self.import_csv_button)
        controls_layout.addWidget(self.calculate_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addSpacing(20)

        # Export Buttons
        export_label = QLabel("Export Results")
        export_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(export_label)
        self.export_csv_button = self.create_styled_button("Export to CSV", "#6C757D")
        self.export_pdf_button = self.create_styled_button("Export Report (PDF)", "#DC3545")
        self.export_kml_button = self.create_styled_button("Export to KML", "#FFC107", text_color="#000000")
        controls_layout.addWidget(self.export_csv_button)
        controls_layout.addWidget(self.export_pdf_button)
        controls_layout.addWidget(self.export_kml_button)

        controls_layout.addStretch()
        right_layout.addWidget(controls_group)

        # --- Assemble Main Layout ---
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout)

        # --- Connect Signals ---
        self.add_row_button.clicked.connect(self.add_row)
        self.remove_row_button.clicked.connect(self.remove_row)
        self.clear_button.clicked.connect(self.handle_clear)
        self.calculate_button.clicked.connect(self.handle_calculate)
        self.import_csv_button.clicked.connect(self.handle_import_csv)
        self.export_csv_button.clicked.connect(self.handle_export_csv)
        self.export_pdf_button.clicked.connect(self.handle_export_pdf)
        self.export_kml_button.clicked.connect(self.handle_export_kml)

        # Setup table now that all widgets are initialized
        self.setup_table()

    def setup_table(self):
        """Configures the properties of the data input table."""
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Target Name", "Horiz. Distance (m)", "Vert. Angle",
            "Target Height (m)", "Azimuth",
            "Δ Elevation (m)", "Target Northing", "Target Easting", "Target Elevation"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setRowCount(10)
        self.update_angle_headers() # Set initial headers

    def update_angle_headers(self):
        """Updates the table headers to reflect the selected angle format."""
        angle_format = self.angle_format_combo.currentText()
        self.table.horizontalHeaderItem(2).setText(f"Vert. Angle ({angle_format})")
        self.table.horizontalHeaderItem(4).setText(f"Azimuth ({angle_format})")

    def handle_calculate(self):
        """Performs the trigonometric leveling calculation."""
        try:
            inst_elev = self.inst_elevation.value()
            inst_height = self.inst_height.value()
            inst_north = self.inst_northing.value()
            inst_east = self.inst_easting.value()
            angle_format = self.angle_format_combo.currentText()
            self.final_points_3d = [] # Clear previous results

            for row in range(self.table.rowCount()):
                # Read inputs from the table row
                dist_item = self.table.item(row, 1)
                angle_item = self.table.item(row, 2)
                target_h_item = self.table.item(row, 3)
                azimuth_item = self.table.item(row, 4)

                if not all(item and item.text() for item in [dist_item, angle_item, target_h_item, azimuth_item]):
                    break # Stop at first empty row

                horiz_dist = float(dist_item.text())
                target_height = float(target_h_item.text())
                
                vert_angle_str = angle_item.text()
                azimuth_str = azimuth_item.text()
                if angle_format == "DD.MMSS":
                    vert_angle_dd = dms_to_dd(vert_angle_str)
                    azimuth_dd = dms_to_dd(azimuth_str)
                else: # Decimal Degrees
                    vert_angle_dd = float(vert_angle_str)
                    azimuth_dd = float(azimuth_str)

                # Calculate elevation difference
                delta_elev = (horiz_dist * math.tan(math.radians(vert_angle_dd))) + inst_height - target_height
                target_elev = inst_elev + delta_elev

                # Calculate target coordinates
                lat, dep = calculate_lat_dep([azimuth_dd], [horiz_dist])
                target_north = inst_north + lat[0]
                target_east = inst_east + dep[0]

                # Populate results in the table
                self.table.setItem(row, 5, QTableWidgetItem(f"{delta_elev:.4f}"))
                self.table.setItem(row, 6, QTableWidgetItem(f"{target_north:.4f}"))
                self.table.setItem(row, 7, QTableWidgetItem(f"{target_east:.4f}"))
                self.table.setItem(row, 8, QTableWidgetItem(f"{target_elev:.4f}"))

                # Store for exporting
                self.final_points_3d.append((target_east, target_north, target_elev))

            # Store summary for PDF report
            self.calculation_summary = {
                "Instrument Northing": f"{inst_north:.4f}",
                "Instrument Easting": f"{inst_east:.4f}",
                "Instrument Elevation": f"{inst_elev:.4f}",
                "Instrument Height": f"{inst_height:.4f}",
            }
            QMessageBox.information(self, "Success", "Calculation complete.")

        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Input Error", f"Please check your data. A number might be missing or invalid.\n\nDetails: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def get_table_data_as_dataframe(self):
        """Reads all data from the QTableWidget into a pandas DataFrame."""
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            first_item = self.table.item(row, 0)
            if not (first_item and first_item.text()):
                break
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item and item.text() else "")
            data.append(row_data)
        return pd.DataFrame(data, columns=headers)

    def populate_table_from_dataframe(self, df):
        """Fills the table with data from a pandas DataFrame."""
        self.table.clearContents()
        self.table.setRowCount(len(df))
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        for row_idx, row_data in df.iterrows():
            for col_idx, col_name in enumerate(headers):
                if col_name in df.columns:
                    item_data = str(row_data.get(col_name, ""))
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(item_data))

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

    def handle_export_pdf(self):
        if not self.calculation_summary:
            QMessageBox.warning(self, "Export Error", "Please run a calculation before exporting a report.")
            return
        df = self.get_table_data_as_dataframe()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Report to PDF", "", "PDF Files (*.pdf)")
        if not file_path: return
        if generate_trig_leveling_report(self.calculation_summary, df, file_path):
            QMessageBox.information(self, "Success", f"Report successfully saved to {file_path}")
        else:
            QMessageBox.critical(self, "Export Error", "Failed to generate PDF report.")

    def handle_export_kml(self):
        if not self.final_points_3d:
            QMessageBox.warning(self, "Export Error", "Please run a calculation to generate coordinates first.")
            return
        epsg_code, ok = QInputDialog.getInt(self, "Coordinate System", "Enter EPSG code for your UTM Zone:", 32632)
        if not ok: return
        try:
            local_points = [(p[0], p[1]) for p in self.final_points_3d]
            global_points = convert_to_global(local_points, epsg_code)
            kml_points = []
            for i, (lon, lat) in enumerate(global_points):
                point_name = self.table.item(i, 0).text() if self.table.item(i, 0) and self.table.item(i, 0).text() else f"Point {i+1}"
                elev = self.final_points_3d[i][2]
                kml_points.append((point_name, lon, lat, elev))
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", f"Could not convert coordinates: {e}")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export to KML", "", "KML Files (*.kml)")
        if not file_path: return
        try:
            export_to_kml(file_path, kml_points)
            QMessageBox.information(self, "Success", f"KML file successfully saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate KML file: {e}")

    def add_row(self): self.table.insertRow(self.table.rowCount())
    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0: self.table.removeRow(current_row)
        else: QMessageBox.information(self, "Information", "Please select a row to remove.")

    def handle_clear(self):
        self.table.clearContents()
        self.table.setRowCount(10)
        self.calculation_summary = {}
        self.final_points_3d = []

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