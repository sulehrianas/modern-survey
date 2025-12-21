# UI for the Differential Leveling tab
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QFileDialog,
    QHeaderView,
    QMessageBox
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
import pandas as pd

# Import data service functions
from data_services.csv_handler import import_csv_to_dataframe, export_dataframe_to_csv
from data_services.pdf_reporter import generate_leveling_report

class LevelingTab(QWidget):
    def __init__(self):
        super().__init__()
        # Attribute to store calculation summary for reporting
        self.calculation_summary = {}
        self.setup_ui()

    def setup_ui(self):
        """Initializes the user interface for the tab."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Left Side: Data Input ---
        left_layout = QVBoxLayout()
        
        # Starting Benchmark Group
        start_bm_group = QGroupBox("Starting Benchmark (BM)")
        start_bm_layout = QHBoxLayout(start_bm_group)
        start_bm_layout.addWidget(QLabel("Start BM Elevation:"))
        self.start_bm_elevation = QDoubleSpinBox()
        self.start_bm_elevation.setDecimals(4)
        self.start_bm_elevation.setRange(0, 99999.9999)
        self.start_bm_elevation.setValue(100.0)
        start_bm_layout.addWidget(self.start_bm_elevation)
        start_bm_layout.addStretch()
        left_layout.addWidget(start_bm_group)

        # Data Table Group
        data_group = QGroupBox("Leveling Data")
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

        # --- Right Side: Controls & Results ---
        right_layout = QVBoxLayout()
        controls_group = QGroupBox("Controls & Results")
        controls_group.setFixedWidth(250)
        controls_layout = QVBoxLayout(controls_group)

        self.import_csv_button = self.create_styled_button("Import from CSV", "#007BFF")
        self.calculate_button = self.create_styled_button("Calculate Levels", "#28A745")
        self.clear_button = self.create_styled_button("Clear All Data", "#FFC107", text_color="#000000")
        
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

        controls_layout.addWidget(self.export_csv_button)
        controls_layout.addWidget(self.export_pdf_button)

        # Results Display
        self.results_label = QLabel("Misclosure will be shown here.")
        self.results_label.setWordWrap(True)
        controls_layout.addWidget(QLabel("<b>Results:</b>"))
        controls_layout.addWidget(self.results_label)
        controls_layout.addStretch()
        right_layout.addWidget(controls_group)

        # --- Assemble Main Layout ---
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout)

        # --- Connect Signals ---
        self.add_row_button.clicked.connect(self.add_row)
        self.remove_row_button.clicked.connect(self.remove_row)
        self.calculate_button.clicked.connect(self.handle_calculate)
        self.clear_button.clicked.connect(self.handle_clear)
        self.import_csv_button.clicked.connect(self.handle_import_csv)
        self.export_csv_button.clicked.connect(self.handle_export_csv)
        self.export_pdf_button.clicked.connect(self.handle_export_pdf)

    def setup_table(self):
        """Configures the properties of the data input table."""
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Station", "Backsight (BS)", "Height of Inst. (HI)", "Foresight (FS)", "Elevation"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setRowCount(10) # Start with 10 rows

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
        # QColor.darker() takes an integer percentage (100-400). 100/0.85 is ~117.
        return color.darker(int(100 / factor)).name()

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
        else:
            QMessageBox.information(self, "Information", "Please select a row to remove.")

    def handle_clear(self):
        """Clears all inputs and results."""
        self.table.clearContents()
        self.table.setRowCount(10)
        self.start_bm_elevation.setValue(100.0)
        self.calculation_summary = {}
        self.results_label.setText("Misclosure will be shown here.")
        QMessageBox.information(self, "Cleared", "All data has been cleared.")

    def get_table_data_as_dataframe(self):
        """Reads all data from the QTableWidget into a pandas DataFrame."""
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            # Stop at the first row where the 'Station' column is empty
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
        """Imports leveling data from a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        df = import_csv_to_dataframe(file_path)
        if df is not None:
            self.populate_table_from_dataframe(df)
            QMessageBox.information(self, "Success", f"Successfully imported {len(df)} rows.")
        else:
            QMessageBox.critical(self, "Import Error", "Failed to read data from CSV file.")

    def handle_export_csv(self):
        """Exports the current table data to a CSV file."""
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
        """Exports a full report of the leveling run to a PDF file."""
        if not self.calculation_summary:
            QMessageBox.warning(self, "Export Error", "Please run a calculation before exporting a report.")
            return

        df = self.get_table_data_as_dataframe()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Report to PDF", "", "PDF Files (*.pdf)")
        if not file_path: return

        if generate_leveling_report(self.calculation_summary, df, file_path):
            QMessageBox.information(self, "Success", f"Report successfully saved to {file_path}")
        else:
            QMessageBox.critical(self, "Export Error", "Failed to generate PDF report.")

    def handle_calculate(self):
        """Performs the differential leveling calculation."""
        try:
            start_elevation = self.start_bm_elevation.value()
            
            # Set starting elevation in the first row
            self.table.setItem(0, 4, QTableWidgetItem(f"{start_elevation:.4f}"))

            total_bs = 0.0
            total_fs = 0.0

            for row in range(self.table.rowCount()):
                # Read BS
                bs_item = self.table.item(row, 1)
                bs = float(bs_item.text()) if bs_item and bs_item.text() else 0.0

                # Read Elevation of current row
                elev_item = self.table.item(row, 4)
                if not (elev_item and elev_item.text()):
                    # If we don't have an elevation and no BS to create one, stop
                    if bs == 0.0: break 
                    else: raise ValueError(f"Missing elevation at row {row+1} before a turning point.")
                
                elevation = float(elev_item.text())

                # Calculate HI if there is a backsight
                if bs > 0:
                    hi = elevation + bs
                    total_bs += bs
                    self.table.setItem(row, 2, QTableWidgetItem(f"{hi:.4f}"))
                else:
                    # If no BS, HI carries over from the previous setup
                    hi_item = self.table.item(row - 1, 2)
                    if not (hi_item and hi_item.text()):
                        # This case happens on the first row if no BS is entered
                        if row == 0: continue
                        raise ValueError(f"Cannot calculate Foresight at row {row+1} without a Height of Instrument.")
                    hi = float(hi_item.text())

                # Read FS and calculate next elevation
                fs_item = self.table.item(row, 3)
                if fs_item and fs_item.text():
                    fs = float(fs_item.text())
                    total_fs += fs
                    next_elevation = hi - fs
                    
                    # Put the new elevation in the *next* row
                    if row + 1 < self.table.rowCount():
                        self.table.setItem(row + 1, 4, QTableWidgetItem(f"{next_elevation:.4f}"))
                    else:
                        # This is the last row, so we can't place the next elevation
                        pass
            
            # Arithmetic Check
            last_elev_item = self.table.item(self.find_last_data_row(), 4)
            if not last_elev_item:
                raise ValueError("Calculation incomplete. Could not find final elevation.")
            
            end_elevation = float(last_elev_item.text())
            misclosure = (start_elevation + total_bs - total_fs) - end_elevation

            # Store results for display and reporting
            self.calculation_summary = {
                "Starting BM Elevation": f"{start_elevation:.4f} m",
                "Total Backsight (BS)": f"{total_bs:.4f} m",
                "Total Foresight (FS)": f"{total_fs:.4f} m",
                "Arithmetic Check (Start El + BS - FS)": f"{(start_elevation + total_bs - total_fs):.4f} m",
                "Ending Elevation": f"{end_elevation:.4f} m",
                "Misclosure": f"{misclosure:.4f} m"
            }

            self.results_label.setText("\n".join([f"{key}: {value}" for key, value in self.calculation_summary.items()]))
            QMessageBox.information(self, "Success", "Leveling calculation complete.")

        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Input Error", f"Please check your data. A number might be missing or invalid.\n\nDetails: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def find_last_data_row(self):
        """Finds the last row containing any data."""
        for r in range(self.table.rowCount() - 1, -1, -1):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item and item.text():
                    return r
        return 0
