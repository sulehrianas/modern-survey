"""UI for the Simple Triangulation tab"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QTableWidget, QPushButton,
    QLabel, QLineEdit, QMessageBox, QTableWidgetItem, QComboBox, QHeaderView, QFileDialog,
    QDoubleSpinBox, QCheckBox, QTextEdit, QInputDialog, QTabWidget, QStackedWidget
)
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import Qt
import pandas as pd
import math
from .plot_widget import PlotWidget
from core.triangulation import calculate_simple_triangulation, adjust_network_least_squares
from data_services.csv_handler import import_csv_to_dataframe, export_dataframe_to_csv
from data_services.kml_exporter import export_to_kml
from core.coordinate_converter import convert_to_global
from core.calculations import dms_to_dd, dd_to_dms

class TriangulationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.stations = {}
        self.tri_results = []
        self.quad_stations = {} # Store quad results
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self.tab_chain = QWidget()
        self.setup_chain_ui(self.tab_chain)
        
        self.tab_quad = QWidget()
        self.setup_quad_ui(self.tab_quad)
        
        self.tabs.addTab(self.tab_chain, "Simple Chain (Triangles)")
        self.tabs.addTab(self.tab_quad, "Quadrilateral / Polygon")
        
        layout.addWidget(self.tabs)

    def setup_chain_ui(self, parent):
        main_layout = QHBoxLayout(parent)
        
        # --- Left Panel: Data Entry & Plot ---
        left_layout = QVBoxLayout()
        
        # 1. Start Configuration
        start_group = QGroupBox("Starting Configuration")
        start_layout = QVBoxLayout(start_group)
        
        # Row 1: Start Station Coords
        r1 = QHBoxLayout()
        self.start_e = QDoubleSpinBox(); self.start_e.setRange(0, 999999); self.start_e.setValue(1000.0)
        self.start_n = QDoubleSpinBox(); self.start_n.setRange(0, 999999); self.start_n.setValue(1000.0)
        r1.addWidget(QLabel("Start Easting:"))
        r1.addWidget(self.start_e)
        r1.addWidget(QLabel("Start Northing:"))
        r1.addWidget(self.start_n)
        start_layout.addLayout(r1)
        
        # Row 2: Baseline Info
        r2 = QHBoxLayout()
        self.base_dist = QDoubleSpinBox(); self.base_dist.setRange(0, 99999); self.base_dist.setValue(100.0)
        self.base_az = QLineEdit("90.0000")
        r2.addWidget(QLabel("Baseline Distance:"))
        r2.addWidget(self.base_dist)
        r2.addWidget(QLabel("Baseline Azimuth (DD.MMSS):"))
        r2.addWidget(self.base_az)
        start_layout.addLayout(r2)
        
        left_layout.addWidget(start_group)

        # 2. Triangles Table
        tri_group = QGroupBox("Triangles Input")
        tri_layout = QVBoxLayout(tri_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Base Start", "Base End", "New Point", 
            "Angle @ Start", "Angle @ End", "Angle @ New", "Direction"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        tri_layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add_row = QPushButton("Add Row")
        self.btn_remove_row = QPushButton("Remove Row")
        btn_layout.addWidget(self.btn_add_row)
        btn_layout.addWidget(self.btn_remove_row)
        tri_layout.addLayout(btn_layout)
        
        left_layout.addWidget(tri_group)
        
        # 3. Plot (Hidden by default)
        self.plot_group = QGroupBox("Graphical Plot")
        plot_layout = QVBoxLayout(self.plot_group)
        self.plot_widget = PlotWidget()
        plot_layout.addWidget(self.plot_widget)
        self.plot_group.setVisible(False)
        left_layout.addWidget(self.plot_group)
        
        # --- Right Panel: Controls & Results ---
        controls_group = QGroupBox("Controls & Results")
        controls_group.setFixedWidth(300)
        controls_layout = QVBoxLayout(controls_group)
        
        # Calculate Button
        self.btn_calc = QPushButton("Calculate & Adjust")
        self.btn_calc.setStyleSheet("background-color: #28A745; color: white; font-weight: bold; padding: 10px;")
        controls_layout.addWidget(self.btn_calc)

        # Angle Type Selection
        controls_layout.addWidget(QLabel("Angle Type:"))
        self.angle_type_combo = QComboBox()
        self.angle_type_combo.addItems(["Internal (I)", "External (E)"])
        self.angle_type_combo.currentIndexChanged.connect(self.update_angle_headers)
        controls_layout.addWidget(self.angle_type_combo)

        # Default Direction Selection
        controls_layout.addWidget(QLabel("Default Direction:"))
        self.chain_default_dir = QComboBox()
        self.chain_default_dir.addItems(["Left (Anti-Clockwise)", "Right (Clockwise)"])
        controls_layout.addWidget(self.chain_default_dir)

        # Import CSV Button
        self.btn_import_csv = QPushButton("Import Data (CSV)")
        controls_layout.addWidget(self.btn_import_csv)
        
        # Show Plot Checkbox
        self.chk_show_plot = QCheckBox("Show Plot")
        self.chk_show_plot.stateChanged.connect(self.toggle_plot)
        controls_layout.addWidget(self.chk_show_plot)
        
        # Save Plot Button
        self.btn_save_plot = QPushButton("Save Plot")
        controls_layout.addWidget(self.btn_save_plot)
        self.btn_save_plot.setVisible(False)

        # Export Buttons
        self.btn_export_csv = QPushButton("Export Results (CSV)")
        controls_layout.addWidget(self.btn_export_csv)
        
        self.btn_export_kml = QPushButton("Export KML")
        controls_layout.addWidget(self.btn_export_kml)
        
        self.btn_export_pdf = QPushButton("Export Report (PDF)")
        controls_layout.addWidget(self.btn_export_pdf)
        
        # Results Text
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setPlaceholderText("Results will appear here...")
        controls_layout.addWidget(self.results_display)
        controls_layout.addStretch()

        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(controls_group)

        # Signals
        self.btn_add_row.clicked.connect(self.add_row)
        self.btn_remove_row.clicked.connect(self.remove_row)
        self.btn_calc.clicked.connect(self.handle_calculate)
        self.btn_save_plot.clicked.connect(self.handle_save_plot)
        self.btn_import_csv.clicked.connect(self.handle_import_csv)
        self.btn_export_csv.clicked.connect(self.handle_export_csv)
        self.btn_export_kml.clicked.connect(self.handle_export_kml)
        self.btn_export_pdf.clicked.connect(self.handle_export_pdf)
        
        # Add initial row
        self.add_row()
        self.update_angle_headers()

    def setup_quad_ui(self, parent):
        layout = QHBoxLayout(parent)
        
        # Left: Inputs
        left = QVBoxLayout()
        
        # Mode Selection
        mode_grp = QGroupBox("Calculation Mode")
        mode_layout = QHBoxLayout(mode_grp)
        self.net_mode_combo = QComboBox()
        self.net_mode_combo.addItems(["Standard Quadrilateral", "General Network (Any Stations)"])
        self.net_mode_combo.currentIndexChanged.connect(self.toggle_net_mode)
        mode_layout.addWidget(QLabel("Select Mode:"))
        mode_layout.addWidget(self.net_mode_combo)
        left.addWidget(mode_grp)
        
        self.net_stack = QStackedWidget()
        
        # --- Page 1: Standard Quad ---
        self.page_quad = QWidget()
        quad_layout = QVBoxLayout(self.page_quad)
        quad_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Station Names
        stn_grp = QGroupBox("Station Configuration")
        stn_layout = QVBoxLayout(stn_grp)
        
        name_layout = QHBoxLayout()
        self.q_stn_a = QLineEdit("A"); self.q_stn_b = QLineEdit("B")
        self.q_stn_c = QLineEdit("C"); self.q_stn_d = QLineEdit("D")
        name_layout.addWidget(QLabel("A:")); name_layout.addWidget(self.q_stn_a)
        name_layout.addWidget(QLabel("B:")); name_layout.addWidget(self.q_stn_b)
        name_layout.addWidget(QLabel("C:")); name_layout.addWidget(self.q_stn_c)
        name_layout.addWidget(QLabel("D:")); name_layout.addWidget(self.q_stn_d)
        stn_layout.addLayout(name_layout)
        
        self.quad_dir_combo = QComboBox()
        self.quad_dir_combo.addItems(["Anti-Clockwise (Left)", "Clockwise (Right)"])
        stn_layout.addWidget(QLabel("Traverse Direction:"))
        stn_layout.addWidget(self.quad_dir_combo)
        
        quad_layout.addWidget(stn_grp)
        
        # 2. Baseline
        base_grp = QGroupBox("Baseline (A -> B)")
        base_layout = QHBoxLayout(base_grp)
        self.q_base_dist = QDoubleSpinBox(); self.q_base_dist.setRange(0, 99999); self.q_base_dist.setValue(100.0)
        self.q_base_az = QLineEdit("90.0000")
        self.q_start_e = QDoubleSpinBox(); self.q_start_e.setRange(0, 999999); self.q_start_e.setValue(1000.0)
        self.q_start_n = QDoubleSpinBox(); self.q_start_n.setRange(0, 999999); self.q_start_n.setValue(1000.0)
        
        base_layout.addWidget(QLabel("Start E:")); base_layout.addWidget(self.q_start_e)
        base_layout.addWidget(QLabel("Start N:")); base_layout.addWidget(self.q_start_n)
        base_layout.addWidget(QLabel("Dist A-B:")); base_layout.addWidget(self.q_base_dist)
        base_layout.addWidget(QLabel("Azimuth:")); base_layout.addWidget(self.q_base_az)
        quad_layout.addWidget(base_grp)
        
        # 3. Angles Input (8 Angles for Braced Quad)
        ang_grp = QGroupBox("Observed Angles (DD.MMSS)")
        ang_layout = QVBoxLayout(ang_grp)
        
        # Grid for angles
        grid = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        
        self.ang_bac = QLineEdit("45.0000"); col1.addWidget(QLabel("BAC (A1):")); col1.addWidget(self.ang_bac)
        self.ang_cad = QLineEdit("45.0000"); col1.addWidget(QLabel("CAD (A2):")); col1.addWidget(self.ang_cad)
        self.ang_cbd = QLineEdit("45.0000"); col1.addWidget(QLabel("CBD (B1):")); col1.addWidget(self.ang_cbd)
        self.ang_dba = QLineEdit("45.0000"); col1.addWidget(QLabel("DBA (B2):")); col1.addWidget(self.ang_dba)
        
        self.ang_dca = QLineEdit("45.0000"); col2.addWidget(QLabel("DCA (C1):")); col2.addWidget(self.ang_dca)
        self.ang_acb = QLineEdit("45.0000"); col2.addWidget(QLabel("ACB (C2):")); col2.addWidget(self.ang_acb)
        self.ang_adb = QLineEdit("45.0000"); col2.addWidget(QLabel("ADB (D1):")); col2.addWidget(self.ang_adb)
        self.ang_bdc = QLineEdit("45.0000"); col2.addWidget(QLabel("BDC (D2):")); col2.addWidget(self.ang_bdc)
        
        grid.addLayout(col1)
        grid.addLayout(col2)
        ang_layout.addLayout(grid)
        quad_layout.addWidget(ang_grp)
        quad_layout.addStretch()
        
        self.net_stack.addWidget(self.page_quad)
        
        # --- Page 2: General Network ---
        self.page_gen = QWidget()
        gen_layout = QVBoxLayout(self.page_gen)
        gen_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stations Table
        gen_stn_grp = QGroupBox("Stations (Approx Coordinates)")
        gen_stn_layout = QVBoxLayout(gen_stn_grp)
        self.gen_stn_table = QTableWidget(0, 4)
        self.gen_stn_table.setHorizontalHeaderLabels(["Station", "Approx E", "Approx N", "Fixed?"])
        self.gen_stn_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        gen_stn_layout.addWidget(self.gen_stn_table)
        
        stn_btns = QHBoxLayout()
        self.btn_add_gen_stn = QPushButton("Add Station")
        self.btn_add_gen_stn.clicked.connect(self.add_gen_stn_row)
        self.btn_rem_gen_stn = QPushButton("Remove Station")
        self.btn_rem_gen_stn.clicked.connect(self.rem_gen_stn_row)
        stn_btns.addWidget(self.btn_add_gen_stn); stn_btns.addWidget(self.btn_rem_gen_stn)
        gen_stn_layout.addLayout(stn_btns)
        gen_layout.addWidget(gen_stn_grp)
        
        # Observations Table
        gen_obs_grp = QGroupBox("Observations")
        gen_obs_layout = QVBoxLayout(gen_obs_grp)
        
        # Angle Direction Setting
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Angle Measurement:"))
        self.gen_angle_dir = QComboBox()
        self.gen_angle_dir.addItems(["Angles to the Right (Clockwise)", "Angles to the Left (Anti-Clockwise)"])
        dir_layout.addWidget(self.gen_angle_dir)
        dir_layout.addStretch()
        gen_obs_layout.addLayout(dir_layout)
        
        self.gen_obs_table = QTableWidget(0, 6)
        self.gen_obs_table.setHorizontalHeaderLabels(["Type", "At", "From", "To", "Value", "SD"])
        self.gen_obs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        gen_obs_layout.addWidget(self.gen_obs_table)
        
        obs_btns = QHBoxLayout()
        self.btn_add_gen_obs = QPushButton("Add Observation")
        self.btn_add_gen_obs.clicked.connect(self.add_gen_obs_row)
        self.btn_rem_gen_obs = QPushButton("Remove Observation")
        self.btn_rem_gen_obs.clicked.connect(self.rem_gen_obs_row)
        obs_btns.addWidget(self.btn_add_gen_obs); obs_btns.addWidget(self.btn_rem_gen_obs)
        gen_obs_layout.addLayout(obs_btns)
        gen_layout.addWidget(gen_obs_grp)
        
        self.net_stack.addWidget(self.page_gen)
        
        left.addWidget(self.net_stack)
        
        # --- Right Panel: Controls & Results ---
        right = QVBoxLayout()
        
        # Plot (Hidden by default)
        self.quad_plot_group = QGroupBox("Quadrilateral Plot")
        plot_layout = QVBoxLayout(self.quad_plot_group)
        self.quad_plot = PlotWidget()
        plot_layout.addWidget(self.quad_plot)
        self.quad_plot_group.setVisible(False)
        right.addWidget(self.quad_plot_group)
        
        # Controls Group
        ctrl_grp = QGroupBox("Controls")
        ctrl_layout = QVBoxLayout(ctrl_grp)
        
        self.btn_calc_quad = QPushButton("Calculate & Adjust")
        self.btn_calc_quad.setStyleSheet("background-color: #28A745; color: white; font-weight: bold; padding: 10px;")
        self.btn_calc_quad.clicked.connect(self.handle_quad_calc)
        ctrl_layout.addWidget(self.btn_calc_quad)
        
        # Plot Toggle
        self.chk_show_quad_plot = QCheckBox("Show Plot")
        self.chk_show_quad_plot.stateChanged.connect(self.toggle_quad_plot)
        ctrl_layout.addWidget(self.chk_show_quad_plot)
        
        # Import/Export
        self.btn_imp_quad = QPushButton("Import CSV")
        self.btn_imp_quad.clicked.connect(self.handle_import_quad_csv)
        ctrl_layout.addWidget(self.btn_imp_quad)
        
        self.btn_exp_quad = QPushButton("Export Results (CSV)")
        self.btn_exp_quad.clicked.connect(self.handle_export_quad_csv)
        ctrl_layout.addWidget(self.btn_exp_quad)
        
        self.btn_save_quad_plot = QPushButton("Save Plot")
        self.btn_save_quad_plot.clicked.connect(self.handle_save_quad_plot)
        self.btn_save_quad_plot.setVisible(False)
        ctrl_layout.addWidget(self.btn_save_quad_plot)

        self.btn_exp_quad_kml = QPushButton("Export KML")
        self.btn_exp_quad_kml.clicked.connect(self.handle_export_quad_kml)
        ctrl_layout.addWidget(self.btn_exp_quad_kml)

        self.btn_exp_quad_pdf = QPushButton("Export Report (PDF)")
        self.btn_exp_quad_pdf.clicked.connect(self.handle_export_quad_pdf)
        ctrl_layout.addWidget(self.btn_exp_quad_pdf)
        
        right.addWidget(ctrl_grp)
        
        # Results
        self.quad_results = QTextEdit()
        self.quad_results.setReadOnly(True)
        self.quad_results.setPlaceholderText("Quadrilateral results will appear here...")
        right.addWidget(self.quad_results)
        
        layout.addLayout(left, 4)
        layout.addLayout(right, 6)

    def toggle_net_mode(self, index):
        self.net_stack.setCurrentIndex(index)

    def add_gen_stn_row(self):
        r = self.gen_stn_table.rowCount()
        self.gen_stn_table.insertRow(r)
        # Fixed Checkbox
        chk_widget = QWidget()
        chk = QCheckBox()
        l = QHBoxLayout(chk_widget); l.addWidget(chk); l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setContentsMargins(0,0,0,0)
        self.gen_stn_table.setCellWidget(r, 3, chk_widget)

    def rem_gen_stn_row(self):
        r = self.gen_stn_table.currentRow()
        if r >= 0: self.gen_stn_table.removeRow(r)

    def add_gen_obs_row(self):
        r = self.gen_obs_table.rowCount()
        self.gen_obs_table.insertRow(r)
        # Type Combo
        cb = QComboBox()
        cb.addItems(["Angle", "Distance", "Azimuth"])
        self.gen_obs_table.setCellWidget(r, 0, cb)

    def rem_gen_obs_row(self):
        r = self.gen_obs_table.currentRow()
        if r >= 0: self.gen_obs_table.removeRow(r)

    def handle_quad_calc(self):
        try:
            if self.net_mode_combo.currentIndex() == 1:
                # General Network Mode
                stations = {}
                for r in range(self.gen_stn_table.rowCount()):
                    name = self.gen_stn_table.item(r, 0).text() if self.gen_stn_table.item(r, 0) else ""
                    if not name: continue
                    e = float(self.gen_stn_table.item(r, 1).text())
                    n = float(self.gen_stn_table.item(r, 2).text())
                    chk_w = self.gen_stn_table.cellWidget(r, 3)
                    fixed = chk_w.findChild(QCheckBox).isChecked()
                    stations[name] = {'e': e, 'n': n, 'fixed': fixed}
                
                obs = []
                is_left_angles = "Left" in self.gen_angle_dir.currentText()
                for r in range(self.gen_obs_table.rowCount()):
                    cb = self.gen_obs_table.cellWidget(r, 0)
                    otype = cb.currentText().lower()
                    at = self.gen_obs_table.item(r, 1).text() if self.gen_obs_table.item(r, 1) else ""
                    frm = self.gen_obs_table.item(r, 2).text() if self.gen_obs_table.item(r, 2) else ""
                    to = self.gen_obs_table.item(r, 3).text() if self.gen_obs_table.item(r, 3) else ""
                    val = float(self.gen_obs_table.item(r, 4).text())
                    sd = float(self.gen_obs_table.item(r, 5).text())
                    
                    # Convert Left (Anti-Clockwise) angles to Standard (Right/Clockwise)
                    if otype == 'angle' and is_left_angles:
                        val = 360.0 - val
                        
                    obs.append({'type': otype, 'at': at, 'from': frm, 'to': to, 'value': val, 'sd': sd})
                
                adj_stations = adjust_network_least_squares(stations, obs)
                self.quad_stations = adj_stations
                
                # Report
                report = "<h3>General Network Adjustment</h3>"
                report += "<table border='1'><tr><th>Station</th><th>Easting</th><th>Northing</th></tr>"
                for name, s in adj_stations.items():
                    report += f"<tr><td>{name}</td><td>{s['e']:.4f}</td><td>{s['n']:.4f}</td></tr>"
                report += "</table>"
                self.quad_results.setHtml(report)
                
                # Plot
                plot_obs = [{'type': o['type'], 'from': o['at'] if o['type']=='angle' else o['from'], 'to': o['to']} for o in obs]
                self.quad_plot.plot_network(adj_stations, plot_obs, title="General Network")
                QMessageBox.information(self, "Success", "Network adjusted.")
                return

            # Gather Inputs
            a, b, c, d = self.q_stn_a.text(), self.q_stn_b.text(), self.q_stn_c.text(), self.q_stn_d.text()
            
            # Baseline
            ea = self.q_start_e.value()
            na = self.q_start_n.value()
            dist_ab = self.q_base_dist.value()
            az_ab_dms = self.q_base_az.text()
            az_ab = dms_to_dd(az_ab_dms)
            
            # Direction
            calc_dir = "Right" if "Clockwise (Right)" in self.quad_dir_combo.currentText() else "Left"
            
            # Angles (DD.MMSS -> DD)
            angles = {
                'bac': dms_to_dd(self.ang_bac.text()), 'cad': dms_to_dd(self.ang_cad.text()),
                'cbd': dms_to_dd(self.ang_cbd.text()), 'dba': dms_to_dd(self.ang_dba.text()),
                'dca': dms_to_dd(self.ang_dca.text()), 'acb': dms_to_dd(self.ang_acb.text()),
                'adb': dms_to_dd(self.ang_adb.text()), 'bdc': dms_to_dd(self.ang_bdc.text())
            }
            
            # Geometric Checks
            report = "<h3>Quadrilateral Analysis</h3>"
            
            # 1. Quad Sum (A+B+C+D)
            sum_a = angles['bac'] + angles['cad']
            sum_b = angles['cbd'] + angles['dba']
            sum_c = angles['dca'] + angles['acb']
            sum_d = angles['adb'] + angles['bdc']
            total = sum_a + sum_b + sum_c + sum_d
            
            report += f"<b>Total Angle Sum:</b> {self.format_dms(total)} (Target 360°)<br>"
            report += f"<i>Misclosure: {self.format_dms(total - 360.0)}</i><br><br>"
            
            # 2. Calculate Coordinates
            # Station A (Fixed)
            stations = {a: {'e': ea, 'n': na, 'fixed': True}}
            
            # Station B (Fixed by Az/Dist)
            eb = ea + dist_ab * math.sin(math.radians(az_ab))
            nb = na + dist_ab * math.cos(math.radians(az_ab))
            stations[b] = {'e': eb, 'n': nb, 'fixed': True} # Fix B to hold baseline scale/orient
            
            # Approx C (Intersection from A-B using Tri ABC)
            # Angle at A = BAC, Angle at B = CBA (CBD + DBA)
            ang_a_c = angles['bac']
            ang_b_c = angles['cbd'] + angles['dba']
            ec, nc = self.calculate_intersection_coords(ea, na, eb, nb, ang_a_c, ang_b_c, calc_dir)
            stations[c] = {'e': ec, 'n': nc, 'fixed': False}
            
            # Approx D (Intersection from A-B using Tri ABD)
            # Angle at A = BAD (BAC + CAD), Angle at B = DBA
            ang_a_d = angles['bac'] + angles['cad']
            ang_b_d = angles['dba']
            ed, nd = self.calculate_intersection_coords(ea, na, eb, nb, ang_a_d, ang_b_d, calc_dir)
            stations[d] = {'e': ed, 'n': nd, 'fixed': False}
            
            # 3. Prepare Observations for LSA
            obs = []
            # Distance AB
            obs.append({'type': 'distance', 'from': a, 'to': b, 'value': dist_ab, 'sd': 0.005})
            
            # Angles (At Station, From Backsight, To Foresight)
            # A: BAC (B->C), CAD (C->D)
            obs.append({'type': 'angle', 'at': a, 'from': b, 'to': c, 'value': angles['bac'], 'sd': 1.0/3600})
            obs.append({'type': 'angle', 'at': a, 'from': c, 'to': d, 'value': angles['cad'], 'sd': 1.0/3600})
            
            # B: CBD (D->C), DBA (A->D) -> Wait, DBA is D-B-A.
            # Standard input DBA means angle between BD and BA.
            # So at B: From D to A is DBA. From C to D is CBD.
            obs.append({'type': 'angle', 'at': b, 'from': d, 'to': a, 'value': angles['dba'], 'sd': 1.0/3600})
            obs.append({'type': 'angle', 'at': b, 'from': c, 'to': d, 'value': angles['cbd'], 'sd': 1.0/3600})
            
            # C: DCA (A->D), ACB (B->A)
            obs.append({'type': 'angle', 'at': c, 'from': a, 'to': d, 'value': angles['dca'], 'sd': 1.0/3600})
            obs.append({'type': 'angle', 'at': c, 'from': b, 'to': a, 'value': angles['acb'], 'sd': 1.0/3600})
            
            # D: ADB (B->A), BDC (C->B)
            obs.append({'type': 'angle', 'at': d, 'from': b, 'to': a, 'value': angles['adb'], 'sd': 1.0/3600})
            obs.append({'type': 'angle', 'at': d, 'from': c, 'to': b, 'value': angles['bdc'], 'sd': 1.0/3600})
            
            # 4. Adjust
            adj_stations = adjust_network_least_squares(stations, obs)
            self.quad_stations = adj_stations
            
            # 5. Report
            report += "<h3>Adjusted Coordinates</h3>"
            report += "<table border='1' cellspacing='0' cellpadding='5'>"
            report += "<tr><th>Station</th><th>Easting</th><th>Northing</th></tr>"
            for name in [a, b, c, d]:
                s = adj_stations[name]
                report += f"<tr><td>{name}</td><td>{s['e']:.4f}</td><td>{s['n']:.4f}</td></tr>"
            report += "</table>"
            
            self.quad_results.setHtml(report)
            
            # 6. Plot
            plot_obs = []
            # Draw perimeter and diagonals
            plot_obs.append({'type': 'distance', 'from': a, 'to': b})
            plot_obs.append({'type': 'distance', 'from': b, 'to': c})
            plot_obs.append({'type': 'distance', 'from': c, 'to': d})
            plot_obs.append({'type': 'distance', 'from': d, 'to': a})
            # Diagonals
            plot_obs.append({'type': 'distance', 'from': a, 'to': c})
            plot_obs.append({'type': 'distance', 'from': b, 'to': d})
            
            self.quad_plot.plot_network(adj_stations, plot_obs, title="Adjusted Quadrilateral")
            QMessageBox.information(self, "Success", "Quadrilateral calculated and adjusted.")

            # Refresh button visibility
            self.toggle_quad_plot(self.chk_show_quad_plot.checkState().value)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def calculate_intersection_coords(self, e1, n1, e2, n2, ang_a_dd, ang_b_dd, direction="Left"):
        """
        Calculates intersection point C given baseline A(e1,n1)->B(e2,n2) and angles A and B (in Decimal Degrees).
        """
        dx = e2 - e1
        dy = n2 - n1
        dist_ab = math.sqrt(dx**2 + dy**2)
        az_ab = math.degrees(math.atan2(dx, dy)) % 360
        
        # Calculate Azimuths to C
        if direction == "Left":
            az_ac = (az_ab - ang_a_dd) % 360
            # Angle at B is inside, so Az BC is Az BA + Angle B. Az BA = Az AB + 180
            az_ba = (az_ab + 180) % 360
            az_bc = (az_ba + ang_b_dd) % 360 
        else: # Right
            az_ac = (az_ab + ang_a_dd) % 360
            az_ba = (az_ab + 180) % 360
            az_bc = (az_ba - ang_b_dd) % 360
            
        # Solve for C using Sine Rule (Intersection of two rays)
        # Angle at C = 180 - (A + B)
        ang_c = 180 - (ang_a_dd + ang_b_dd)
        if ang_c <= 0.001: return 0.0, 0.0 # Invalid geometry
        
        # Dist AC / sin(B) = Dist AB / sin(C)
        dist_ac = dist_ab * math.sin(math.radians(ang_b_dd)) / math.sin(math.radians(ang_c))
        
        ec = e1 + dist_ac * math.sin(math.radians(az_ac))
        nc = n1 + dist_ac * math.cos(math.radians(az_ac))
        
        return ec, nc

    def update_angle_headers(self):
        atype = "I" if "Internal" in self.angle_type_combo.currentText() else "E"
        self.table.horizontalHeaderItem(3).setText(f"Angle @ Start ({atype})")
        self.table.horizontalHeaderItem(4).setText(f"Angle @ End ({atype})")
        self.table.horizontalHeaderItem(5).setText(f"Angle @ New ({atype})")

    def toggle_plot(self, state):
        is_visible = state == Qt.CheckState.Checked.value
        self.plot_group.setVisible(is_visible)
        self.btn_save_plot.setVisible(is_visible and bool(self.stations))

    def toggle_quad_plot(self, state):
        is_visible = state == Qt.CheckState.Checked.value
        self.quad_plot_group.setVisible(is_visible)
        self.btn_save_quad_plot.setVisible(is_visible and bool(self.quad_stations))

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Add Direction Combo
        combo = QComboBox()
        combo.addItems(["Left (Anti-Clockwise)", "Right (Clockwise)"])
        
        # Set default from global combo if available
        if hasattr(self, 'chain_default_dir'):
            combo.setCurrentText(self.chain_default_dir.currentText())
            
        self.table.setCellWidget(row, 6, combo)
        
        # Default values for testing
        if row == 0:
            self.table.setItem(row, 0, QTableWidgetItem("A"))
            self.table.setItem(row, 1, QTableWidgetItem("B"))
            self.table.setItem(row, 2, QTableWidgetItem("C"))

    def remove_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def handle_calculate(self):
        try:
            # 1. Get Start Config
            start_e = self.start_e.value()
            start_n = self.start_n.value()
            base_dist = self.base_dist.value()
            base_az = self.base_az.text()
            
            is_external = "External" in self.angle_type_combo.currentText()

            # 2. Parse Triangles
            triangles = []
            for row in range(self.table.rowCount()):
                p1_item = self.table.item(row, 0)
                p2_item = self.table.item(row, 1)
                p3_item = self.table.item(row, 2)
                a1_item = self.table.item(row, 3)
                a2_item = self.table.item(row, 4)
                a3_item = self.table.item(row, 5)
                dir_combo = self.table.cellWidget(row, 6)

                if not (p1_item and p1_item.text() and p2_item and p2_item.text() and p3_item and p3_item.text()):
                    continue # Skip incomplete rows

                a1_val = a1_item.text()
                a2_val = a2_item.text()
                a3_val = a3_item.text()

                if is_external:
                    # Convert Reflex/External to Internal (360 - angle)
                    # Convert to DD, subtract from 360, convert back to DMS string for core logic
                    a1_val = dd_to_dms(360.0 - dms_to_dd(a1_val))
                    a2_val = dd_to_dms(360.0 - dms_to_dd(a2_val))
                    a3_val = dd_to_dms(360.0 - dms_to_dd(a3_val))

                triangles.append({
                    'p1': p1_item.text(),
                    'p2': p2_item.text(),
                    'p3': p3_item.text(),
                    'a1': a1_val,
                    'a2': a2_val,
                    'a3': a3_val,
                'dir': "Left" if "Left" in dir_combo.currentText() else "Right"
                })

            if not triangles:
                QMessageBox.warning(self, "No Data", "Please enter at least one triangle.")
                return

            # 3. Calculate
            self.stations, self.tri_results = calculate_simple_triangulation(start_e, start_n, base_dist, base_az, triangles)

            # 4. Display Results
            res_text = "<h3>Triangulation Report:</h3>"
            for res in self.tri_results:
                # Format angles to symbols
                p1, p2, p3 = res['triangle'].split('-')
                a1_sym = self.format_dms(dms_to_dd(res['adj_a1']))
                a2_sym = self.format_dms(dms_to_dd(res['adj_a2']))
                a3_sym = self.format_dms(dms_to_dd(res['adj_a3']))
                err_sym = self.format_dms(res['error_deg'])

                res_text += f"<div style='margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 10px;'>"
                res_text += f"<b style='font-size:14px; color:#2c3e50;'>Triangle {res['triangle']}</b><br>"
                res_text += f"<b>Angular Misclosure:</b> <span style='color:#e74c3c;'>{err_sym}</span><br>"
                res_text += f"<b>Adjusted Angles:</b><br>"
                res_text += f"&nbsp;&nbsp;&bull; Angle @ {p1}: {a1_sym}<br>"
                res_text += f"&nbsp;&nbsp;&bull; Angle @ {p2}: {a2_sym}<br>"
                res_text += f"&nbsp;&nbsp;&bull; Angle @ {p3}: {a3_sym}<br>"
                res_text += f"<b>Side Distances:</b><br>"
                res_text += f"&nbsp;&nbsp;&bull; Base ({p1}-{p2}): <b>{res['dist_base']:.3f} m</b><br>"
                res_text += f"&nbsp;&nbsp;&bull; Side ({p1}-{p3}): <b>{res['dist_13']:.3f} m</b><br>"
                res_text += f"&nbsp;&nbsp;&bull; Side ({p2}-{p3}): <b>{res['dist_23']:.3f} m</b><br>"
                res_text += "</div>"
            
            res_text += "<h3>Final Coordinates:</h3>"
            for name, (e, n) in self.stations.items():
                res_text += f"{name}: E={e:.3f}, N={n:.3f}<br>"
            
            self.results_display.setHtml(res_text)

            # 5. Plot
            # Convert stations dict to format for plot_network
            plot_stations = {name: {'e': coords[0], 'n': coords[1], 'fixed': False} for name, coords in self.stations.items()}
            
            # Create observation lines for plotting
            plot_obs = []
            # Add baseline
            first_tri = triangles[0]
            plot_obs.append({'type': 'distance', 'from': first_tri['p1'], 'to': first_tri['p2']})
            
            for tri in triangles:
                plot_obs.append({'type': 'distance', 'from': tri['p1'], 'to': tri['p3']})
                plot_obs.append({'type': 'distance', 'from': tri['p2'], 'to': tri['p3']})

            self.plot_widget.plot_network(plot_stations, plot_obs, title="Triangulation Network")
            QMessageBox.information(self, "Success", "Calculation and Adjustment Complete.")

            # Refresh button visibility
            self.toggle_plot(self.chk_show_plot.checkState().value)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def format_dms(self, dd_angle):
        """Formats decimal degrees to D° M' S\" string."""
        sign = "-" if dd_angle < 0 else ""
        dd_angle = abs(dd_angle)
        d = int(dd_angle)
        m_float = (dd_angle - d) * 60
        m = int(m_float)
        s = (m_float - m) * 60
        # Handle rounding
        if s >= 59.995:
            s = 0; m += 1
        if m >= 60:
            m = 0; d += 1
        return f"{sign}{d}° {m:02d}' {s:05.2f}\""

    def handle_save_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "Image Files (*.png *.jpg *.pdf)")
        if file_path:
            self.plot_widget.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Success", f"Plot saved to {file_path}")

    def handle_import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not file_path: return
        
        df = import_csv_to_dataframe(file_path)
        if df is None:
            QMessageBox.critical(self, "Import Error", "Failed to read CSV.")
            return
            
        self.table.setRowCount(0)
        # Expected columns: Base Start, Base End, New Point, Angle @ Start, Angle @ End, Angle @ New, Direction
        for _, row in df.iterrows():
            r = self.table.rowCount()
            self.table.insertRow(r)
            cols = ["Base Start", "Base End", "New Point", "Angle @ Start", "Angle @ End", "Angle @ New", "Direction"]
            for i, col in enumerate(cols):
                val = str(row.iloc[i]) if i < len(row) else ""
                if i == 6: # Direction Combo
                    combo = QComboBox()
                    combo.addItems(["Left (Anti-Clockwise)", "Right (Clockwise)"])
                    # Try to match existing value
                    idx = 0 if "Left" in val else 1
                    combo.setCurrentIndex(idx)
                    self.table.setCellWidget(r, i, combo)
                else:
                    self.table.setItem(r, i, QTableWidgetItem(val))

    def handle_export_csv(self):
        if not self.stations:
            QMessageBox.warning(self, "Export Error", "No results to export.")
            return
            
        data = []
        for name, (e, n) in self.stations.items():
            data.append({"Station": name, "Easting": e, "Northing": n})
        
        df = pd.DataFrame(data)
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Results", "", "CSV Files (*.csv)")
        if file_path:
            export_dataframe_to_csv(df, file_path)
            QMessageBox.information(self, "Success", f"Results exported to {file_path}")

    def handle_export_kml(self):
        if not self.stations:
            QMessageBox.warning(self, "Export Error", "No coordinates to export.")
            return
            
        epsg, ok = QInputDialog.getInt(self, "Input EPSG", "Enter UTM Zone EPSG Code:", 32632)
        if not ok: return
        
        try:
            local_pts = [(coords[0], coords[1]) for coords in self.stations.values()]
            names = list(self.stations.keys())
            global_pts = convert_to_global(local_pts, epsg)
            
            kml_data = []
            for i, (lon, lat) in enumerate(global_pts):
                kml_data.append((names[i], lon, lat))
                
            file_path, _ = QFileDialog.getSaveFileName(self, "Export KML", "", "KML Files (*.kml)")
            if file_path:
                export_to_kml(file_path, kml_data)
                QMessageBox.information(self, "Success", f"KML exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def handle_export_pdf(self):
        if not self.results_display.toPlainText():
            QMessageBox.warning(self, "Export Error", "No report to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if file_path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            self.results_display.document().print(printer)
            QMessageBox.information(self, "Success", f"Report saved to {file_path}")

    def handle_import_quad_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not file_path: return
        df = import_csv_to_dataframe(file_path)
        if df is None or df.empty: return
        
        # Expecting a single row with columns matching input fields
        row = df.iloc[0]
        try:
            self.q_stn_a.setText(str(row.get('A', 'A')))
            self.q_stn_b.setText(str(row.get('B', 'B')))
            self.q_stn_c.setText(str(row.get('C', 'C')))
            self.q_stn_d.setText(str(row.get('D', 'D')))
            self.q_base_dist.setValue(float(row.get('BaseDist', 100)))
            self.q_base_az.setText(str(row.get('BaseAz', '90.0000')))
            self.ang_bac.setText(str(row.get('BAC', '')))
            self.ang_cad.setText(str(row.get('CAD', '')))
            self.ang_cbd.setText(str(row.get('CBD', '')))
            self.ang_dba.setText(str(row.get('DBA', '')))
            self.ang_dca.setText(str(row.get('DCA', '')))
            self.ang_acb.setText(str(row.get('ACB', '')))
            self.ang_adb.setText(str(row.get('ADB', '')))
            self.ang_bdc.setText(str(row.get('BDC', '')))
            QMessageBox.information(self, "Success", "Quadrilateral data imported.")
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Check CSV format: {e}")

    def handle_export_quad_csv(self):
        if not self.quad_stations:
            QMessageBox.warning(self, "Export Error", "No results to export.")
            return
        data = [{"Station": n, "Easting": d['e'], "Northing": d['n']} for n, d in self.quad_stations.items()]
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Quad Results", "", "CSV Files (*.csv)")
        if file_path:
            export_dataframe_to_csv(pd.DataFrame(data), file_path)
            QMessageBox.information(self, "Success", f"Saved to {file_path}")

    def handle_save_quad_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "Image Files (*.png *.jpg *.pdf)")
        if file_path:
            self.quad_plot.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Success", f"Plot saved to {file_path}")

    def handle_export_quad_kml(self):
        if not self.quad_stations:
            QMessageBox.warning(self, "Export Error", "No coordinates to export.")
            return
            
        epsg, ok = QInputDialog.getInt(self, "Input EPSG", "Enter UTM Zone EPSG Code:", 32632)
        if not ok: return
        
        try:
            # quad_stations values are dicts {'e': val, 'n': val, ...}
            local_pts = [(d['e'], d['n']) for d in self.quad_stations.values()]
            names = list(self.quad_stations.keys())
            global_pts = convert_to_global(local_pts, epsg)
            
            kml_data = []
            for i, (lon, lat) in enumerate(global_pts):
                kml_data.append((names[i], lon, lat))
                
            file_path, _ = QFileDialog.getSaveFileName(self, "Export KML", "", "KML Files (*.kml)")
            if file_path:
                export_to_kml(file_path, kml_data)
                QMessageBox.information(self, "Success", f"KML exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def handle_export_quad_pdf(self):
        if not self.quad_results.toPlainText():
            QMessageBox.warning(self, "Export Error", "No report to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if file_path:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            self.quad_results.document().print(printer)
            QMessageBox.information(self, "Success", f"Report saved to {file_path}")