"""
table_tab.py - Price table of all stations of the last refresh.

Features:
    - Columns: Name, Brand, City, Distance, E5, E10, Diesel, Status
    - Sortable via Click on the Column-Header
    - Filter: Show only open stations 
    - Cheapest cell for each fuel type is highlighted
    - Click on a row centeres onto the station on the map (Signal)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QCheckBox, QComboBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from benzintracker import config


# Rows of fuel type in order;
FUEL_COLS = ["e5", "e10", "diesel"]
FUEL_LABELS = { "e5": "E5", "e10": "E10", "diesel": "Diesel" }

# Highlight colors for cheapest price (agreeable with light / dark themes);
COLOR_BEST = QColor("#c8e6c9")
COLOR_OPEN = QColor("#4caf50")
COLOR_CLOSE = QColor("#9e9e9e")


class TableTab(QWidget):
    # Triggers when the user clicks on a row;
    # Contains the station_id and can later be used by the main window
    # to center the map onto the station;
    station_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stations: list[dict] = []
        self._build_ui()



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

        self.check_open_only = QCheckBox("Only Opened")
        self.check_open_only.setChecked(False)
        self.check_open_only.stateChanged.connect(self._apply_filter)

        self.combo_sort_fuel = QComboBox()
        self.combo_sort_fuel.addItem("Sort: Distance", userData="dist")
        for key, label in FUEL_LABELS.items():
            self.combo_sort_fuel.addItem(f"Sort: {label}", userData=key)
        self.combo_sort_fuel.currentIndexChanged.connect(self._apply_filter)

        layout.addWidget(self.check_open_only)
        layout.addSpacing(16)
        layout.addWidget(self.combo_sort_fuel)
        layout.addStretch()

        return bar

    
    def _build_table(self) -> QTableWidget:
        columns = ["Name", "Brand", "City", "Distance", "E5", "E10", "Diesel", "Status"]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        # Column Width;
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)                  # Name;
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)         # Brand;
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)         # City;
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)         # Distance;
        for col in range(4, 7):                                              # Price Columns;
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)         # Status;

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        #self.table.setEditTriggers(QTableWidget.NoEditTriggers)
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
                        item.setBackground(COLOR_BEST)
                        item.setFont(bold_font)

                else:
                    item = QTableWidgetItem("-")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.table.setItem(row_idx, col, item)

            # Status;
            status_text = "Opened" if s["is_open"] else "Closed"
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setForeground(
                COLOR_OPEN if s["is_open"] else COLOR_CLOSE
            )
            self.table.setItem(row_idx, 7, item_status)

        self.table.setSortingEnabled(True)
        self.label_count.setText(
            f"{len(stations)} Station(s)"
            + (" (filtered)" if self.check_open_only.isChecked() else "")
        )


    def _set_item(self, row: int, col: int, text: str, data=None):
        item = QTableWidgetItem(text)
        if data is not None: item.setData(Qt.ItemDataRole.UserRole, data)
        self.table.setItem(row, col, item)

    

    # ---------------------------------------------------------------------------------------------------
    # Slots;
    # ---------------------------------------------------------------------------------------------------
    def _on_row_selected(self):
        selected = self.table.selectedItems()
        if not selected: return

        row = selected[0].row()
        name_item = self.table.item(row, 0)

        if name_item:
            station_id = name_item.data(Qt.ItemDataRole.UserRole)
            if station_id: self.station_selected.emit(station_id)