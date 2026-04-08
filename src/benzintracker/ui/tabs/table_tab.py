"""
table_tab.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: Price table of all stations of the last refresh.
=========================================================================================

Features:
    - Columns: Name, Brand, City, Distance, E5, E10, Diesel, Status
    - Sortable via Click on the Column-Header
    - Filter: Show only open stations 
    - Cheapest cell for each fuel type is highlighted
    - Click on a row centeres onto the station on the map (Signal)
"""
import csv
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QPushButton, QLabel, QCheckBox, QComboBox, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPalette

from benzintracker import config
from benzintracker.translator import tr, translator


# Rows of fuel type in order;
FUEL_COLS = ["e5", "e10", "diesel"]
FUEL_LABELS = { "e5": "E5", "e10": "E10", "diesel": "Diesel" }

# Highlight colors for cheapest price (agreeable with light / dark themes);
COLOR_OPEN = QColor("#4caf50")
COLOR_CLOSE = QColor("#9e9e9e")


def _color_best() -> QColor:
    base = QApplication.instance().palette().color(QPalette.ColorRole.Base)
    if base.lightness() < 128: return QColor("#1b5e20")
    return QColor("#c8e6c9")


def _text_on_best() -> QColor:
    base = QApplication.instance().palette().color(QPalette.ColorRole.Base)
    if base.lightness() < 128: return QColor("#a5d6a7")
    return QColor("#1b5e20")


class TableTab(QWidget):
    # Triggers when the user clicks on a row;
    # Contains the station_id and can later be used by the main window
    # to center the map onto the station;
    station_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stations: list[dict] = []
        self._build_ui()
        translator.language_changed.connect(self.retranslate)



    # ---------------------------------------------------------------------------------------------------
    # Build UI;
    # ---------------------------------------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_table())
        root.addWidget(self._build_footer())


    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.check_open_only = QCheckBox(tr("table.open_only"))
        self.check_open_only.setChecked(False)
        self.check_open_only.stateChanged.connect(self._apply_filter)

        self.combo_sort_fuel = QComboBox()
        self.combo_sort_fuel.addItem(tr("table.sort_dist"), userData="dist")
        for key, label in FUEL_LABELS.items():
            self.combo_sort_fuel.addItem(tr("table.sort_fuel", fuel=label), userData=key)
        self.combo_sort_fuel.currentIndexChanged.connect(self._apply_filter)

        # Export;
        self.btn_export = QPushButton(tr("table.btn_cvs_export"))
        self.btn_export.setObjectName("btn_secondary")
        self.btn_export.clicked.connect(self._export_csv)

        layout.addWidget(self.check_open_only)
        layout.addSpacing(16)
        layout.addWidget(self.combo_sort_fuel)
        layout.addStretch()
        layout.addWidget(self.btn_export)

        return bar

    
    def _build_table(self) -> QTableWidget:
        columns = [
            tr("table.col_name"), tr("table.col_brand"), tr("table.col_city"),
            tr("table.col_dist"), tr("table.col_e5"), tr("table.col_e10"),
            tr("table.col_diesel"), tr("table.col_status")
        ]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        # Column Width;
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)                  # Name;
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)         # Brand;
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)         # City;
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)         # Distance;
        for col in range(4, 7):                                                         # Price Columns;
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)         # Status;

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)

        self.table.itemSelectionChanged.connect(self._on_row_selected)

        return self.table


    def _build_footer(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label_count = QLabel("")
        self.label_count.setObjectName("label_status")
        layout.addWidget(self.label_count)
        layout.addStretch()

        return bar
    


    # ---------------------------------------------------------------------------------------------------
    # Public Interface;
    # ---------------------------------------------------------------------------------------------------
    def update_data(self, stations: list[dict]):
        """
        Is being called by the main window after each refresh.
        """
        self._stations = stations
        self._apply_filter()
    


    # ---------------------------------------------------------------------------------------------------
    # Fill the Table;
    # ---------------------------------------------------------------------------------------------------
    def _apply_filter(self):
        """
        Filter, sort the stations and refill the table.
        """
        data = self._stations

        # Filter: only opened stations;
        if self.check_open_only.isChecked():
            data = [s for s in data if s["is_open"]]

        # Sorting;
        sort_key = self.combo_sort_fuel.currentData()
        if sort_key == "dist": data = sorted(data, key=lambda s: s.get("dist", 0))
        else: data = sorted(data, key=lambda s: s["prices"].get(sort_key) or float("inf"))

        self._fill_table(data)


    def _fill_table(self, stations: list[dict]):
        """
        Write the stations into the table and highlight the cheapest price.
        """
        # Deactivate the sorting while filling the table for performance;
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        # Calculate the cheapest price for each fuel type;
        best: dict[str, float] = {}
        for fuel in FUEL_COLS:
            prices = [s["prices"].get(fuel) for s in stations if s["prices"].get(fuel)]
            if prices: best[fuel] = min(prices)

        bold_font = QFont()
        bold_font.setBold(True)

        for row_idx, s in enumerate(stations):
            self.table.insertRow(row_idx)

            self._set_item(row_idx, 0, s.get("name", ""), data=s["id"])
            self._set_item(row_idx, 1, s.get("brand", "-"))
            self._set_item(row_idx, 2, s.get("city", "-"))

            dist = s.get("dist")
            dist_text = f"{dist:.1f} km" if dist is not None else "-"
            item_dist = QTableWidgetItem(dist_text)
            item_dist.setData(Qt.ItemDataRole.UserRole, dist or 0)
            item_dist.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 3, item_dist)

            # Price Columns;
            for col_offset, fuel in enumerate(FUEL_COLS):
                col = 4 + col_offset
                price = s["prices"].get(fuel)

                if price is not None:
                    text = f"{price:.3f} €"
                    item = QTableWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, price)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                    # Highlight cheapest price;
                    if fuel in best and price == best[fuel]:
                        item.setBackground(_color_best())
                        item.setForeground(_text_on_best())
                        item.setFont(bold_font)

                else:
                    item = QTableWidgetItem("-")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.table.setItem(row_idx, col, item)

            # Status;
            status_text = tr("table.open") if s["is_open"] else tr("table.closed")
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setForeground(
                COLOR_OPEN if s["is_open"] else COLOR_CLOSE
            )
            self.table.setItem(row_idx, 7, item_status)

        self.table.setSortingEnabled(True)
        self.label_count.setText(
            tr("table.count", n=len(stations))
            + (f" {tr("table.count_filtered")}" if self.check_open_only.isChecked() else "")
        )


    def _set_item(self, row: int, col: int, text: str, data=None):
        item = QTableWidgetItem(text)
        if data is not None: item.setData(Qt.ItemDataRole.UserRole, data)
        self.table.setItem(row, col, item)

    

    # ---------------------------------------------------------------------------------------------------
    # Slots;
    # ---------------------------------------------------------------------------------------------------
    def retranslate(self):
        self.check_open_only.setText(tr("table.open_only"))
        current_data = self.combo_sort_fuel.currentData()
        self.combo_sort_fuel.blockSignals(True)
        self.combo_sort_fuel.clear()
        self.combo_sort_fuel.addItem(tr("table.sort_dist"), userData="dist")
        for key, label in FUEL_LABELS.items():
            self.combo_sort_fuel.addItem(tr("table.sort_fuel", fuel=label), userData=key)
        
        idx = self.combo_sort_fuel.findData(current_data)
        self.combo_sort_fuel.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_sort_fuel.blockSignals(False)
        self.btn_export.setText(tr("table.btn_cvs_export"))

        columns = [
            tr("table.col_name"), tr("table.col_brand"), tr("table.col_city"),
            tr("table.col_dist"), tr("table.col_e5"), tr("table.col_e10"),
            tr("table.col_diesel"), tr("table.col_status")
        ]
        self.table.setHorizontalHeaderLabels(columns)


    def _export_csv(self):
        """
        Export the currently visible table rows to CSV.
        """
        if self.table.rowCount() == 0:
            QMessageBox.information(
                self, tr("table.dlg_export_title"),
                tr("table.dlg_export_message_no_data")
            )
            return

        default_name = f"{tr("table.cvs_export_default_name")}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, tr("table.csv_export_filedlg_title"), default_name,
            tr("table.csv_export_filedlg_file_desc")
        )

        if not path: return

        # Header;
        headers = [
            self.table.horizontalHeaderItem(col).text()
            for col in range(self.table.columnCount())
        ]

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                # 'utf-8-sig': BOM for excel to open the file correctly;
                writer = csv.writer(f, delimiter=";")
                writer.writerow(headers)

                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")

                    writer.writerow(row_data)

                QMessageBox.information(
                    self, tr("table.dlg_export_title"),
                    tr("table.dlg_export_message_success", path=path)
                )

        except OSError as e:
            QMessageBox.critical(self, tr("table.dlg_export_failed_title"), str(e))


    def _on_row_selected(self):
        selected = self.table.selectedItems()
        if not selected: return

        row = selected[0].row()
        name_item = self.table.item(row, 0)

        if name_item:
            station_id = name_item.data(Qt.ItemDataRole.UserRole)
            if station_id: self.station_selected.emit(station_id)