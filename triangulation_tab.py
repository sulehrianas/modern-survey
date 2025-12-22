from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDoubleSpinBox, QHeaderView, QMessageBox, QComboBox
)
from core.triangulation import calculate_simple_triangulation

class TriangulationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Baseline Input
        base_group = QGroupBox("Baseline Setup")
        base_layout = QHBoxLayout(base_group)
        
        self.start_e = QDoubleSpinBox(); self.start_e.setRange(-999999, 999999); self.start_e.setValue(500000)
        self.start_n = QDoubleSpinBox(); self.start_n.setRange(-9999999, 9999999); self.start_n.setValue(4000000)
        self.base_dist = QDoubleSpinBox(); self.base_dist.setRange(0, 99999); self.base_dist.setValue(100.0)
        self.base_az = QDoubleSpinBox(); self.base_az.setRange(0, 360); self.base_az.setValue(45.0)
        
        base_layout.addWidget(QLabel("Start E:"))
        base_layout.addWidget(self.start_e)
        base_layout.addWidget(QLabel("Start N:"))
        base_layout.addWidget(self.start_n)
        base_layout.addWidget(QLabel("Base Dist:"))
        base_layout.addWidget(self.base_dist)
        base_layout.addWidget(QLabel("Base Azimuth:"))
        base_layout.addWidget(self.base_az)
        layout.addWidget(base_group)

        # Triangles Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["P1", "P2", "P3", "Angle 1", "Angle 2", "Angle 3", "Direction"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Triangle")
        self.btn_add.clicked.connect(self.add_row)
        self.btn_calc = QPushButton("Calculate Network")
        self.btn_calc.clicked.connect(self.calculate)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_calc)
        layout.addLayout(btn_layout)

        # Results
        self.res_table = QTableWidget()
        self.res_table.setColumnCount(3)
        self.res_table.setHorizontalHeaderLabels(["Station", "Easting", "Northing"])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.res_table)
        
        self.add_row()

    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem("A"))
        self.table.setItem(r, 1, QTableWidgetItem("B"))
        self.table.setItem(r, 2, QTableWidgetItem("C"))
        self.table.setItem(r, 3, QTableWidgetItem("60.0000"))
        self.table.setItem(r, 4, QTableWidgetItem("60.0000"))
        self.table.setItem(r, 5, QTableWidgetItem("60.0000"))
        
        cb = QComboBox()
        cb.addItems(["Left", "Right"])
        self.table.setCellWidget(r, 6, cb)

    def calculate(self):
        triangles = []
        try:
            for r in range(self.table.rowCount()):
                tri = {
                    'p1': self.table.item(r, 0).text(),
                    'p2': self.table.item(r, 1).text(),
                    'p3': self.table.item(r, 2).text(),
                    'a1': self.table.item(r, 3).text(),
                    'a2': self.table.item(r, 4).text(),
                    'a3': self.table.item(r, 5).text(),
                    'dir': self.table.cellWidget(r, 6).currentText()
                }
                triangles.append(tri)

            stations, _ = calculate_simple_triangulation(
                self.start_e.value(), self.start_n.value(),
                self.base_dist.value(), str(self.base_az.value()), triangles
            )
            
            self.res_table.setRowCount(len(stations))
            for i, (name, coords) in enumerate(stations.items()):
                self.res_table.setItem(i, 0, QTableWidgetItem(name))
                self.res_table.setItem(i, 1, QTableWidgetItem(f"{coords[0]:.3f}"))
                self.res_table.setItem(i, 2, QTableWidgetItem(f"{coords[1]:.3f}"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))