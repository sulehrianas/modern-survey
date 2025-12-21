"""
UI for the Theodolite Surveying tab.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QTableWidget,
    QPushButton,
    QLabel,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QComboBox,
    QDoubleSpinBox
)
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
import numpy as np
import pandas as pd
import math

from .plot_widget import PlotWidget
from core.calculations import dms_to_dd, dd_to_dms, calculate_lat_dep, calculate_coordinates
from core.adjustments import adjust_traverse_bowditch
from data_services.csv_handler import import_csv_to_dataframe, export_dataframe_to_csv
from data_services.pdf_reporter import generate_theodolite_report
from data_services.kml_exporter import export_to_kml
from core.coordinate_converter import convert_to_global

class TheodoliteTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Initializes the user interface for the tab."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Left Side: Data Input & Plot ---
        left_layout = QVBoxLayout()

        # Initial Conditions Group
        init_cond_group = QGroupBox("Initial Conditions")
        init_cond_layout = QHBoxLayout(init_cond_group)
        
        init_cond_layout.addWidget(QLabel("Start Northing:"))
        self.start_northing = QDoubleSpinBox()
        self.start_northing.setRange(0, 999999.9999)
        self.start_northing.setValue(1000.0)
        init_cond_layout.addWidget(self.start_northing)

        init_cond_layout.addWidget(QLabel("Start Easting:"))
        self.start_easting = QDoubleSpinBox()
        self.start_easting.setRange(0, 999999.9999)
        self.start_easting.setValue(5000.0)
        init_cond_layout.addWidget(self.start_easting)

        init_cond_layout.addWidget(QLabel("Initial Azimuth (DD.MMSS):"))
        self.initial_azimuth = QLineEdit("120.3045")
        init_cond_layout.addWidget(self.initial_azimuth)

        init_cond_layout.addWidget(QLabel("Stadia Constant (k):"))
        self.stadia_constant = QDoubleSpinBox()
        self.stadia_constant.setRange(1, 1000)
        self.stadia_constant.setValue(100)
        init_cond_layout.addWidget(self.stadia_constant)
        init_cond_layout.addStretch()
        left_layout.addWidget(init_cond_group)

        # Data Table Group
        data_group = QGroupBox("Traverse Data")
        data_layout = QVBoxLayout(data_group)
        self.table = QTableWidget()
        self.setup_table()
        data_layout.addWidget(self.table)

        # Row Management Buttons
        row_mgmt_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Add Row")
        self.remove_row_button = QPushButton("Remove Selected Row")
        row_mgmt_layout.addStretch()
        row_mgmt_layout.addWidget(self.add_row_button)
        row_mgmt_layout.addWidget(self.remove_row_button)
        data_layout.addLayout(row_mgmt_layout)
        left_layout.addWidget(data_group)

        # Plot Group
        self.plot_group = QGroupBox("Traverse Plot")
        plot_layout = QVBoxLayout(self.plot_group)
        self.plot_widget = PlotWidget()
        plot_layout.addWidget(self.plot_widget)
        left_layout.addWidget(self.plot_group)
        self.plot_group.setVisible(False) # Hidden by default

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
        self.update_angle_headers() # Call it here after initialization
        controls_layout.addWidget(self.angle_format_combo)
        controls_layout.addSpacing(10)

        controls_layout.addWidget(QLabel("Traverse Type:"))
        self.traverse_type_combo = QComboBox()
        self.traverse_type_combo.addItems(["Closed-Loop", "Open"])
        controls_layout.addWidget(self.traverse_type_combo)

        controls_layout.addWidget(QLabel("Measured Angles:"))
        self.angle_type_combo = QComboBox()
        self.angle_type_combo.addItems(["Interior (Angles-to-the-Right)", "Exterior Angles"])
        controls_layout.addWidget(self.angle_type_combo)
        controls_layout.addSpacing(20)

        # Action Buttons
        self.import_csv_button = self.create_styled_button("Import from CSV", "#007BFF")
        self.calculate_button = self.create_styled_button("Calculate Traverse", "#28A745")
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

        # Results Display
        controls_layout.addSpacing(20)
        self.results_label = QLabel("Results will be shown here.")
        self.results_label.setWordWrap(True)
        controls_layout.addWidget(QLabel("<b>Calculation Results:</b>"))
        controls_layout.addWidget(self.results_label)
        controls_layout.addStretch()
        right_layout.addWidget(controls_group)

        # --- Assemble Main Layout ---
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout)

        # --- Connect Signals ---
        self.calculate_button.clicked.connect(self.handle_calculate)
        self.table.itemChanged.connect(self.handle_table_item_changed)
        self.add_row_button.clicked.connect(self.add_row)
        self.remove_row_button.clicked.connect(self.remove_row)
        self.clear_button.clicked.connect(self.handle_clear)
        self.import_csv_button.clicked.connect(self.handle_import_csv)
        self.export_csv_button.clicked.connect(self.handle_export_csv)
        self.export_pdf_button.clicked.connect(self.handle_export_pdf)
        self.export_kml_button.clicked.connect(self.handle_export_kml)

    def setup_table(self):
        """Configures the properties of the data input table."""
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Line",
            "Horizontal Angle", "Upper Stadia", "Lower Stadia",
            "Vert. Angle", 
            "Distance (m)", 
            "Azimuth", "Latitude", "Departure", 
            "Adj. Easting", "Adj. Northing"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setRowCount(10)

        # --- Add attributes to store calculation results for reports ---
        self.calculation_summary = {}
        self.final_coords = []

    def update_angle_headers(self):
        """Updates the table headers to reflect the selected angle format."""
        angle_format = self.angle_format_combo.currentText()
        self.table.horizontalHeaderItem(1).setText(f"Horizontal Angle ({angle_format})")
        self.table.horizontalHeaderItem(4).setText(f"Vertical Angle ({angle_format})")

    def read_input_data_from_table(self):
        """Reads and validates data from the QTableWidget."""
        lines, angles, distances = [], [], []
        angle_format = self.angle_format_combo.currentText()

        for row in range(self.table.rowCount()):
            line_item = self.table.item(row, 0)
            angle_item = self.table.item(row, 1)
            dist_item = self.table.item(row, 5)

            if not (line_item and line_item.text() and angle_item and angle_item.text() and dist_item and dist_item.text()):
                break

            lines.append(line_item.text().strip())
            
            angle_str = angle_item.text().strip()
            if angle_format == "DD.MMSS":
                angles.append(dms_to_dd(angle_str))
            else: # Decimal Degrees
                angles.append(float(angle_str))

            distances.append(float(dist_item.text().strip()))

        if not lines:
            raise ValueError("No data found in the table. Please enter or import data.")
        return lines, np.array(angles), np.array(distances)

    def handle_calculate(self):
        """Performs the full theodolite traverse calculation and adjustment."""
        try:
            # 1. Read data and initial conditions
            lines, measured_angles, distances = self.read_input_data_from_table()
            start_northing = self.start_northing.value()
            start_easting = self.start_easting.value()
            initial_azimuth_dd = dms_to_dd(self.initial_azimuth.text())
            
            traverse_type = self.traverse_type_combo.currentText()
            angle_type = self.angle_type_combo.currentText()
            num_stations = len(lines)

            # 2. Angular Misclosure and Adjustment (for Closed-Loop)
            angular_misclosure = 0
            corrected_angles = measured_angles.copy()

            if traverse_type == "Closed-Loop":
                sum_measured_angles = np.sum(measured_angles)
                if angle_type == "Interior (Angles-to-the-Right)":
                    theoretical_sum = (num_stations - 2) * 180
                else: # Exterior Angles
                    theoretical_sum = (num_stations + 2) * 180
                
                angular_misclosure = sum_measured_angles - theoretical_sum
                correction_per_angle = -angular_misclosure / num_stations
                corrected_angles += correction_per_angle

            # 3. Calculate Azimuths
            azimuths = []
            current_azimuth = initial_azimuth_dd

            for i in range(num_stations):
                azimuths.append(current_azimuth)
                back_azimuth = (current_azimuth + 180) % 360
                
                if angle_type == "Interior (Angles-to-the-Right)":
                    next_azimuth = (back_azimuth + corrected_angles[i]) % 360
                else: # Exterior Angles
                    next_azimuth = (back_azimuth - corrected_angles[i]) % 360
                
                current_azimuth = next_azimuth

            # 4. Calculate Latitudes, Departures, and Linear Misclosure
            latitudes, departures = calculate_lat_dep(np.array(azimuths), distances)
            
            lat_misclosure = np.sum(latitudes)
            dep_misclosure = np.sum(departures)
            
            # 5. Adjust Traverse (Bowditch)
            adj_latitudes, adj_departures, _, _ = adjust_traverse_bowditch(distances, latitudes, departures)

            # 6. Calculate Final Coordinates
            final_coords = calculate_coordinates(start_northing, start_easting, adj_latitudes, adj_departures)

            # 7. Populate results back into the table
            self.populate_results_in_table(azimuths, latitudes, departures, final_coords)

            # 8. Display summary results
            results_text = f"Angular Misclosure: {dd_to_dms(angular_misclosure)}\n"
            results_text += f"Latitude Misclosure: {lat_misclosure:.4f} m\n"
            results_text += f"Departure Misclosure: {dep_misclosure:.4f} m\n"
            linear_misclosure = math.sqrt(lat_misclosure**2 + dep_misclosure**2)
            results_text += f"Linear Misclosure: {linear_misclosure:.4f} m\n"
            precision = np.sum(distances) / linear_misclosure if linear_misclosure != 0 else float('inf')
            results_text += f"Precision: 1 in {precision:,.0f}"
            self.results_label.setText(results_text)

            # Store summary and coordinates for exporting
            self.calculation_summary = {
                "Traverse Type": traverse_type,
                "Angle Type": angle_type,
                "Angular Misclosure": dd_to_dms(angular_misclosure),
                "Latitude Misclosure": f"{lat_misclosure:.4f} m",
                "Departure Misclosure": f"{dep_misclosure:.4f} m",
                "Linear Misclosure": f"{linear_misclosure:.4f} m",
                "Precision": f"1 in {precision:,.0f}"
            }
            self.final_coords = final_coords

            QMessageBox.information(self, "Calculation Complete", "Theodolite traverse calculation finished successfully.")

        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Input Error", f"Please check your data. A number might be missing or invalid.\n\nDetails: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def populate_results_in_table(self, azimuths, lats, deps, coords):
        """Writes the calculated values into the table's output columns."""
        for i in range(len(azimuths)):
            self.table.setItem(i, 6, QTableWidgetItem(dd_to_dms(azimuths[i])))
            self.table.setItem(i, 7, QTableWidgetItem(f"{lats[i]:.4f}"))
            self.table.setItem(i, 8, QTableWidgetItem(f"{deps[i]:.4f}"))
            self.table.setItem(i, 9, QTableWidgetItem(f"{coords[i+1][0]:.4f}")) # Easting
            self.table.setItem(i, 10, QTableWidgetItem(f"{coords[i+1][1]:.4f}")) # Northing

    def handle_table_item_changed(self, item):
        """
        Automatically calculates the horizontal distance when stadia readings are entered.
        """
        # Columns: 2=Upper, 3=Lower, 4=Vert. Angle
        if item.column() not in [2, 3, 4]:
            return

        row = item.row()
        try:
            upper_item = self.table.item(row, 2)
            lower_item = self.table.item(row, 3)

            if not (upper_item and upper_item.text() and lower_item and lower_item.text()):
                return # Not enough data

            upper = float(upper_item.text())
            lower = float(lower_item.text())
            
            vert_angle_item = self.table.item(row, 4)
            vert_angle_str = vert_angle_item.text() if vert_angle_item and vert_angle_item.text() else "0.0"

            if self.angle_format_combo.currentText() == "DD.MMSS":
                vert_angle_dd = dms_to_dd(vert_angle_str)
            else: # Decimal Degrees
                vert_angle_dd = float(vert_angle_str)

            k = self.stadia_constant.value()
            stadia_interval = upper - lower
            
            # The formula requires the vertical angle in radians for math.cos
            distance = k * stadia_interval * (math.cos(math.radians(vert_angle_dd))**2)

            self.table.setItem(row, 5, QTableWidgetItem(f"{distance:.4f}"))
        except (ValueError, TypeError):
            return # Ignore errors from invalid text during input

    def get_table_data_as_dataframe(self):
        """Reads all data from the QTableWidget into a pandas DataFrame."""
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            first_item = self.table.item(row, 0)
            if not (first_item and first_item.text()):
                break # Stop at first empty row
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
        if generate_theodolite_report(self.calculation_summary, df, file_path):
            QMessageBox.information(self, "Success", f"Report successfully saved to {file_path}")
        else:
            QMessageBox.critical(self, "Export Error", "Failed to generate PDF report.")

    def handle_export_kml(self):
        if not self.final_coords:
            QMessageBox.warning(self, "Export Error", "Please run a calculation to generate coordinates first.")
            return

        from PyQt6.QtWidgets import QInputDialog
        epsg_code, ok = QInputDialog.getInt(self, "Coordinate System", "Enter EPSG code for your UTM Zone:", 32632)
        if not ok: return

        try:
            # The coordinates are (Easting, Northing), which is (x, y)
            local_points = [(coord[0], coord[1]) for coord in self.final_coords]
            
            # convert_to_global returns (lon, lat)
            global_points = convert_to_global(local_points, epsg_code)

            # Prepare points for KML exporter: (name, lon, lat)
            kml_points = []
            for i, (lon, lat) in enumerate(global_points):
                # Use the 'Line' name from the table to derive the point name
                line_item = self.table.item(i-1, 0) if i > 0 else None # i-1 because final_coords has one more point (start)
                point_name = line_item.text() if line_item and line_item.text() else f"Point {i}"
                if i == 0: point_name = "Start Point"
                kml_points.append((point_name, lon, lat))

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

    def create_styled_button(self, text, bg_color, text_color="#FFFFFF"):
        """Factory function to create a styled QPushButton."""
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(bg_color)};
            }}
        """)
        return button

    def darken_color(self, color_str, factor=0.85):
        """Darkens a hex color string."""
        color = QColor(color_str)
        return color.darker(int(100 / factor)).name()

    def add_row(self):
        """Adds a new empty row to the end of the table."""
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        """Removes the currently selected row from the table."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
        else:
            QMessageBox.information(self, "Information", "Please select a row to remove.")

    def handle_clear(self):
        """Clears all input fields and results."""
        self.table.clearContents()
        self.table.setRowCount(10)
        self.results_label.setText("Results will be shown here.")
        self.plot_widget.clear_plot()