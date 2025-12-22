"""UI for the Compass Traversing tab"""
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
    QGroupBox,
    QTableWidget,
    QPushButton,
    QComboBox,
    QHeaderView,
    QLabel,
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
    QInputDialog,
    QScrollArea,
)
from PyQt6.QtCore import Qt
import numpy as np

# Import data service functions
from data_services.csv_handler import import_csv_to_dataframe, export_dataframe_to_csv
from data_services.pdf_reporter import generate_traverse_report
from data_services.kml_exporter import export_to_kml

# Import calculation and adjustment functions
from core.calculations import dms_to_dd, calculate_lat_dep, calculate_coordinates
from core.adjustments import adjust_traverse_bowditch
from core.coordinate_converter import convert_to_global
import pandas as pd
from .plot_widget import PlotWidget

class CompassTab(QWidget):
    def __init__(self):
        super().__init__()

        # --- Scroll Area Setup ---
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)
        content_widget = QWidget()
        scroll.setWidget(content_widget)

        # --- Main Layout ---
        main_layout = QHBoxLayout(content_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Left Side: Data Input and Results ---
        left_layout = QVBoxLayout()
        
        # Data Input Group
        data_input_group = QGroupBox("Data Input")
        data_layout = QVBoxLayout(data_input_group)
        
        self.table = QTableWidget()
        self.setup_table()
        data_layout.addWidget(self.table)

        # Add buttons for row management
        row_management_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Add Row")
        self.remove_row_button = QPushButton("Remove Selected Row")
        row_management_layout.addStretch() # Push buttons to the right
        row_management_layout.addWidget(self.add_row_button)
        row_management_layout.addWidget(self.remove_row_button)
        data_layout.addLayout(row_management_layout)

        left_layout.addWidget(data_input_group)

        # Results Plot Group
        self.plot_group = QGroupBox("Traverse Plot")
        plot_layout = QVBoxLayout(self.plot_group)
        self.plot_widget = PlotWidget()
        plot_layout.addWidget(self.plot_widget)
        left_layout.addWidget(self.plot_group)
        self.plot_group.setVisible(False) # Start with the plot hidden

        # --- Right Side: Controls ---
        controls_layout = QVBoxLayout()
        controls_group = QGroupBox("Controls & Options")
        controls_group.setLayout(controls_layout)
        controls_group.setFixedWidth(250) # Fixed width for the controls panel

        # Angle Input Type
        controls_layout.addWidget(QLabel("Angle Input Format:"))
        self.angle_type_combo = QComboBox() # This is the dropdown you wanted to change
        self.angle_type_combo.addItems(["Azimuth (DD.MMSS)", "Azimuth (Decimal)"])
        self.angle_type_combo.currentIndexChanged.connect(self.update_angle_header)
        controls_layout.addWidget(self.angle_type_combo)
        controls_layout.addSpacing(10)

        # Adjustment Method
        controls_layout.addWidget(QLabel("Adjustment Method:"))
        self.adjustment_method_combo = QComboBox()
        self.adjustment_method_combo.addItems(["Bowditch Method", "Least Squares Method"])
        # Disable "Least Squares Method" as it is not implemented yet.
        # The index for "Least Squares Method" is 1.
        self.adjustment_method_combo.model().item(1).setEnabled(False)
        controls_layout.addWidget(self.adjustment_method_combo)
        controls_layout.addSpacing(10)

        # Show Plot Checkbox
        self.show_plot_checkbox = QCheckBox("Show Traverse Plot")
        self.show_plot_checkbox.setChecked(False) # Explicitly set to unchecked
        self.show_plot_checkbox.stateChanged.connect(self.toggle_plot_visibility)
        controls_layout.addWidget(self.show_plot_checkbox)
        controls_layout.addSpacing(20)

        # Action Buttons
        self.import_csv_button = self.create_styled_button("Import from CSV", "#007BFF")
        self.calculate_button = self.create_styled_button("Calculate & Adjust", "#28A745")
        self.save_plot_button = self.create_styled_button("Save Plot", "#17A2B8")
        
        controls_layout.addWidget(self.import_csv_button)
        controls_layout.addWidget(self.calculate_button)
        controls_layout.addWidget(self.save_plot_button)
        # --- Connect Signals to Slots (i.e., connect button clicks to functions) ---
        self.import_csv_button.clicked.connect(self.handle_import_csv)
        self.calculate_button.clicked.connect(self.handle_calculate)
        self.save_plot_button.clicked.connect(self.handle_save_plot)

        controls_layout.addStretch() # Pushes export buttons to the bottom

        # Export Buttons
        export_label = QLabel("Export Results")
        export_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(export_label)
        
        self.export_csv_button = self.create_styled_button("Export to CSV", "#6C757D")
        self.export_pdf_button = self.create_styled_button("Export Report (PDF)", "#DC3545")
        self.export_kml_button = self.create_styled_button("Export for Google Earth (KML)", "#FFC107", text_color="#000000")

        controls_layout.addWidget(self.export_csv_button)
        controls_layout.addWidget(self.export_pdf_button)
        controls_layout.addWidget(self.export_kml_button)
        # Connect row management buttons
        self.add_row_button.clicked.connect(self.handle_add_row)
        self.remove_row_button.clicked.connect(self.handle_remove_row)
        
        # Connect export buttons
        self.export_csv_button.clicked.connect(self.handle_export_csv)
        self.export_pdf_button.clicked.connect(self.handle_export_pdf)
        self.export_kml_button.clicked.connect(self.handle_export_kml)

        # --- Assemble Main Layout ---
        main_layout.addLayout(left_layout, 7) # 70% of the width
        main_layout.addWidget(controls_group, 3) # 30% of the width

    def setup_table(self):
        """Configures the properties of the data input table."""
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Line", "Azimuth (DD.MMSS)", "Distance (m)",
            "Latitude", "Departure", "Lat. Corr. (m)", "Dep. Corr. (m)",
            "Adj. Easting (m)", "Adj. Northing (m)"
        ])
        header = self.table.horizontalHeader()
        self.table.setRowCount(5)  # Start with 5 empty rows for manual input
        
        # --- Add attributes to store calculation results for reports ---
        self.calculation_summary = {}
        self.final_coords = []

    def update_angle_header(self):
        """Updates the table header based on the selected angle type."""
        angle_type = self.angle_type_combo.currentText()
        self.table.horizontalHeaderItem(1).setText(angle_type)

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
        from PyQt6.QtGui import QColor
        color = QColor(color_str)
        return color.darker(int(100 / factor)).name()

    def handle_add_row(self):
        """Adds a new empty row to the end of the table."""
        current_row_count = self.table.rowCount()
        self.table.insertRow(current_row_count)

    def handle_remove_row(self):
        """Removes the currently selected row from the table."""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            self.table.removeRow(selected_row)
        else:
            QMessageBox.information(self, "Information", "Please select a row to remove.")

    def toggle_plot_visibility(self, state):
        """Shows or hides the plot group based on the checkbox state."""
        is_visible = (state == Qt.CheckState.Checked.value)
        self.plot_group.setVisible(is_visible)

    def handle_import_csv(self):
        """Opens a file dialog to select a CSV and populates the table with its data."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return # User cancelled the dialog

        df = import_csv_to_dataframe(file_path)

        if df is None:
            QMessageBox.critical(self, "Import Error", "Failed to read or process the CSV file.")
            return

        self.populate_table_from_dataframe(df)

    def populate_table_from_dataframe(self, df):
        """
        Clears the table and fills it with data from a pandas DataFrame.
        Assumes the DataFrame columns match the table's intended columns.
        """
        self.table.clearContents()
        self.table.setRowCount(len(df))

        # Map DataFrame columns to table columns by name if possible, or by index
        # This makes it more robust if CSV columns are in a different order.
        header_labels = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        
        for row_idx, row_data in df.iterrows():
            for col_idx, col_name in enumerate(header_labels):
                # Try to get data by column name, fall back to index if name doesn't exist in df
                if col_name in row_data:
                    item_data = str(row_data[col_name])
                elif col_idx < len(row_data):
                    item_data = str(row_data.iloc[col_idx])
                else:
                    item_data = "" # No data for this column
                
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(item_data))
        
        # Resize columns to fit the new content
        self.table.resizeColumnsToContents()

        QMessageBox.information(self, "Success", f"Successfully imported {len(df)} rows from the CSV file.")

    def handle_calculate(self):
        """Orchestrates the entire calculation and adjustment process."""
        # 1. Read and validate data from the table first.
        try:
            bearings_dms, distances = self.read_input_data_from_table()
            angle_type = self.angle_type_combo.currentText()

            if "DD.MMSS" in angle_type:
                bearings_dd = [dms_to_dd(b) for b in bearings_dms]
            else: # Decimal
                bearings_dd = [float(b) for b in bearings_dms]

            if None in bearings_dd:
                raise ValueError("Invalid angle format found. Please check your data and ensure it matches the selected format.")
        except ValueError as e:
            QMessageBox.critical(self, "Input Error", str(e))
            return # Stop execution if data is invalid

        # 2. Get starting coordinates from the user (only if data is valid)
        start_coords = self.get_start_coordinates()
        if not start_coords:
            return # User cancelled
        start_easting, start_northing = start_coords

        # 3. Perform the rest of the calculations
        try:
            # Calculate Latitudes and Departures
            latitudes, departures = calculate_lat_dep(np.array(bearings_dd), np.array(distances))

            # Store misclosures for reporting
            misclosure_lat = np.sum(latitudes)
            misclosure_dep = np.sum(departures)

            # Perform adjustment based on user selection
            adjustment_method = self.adjustment_method_combo.currentText()
            if adjustment_method == "Bowditch Method":
                adj_latitudes, adj_departures, lat_corrections, dep_corrections = adjust_traverse_bowditch(distances, latitudes, departures)
            else: # Placeholder for other methods
                QMessageBox.warning(self, "Not Implemented", "Least Squares Method is not yet fully implemented. No adjustment has been applied.")
                adj_latitudes, adj_departures = latitudes, departures
                zero_corrections = [0.0] * len(latitudes)
                lat_corrections, dep_corrections = zero_corrections, zero_corrections

            # Calculate final adjusted coordinates
            self.final_coords = calculate_coordinates(start_northing, start_easting, adj_latitudes, adj_departures)

            # Populate the results back into the table
            self.populate_results_in_table(latitudes, departures, lat_corrections, dep_corrections, self.final_coords)

            # Store summary for reporting
            self.calculation_summary = {
                "Adjustment Method": adjustment_method,
                "Start Northing (m)": f"{start_northing:.4f}",
                "Start Easting (m)": f"{start_easting:.4f}",
                "Latitude Misclosure (m)": f"{misclosure_lat:.4f}",
                "Departure Misclosure (m)": f"{misclosure_dep:.4f}",
                "Total Traverse Length (m)": f"{np.sum(distances):.4f}",
            }

            # Update the plot
            self.plot_widget.plot_traverse(self.final_coords, title="Adjusted Traverse")

            QMessageBox.information(self, "Calculation Complete", "Traverse has been calculated and adjusted successfully.")
        except Exception as e:
            QMessageBox.critical(self, "An Error Occurred", f"An unexpected error occurred: {e}")

    def read_input_data_from_table(self):
        """Reads and validates bearing and distance data from the QTableWidget."""
        bearings = []
        distances = []
        # Column indices have changed after removing 'Station'
        line_col, angle_col, dist_col = 0, 1, 2
        for row in range(self.table.rowCount()):
            line_item = self.table.item(row, line_col)
            bearing_item = self.table.item(row, angle_col)
            distance_item = self.table.item(row, dist_col)

            # Stop at the first empty row
            if not (line_item and line_item.text()):
                break

            if not (bearing_item and bearing_item.text() and distance_item and distance_item.text()):
                raise ValueError(f"Missing bearing or distance for Line '{line_item.text()}' at row {row + 1}.")

            bearings.append(bearing_item.text().strip())
            distances.append(float(distance_item.text().strip()))

        if not distances:
            raise ValueError("No data found in the table. Please enter or import data.")
        return bearings, distances

    def get_start_coordinates(self):
        """Prompts the user to enter the starting coordinates."""
        start_easting, ok1 = QInputDialog.getDouble(self, "Starting Coordinate", "Enter Start Easting:", 5000.0, decimals=4)
        if not ok1: return None

        start_northing, ok2 = QInputDialog.getDouble(self, "Starting Coordinate", "Enter Start Northing:", 1000.0, decimals=4)
        if not ok2: return None

        return start_easting, start_northing

    def populate_results_in_table(self, latitudes, departures, lat_corrections, dep_corrections, final_coords):
        """Writes the calculated and adjusted values into the table's output columns."""
        # Column indices have changed
        lat_col, dep_col = 3, 4
        lat_corr_col, dep_corr_col = 5, 6
        east_col, north_col = 7, 8

        for i in range(len(latitudes)):
            # Unadjusted Lat/Dep
            self.table.setItem(i, lat_col, QTableWidgetItem(f"{latitudes[i]:.4f}"))
            self.table.setItem(i, dep_col, QTableWidgetItem(f"{departures[i]:.4f}"))

            # Corrections
            self.table.setItem(i, lat_corr_col, QTableWidgetItem(f"{lat_corrections[i]:.4f}"))
            self.table.setItem(i, dep_corr_col, QTableWidgetItem(f"{dep_corrections[i]:.4f}"))

            # Final Adjusted Coordinates (for the END of the line)
            adj_easting = final_coords[i+1][0]
            adj_northing = final_coords[i+1][1]
            self.table.setItem(i, east_col, QTableWidgetItem(f"{adj_easting:.4f}")) # Easting is X
            self.table.setItem(i, north_col, QTableWidgetItem(f"{adj_northing:.4f}")) # Northing is Y

        # Resize columns to fit the new content
        self.table.resizeColumnsToContents()

    def get_table_data_as_dataframe(self):
        """Reads all data from the QTableWidget into a pandas DataFrame."""
        col_headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            # Check if the first cell has data, if not, assume it's an empty row
            first_item = self.table.item(row, 0)
            if not (first_item and first_item.text()):
                continue
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return pd.DataFrame(data, columns=col_headers)

    def handle_export_csv(self):
        """Handles exporting the current table data to a CSV file."""
        df = self.get_table_data_as_dataframe()
        if df.empty:
            QMessageBox.warning(self, "Export Error", "There is no data to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        if export_dataframe_to_csv(df, file_path):
            QMessageBox.information(self, "Success", f"Data successfully exported to {file_path}")
        else:
            QMessageBox.critical(self, "Export Error", "Failed to export data to CSV.")

    def handle_export_pdf(self):
        """Handles exporting a full report to a PDF file."""
        if not self.calculation_summary:
            QMessageBox.warning(self, "Export Error", "Please run a calculation before exporting a report.")
            return
        
        df = self.get_table_data_as_dataframe()
        if df.empty:
            QMessageBox.warning(self, "Export Error", "There is no data to export for the report.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Report to PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        if generate_traverse_report("Compass Traverse Report", self.calculation_summary, df, file_path):
            QMessageBox.information(self, "Success", f"Report successfully saved to {file_path}")
        else:
            QMessageBox.critical(self, "Export Error", "Failed to generate PDF report.")

    def handle_export_kml(self):
        """Handles exporting adjusted coordinates to a KML file for Google Earth."""
        if not self.final_coords:
            QMessageBox.warning(self, "Export Error", "Please run a calculation to generate coordinates first.")
            return

        # Prompt user for their UTM Zone's EPSG code
        epsg_code, ok = QInputDialog.getInt(
            self, "Coordinate System", "Enter the EPSG code for your UTM Zone (e.g., 32632 for WGS 84 / UTM zone 32N):", 32632
        )
        if not ok:
            return

        try:
            # The coordinates are (Easting, Northing), which is (x, y)
            local_points = [(coord[0], coord[1]) for coord in self.final_coords]
            
            # convert_to_global returns (lon, lat) which is what simplekml needs
            global_points = convert_to_global(local_points, epsg_code)

            # Prepare points for KML exporter: (name, lon, lat)
            kml_points = []
            kml_points.append(("Start Point", global_points[0][0], global_points[0][1]))
            for i, (lon, lat) in enumerate(global_points[1:], start=1):
                kml_points.append((f"Point {i}", lon, lat))

        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", f"Could not convert coordinates: {e}")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export to KML", "", "KML Files (*.kml)")
        if not file_path:
            return

        try:
            export_to_kml(file_path, kml_points)
            QMessageBox.information(self, "Success", f"KML file successfully saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate KML file: {e}")

    def handle_save_plot(self):
        """Saves the current traverse plot to a file."""
        if not self.plot_group.isVisible() or not self.final_coords:
            QMessageBox.warning(self, "Save Plot Error", "No plot is currently visible or calculated to save.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "Image Files (*.png *.jpg *.pdf);;All Files (*)")
        if file_path:
            self.plot_widget.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Success", f"Plot saved to {file_path}")
