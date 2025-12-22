from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDoubleSpinBox, QHeaderView, QMessageBox
)
from core.trigonometric_leveling import calculate_trig_levels

class TrigLevelingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # --- Left: Inputs ---
        left_layout = QVBoxLayout()
        
        # Station Setup
        stn_group = QGroupBox("Instrument Station")
        stn_layout = QVBoxLayout(stn_group)
        
        r1 = QHBoxLayout()
        self.stn_elev = QDoubleSpinBox(); self.stn_elev.setRange(-9999, 99999); self.stn_elev.setValue(100.0)
        self.hi = QDoubleSpinBox(); self.hi.setRange(0, 10); self.hi.setValue(1.500)
        
        r1.addWidget(QLabel("Station Elev:"))
        r1.addWidget(self.stn_elev)
        r1.addWidget(QLabel("HI:"))
        r1.addWidget(self.hi)
        stn_layout.addLayout(r1)
        left_layout.addWidget(stn_group)

        # Observations Table
        obs_group = QGroupBox("Observations")
        obs_layout = QVBoxLayout(obs_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Target", "Horiz. Dist", "Zenith Angle", "Target Height"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        obs_layout.addWidget(self.table)
        
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Add Row")
        self.btn_add.clicked.connect(self.add_row)
        btn_row.addWidget(self.btn_add)
        obs_layout.addLayout(btn_row)
        
        left_layout.addWidget(obs_group)

        # --- Right: Results ---
        right_layout = QVBoxLayout()
        
        self.btn_calc = QPushButton("Calculate")
        self.btn_calc.setStyleSheet("background-color: #28A745; color: white; font-weight: bold; padding: 10px;")
        self.btn_calc.clicked.connect(self.calculate)
        right_layout.addWidget(self.btn_calc)
        
        res_group = QGroupBox("Results")
        res_layout = QVBoxLayout(res_group)
        self.res_table = QTableWidget()
        self.res_table.setColumnCount(2)
        self.res_table.setHorizontalHeaderLabels(["Target", "Elevation"])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        res_layout.addWidget(self.res_table)
        right_layout.addWidget(res_group)

        layout.addLayout(left_layout, 6)
        layout.addLayout(right_layout, 4)
        self.add_row()

    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(f"T{r+1}"))
        self.table.setItem(r, 1, QTableWidgetItem("0.00"))
        self.table.setItem(r, 2, QTableWidgetItem("90.0000")) # Default Zenith
        self.table.setItem(r, 3, QTableWidgetItem("0.00"))

    def calculate(self):
        obs_list = []
        try:
            for r in range(self.table.rowCount()):
                t = self.table.item(r, 0).text()
                hd = self.table.item(r, 1).text()
                va = self.table.item(r, 2).text()
                th = self.table.item(r, 3).text()
                obs_list.append({'target': t, 'hd': hd, 'va': va, 'th': th})
            
            results = calculate_trig_levels(self.stn_elev.value(), self.hi.value(), obs_list)
            
            self.res_table.setRowCount(len(results))
            for i, res in enumerate(results):
                self.res_table.setItem(i, 0, QTableWidgetItem(res['target']))
                self.res_table.setItem(i, 1, QTableWidgetItem(f"{res['elevation']:.4f}"))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))