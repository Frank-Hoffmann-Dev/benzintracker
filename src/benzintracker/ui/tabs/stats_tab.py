"""
stats_tab.py - Statistics with four matplotlib-charts.

Charts:
    1. Price History            Line chart, one line per choosen station
    2. Daily Average            Line chart, AVG prices of all stations per day
    3. Station Comparision      Bar chart, AVG of each station
    4. Daytime                  Line chart, AVG price per hour (available >= 50 data points)

Each chart lives in its own tab inside this tab.
Filter (fuel type, time period, stations) can be set individually per chart.

Matplotlib is embeded via 'FigureCanvasQTAgg' inside a QWidget, therefore no seperate window is required.
The chart is part of the GUI.
"""
from datetime import datetime

import matplotlib
matplotlib.use("QtAgg")             # Force the Qt backend;
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QComboBox, QListWidget, QListWidgetItem,
    QPushButton, QAbstractItemView, QSizePolicy
)
from PySide6.QtCore import Qt

from benzintracker.database import models
from benzintracker import config


# ---------------------------------------------------------------------------------------------------
# Color Palette for the Lines (up to 8 Stations);
# ---------------------------------------------------------------------------------------------------
LINE_COLORS = [
    "#2196F3", "#4CAF50", "#FF9800", "#E91E63",
    "#9C27B0", "#00BCD4", "#FF5722", "#607D8B"
]

PERIOD_OPTIONS = {
    "7 Days": 7, "30 Days": 30, "90 Days": 90, "All": 3650
}

FUEL_OPTIONS = ["e5", "e10", "diesel"]
FUEL_LABELS = { "e5": "E5", "e10": "E10", "diesel": "Diesel" }

FIGSIZE_DEFAULT = (8, 4)
STATION_SELECTION_LIST_MAX_HEIGHT = 100

CHART_PRICE_HISTORY_LINEWIDTH = 1.8
CHART_PRICE_HISTORY_MARKER = "o"
CHART_PRICE_HISTORY_MARKER_SIZE = 3

CHART_DAILY_AVG_LINEWIDTH = 2
CHART_DAILY_AVG_MARKER = "o"
CHART_DAILY_AVG_MARKER_SIZE = 4

CHART_HOURLY_AVG_LINEWIDTH = 2
CHART_HOURLY_AVG_MARKER = "o"
CHART_HOURLY_AVG_MARKER_SIZE = 5


class MplCanvas(FigureCanvas):
    """
    Light-weight widget hosting a matplotlib-figure.
    It is being used by each chart-tab.
    """
    def __init__(self, parent=None):
        self.fig = Figure(figsize=FIGSIZE_DEFAULT, tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


    def clear(self):
        self.ax.clear()


    def redraw(self):
        self.fig.canvas.draw()


    def apply_theme(self, dark: bool):
        """
        Adapts the background and foreground colors according to the active theme.
        """
        bg = "#1e1e1e" if dark else "#ffffff"
        fg = "#e0e0e0" if dark else "#1a1a1a"
        grid = "#3a3a3a" if dark else "#e0e0e0"

        self.fig.patch.set_facecolor(bg)
        self.ax.set_facecolor(bg)
        self.ax.tick_params(colors=fg)
        self.ax.xaxis.label.set_color(fg)
        self.ax.yaxis.label.set_color(fg)
        self.ax.title.set_color(fg)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(grid)
        self.ax.grid(color=grid, linewidth=0.5)

        self.redraw()



# ---------------------------------------------------------------------------------------------------
# Single Chart Widget;
# ---------------------------------------------------------------------------------------------------
class PriceHistoryChart(QWidget):
    """
    Chart 1: Price History
    Shows the price history of one or multiple stations through time.
    One line per station with colors from 'LINE_COLORS'.
    Filter: fuel type, time period, stations (multiple selections possible).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = False
        self._build_ui()


    def _build_ui(self):
        root = QVBoxLayout(self)

        # Toolbar;
        bar = QHBoxLayout()
        self.combo_fuel = self._fuel_combo()
        self.combo_period = self._period_combo()

        bar.addWidget(QLabel("Fuel Type:"))
        bar.addWidget(self.combo_fuel)
        bar.addSpacing(16)
        bar.addWidget(QLabel("Period:"))
        bar.addWidget(self.combo_period)
        bar.addStretch()

        btn = QPushButton("Refresh")
        btn.clicked.connect(self.refresh)
        bar.addWidget(btn)
        root.addLayout(bar)

        # Stations Selection;
        root.addWidget(QLabel("Stations (multiple selection)"))
        self.station_list = QListWidget()
        self.station_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.station_list.setMaximumHeight(STATION_SELECTION_LIST_MAX_HEIGHT)
        root.addWidget(self.station_list)

        # Canvas;
        self.canvas = MplCanvas(self)
        root.addWidget(self.canvas)

        self._populate_stations()


    def _populate_stations(self):
        self.station_list.clear()

        for s in models.get_all_stations():
            item = QListWidgetItem(f"{s['name']} ({s.get('brand', '')})")
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            self.station_list.addItem(item)


    def refresh(self):
        fuel = self.combo_fuel.currentData()
        days = self.combo_period.currentData()
        sel = self.station_list.selectedItems()

        # If no selection -> select all stations (max. 8);
        if sel: station_ids = [item.data(Qt.ItemDataRole.UserRole) for item in sel]
        else:
            station_ids = [
                self.station_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(min(self.station_list.count(), 8))
            ]

        self.canvas.clear()
        ax = self.canvas.ax

        has_data = False
        for idx, sid in enumerate(station_ids[:8]):
            rows = models.get_price_history(sid, fuel, days)
            if not rows: continue

            times = [datetime.fromisoformat(r["recorded_at"]) for r in rows]
            prices = [r["price"] for r in rows]
            station = models.get_station_by_id(sid)
            label = station["name"] if station else sid[:8]
            color = LINE_COLORS[idx % len(LINE_COLORS)]

            ax.plot(
                times, prices, label=label, color=color,
                linewidth=CHART_PRICE_HISTORY_LINEWIDTH,
                marker=CHART_PRICE_HISTORY_MARKER,
                markersize=CHART_PRICE_HISTORY_MARKER_SIZE
            )
            has_data = True

        if not has_data:
            ax.text(
                0.5, 0.5, "No Data...", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray"
            )

        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.canvas.fig.autofmt_xdate()
            ax.set_ylabel(f"{FUEL_LABELS[fuel]} Price in €")
            ax.legend(fontsize=9, framealpha=0.7)
            ax.grid(True, linewidth=0.5, alpha=0.5)

        self.canvas.apply_theme(self._dark)


    def update_data(self, _stations):
        self._populate_stations()
        self.refresh()

    
    def set_dark(self, dark: bool):
        self._dark = dark
        self.canvas.apply_theme


    @staticmethod
    def _fuel_combo():
        c = QComboBox()
        for key, label in FUEL_LABELS.items():
            c.addItem(label, userData=key)
        c.setCurrentText(FUEL_LABELS.get(config.DEFAULT_FUEL_TYPE, "E5"))

        return c

    
    @staticmethod
    def _period_combo():
        c = QComboBox()
        for label, days in PERIOD_OPTIONS.items():
            c.addItem(label, userData=days)
        c.setCurrentIndex(0)        # Default: 7 Days;

        return c


class DailyAverageChart(QWidget):
    """
    Chart 2: Average Price per Day
    Aggregate over all stations and show the general price trend in the area.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = False
        self._build_ui()


    def _build_ui(self):
        root = QVBoxLayout(self)

        bar = QHBoxLayout()
        self.combo_fuel = PriceHistoryChart._fuel_combo()
        self.combo_period = PriceHistoryChart._period_combo()
        bar.addWidget(QLabel("Fuel Type:"))
        bar.addWidget(self.combo_fuel)
        bar.addSpacing(16)
        bar.addWidget(QLabel("Period:"))
        bar.addWidget(self.combo_period)
        bar.addStretch()

        btn = QPushButton("Refresh")
        btn.clicked.connect(self.refresh)
        bar.addWidget(btn)
        root.addLayout(bar)

        self.canvas = MplCanvas(self)
        root.addWidget(self.canvas)


    def refresh(self):
        fuel = self.combo_fuel.currentData()
        days = self.combo_period.currentData()
        rows = models.get_average_prices_per_day(fuel, days)

        self.canvas.clear()
        ax = self.canvas.ax

        if not rows:
            ax.text(
                0.5, 0.5, "No Data...", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray"
            )

        else:
            dates = [datetime.strptime(r["day"], "%d.%m.%Y") for r in rows]
            prices = [r["avg_price"] for r in rows]
            ax.plot(
                dates, prices, color=LINE_COLORS[0],
                linewidth=CHART_DAILY_AVG_LINEWIDTH,
                marker=CHART_DAILY_AVG_MARKER,
                markersize=CHART_DAILY_AVG_MARKER_SIZE
            )
            ax.fill_between(dates, prices, alpha=0.1, color=LINE_COLORS[0])

            # Simple trend line;
            if len(dates) >= 3:
                import numpy as np

                x_num = mdates.date2num(dates)
                z = np.polyfit(x_num, prices, 1)
                p = np.poly1d(z)

                ax.plot(
                    dates, p(x_num), "--", color="gray",
                    linewidth=1, alpha=0.6, label="Trend"
                )
                ax.legend(fontsize=9)

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.canvas.fig.autofmt_xdate()
            ax.set_ylabel(f"AVG {FUEL_LABELS[fuel]} Price in €")
            ax.grid(True, linewidth=0.5, alpha=0.5)

        self.canvas.apply_theme(self._dark)


    def update_data(self, _stations):
        self.refresh()


    def set_dark(self, dark: bool):
        self._dark = dark
        self.canvas.apply_theme(dark)


class StationComparisonChart(QWidget):
    """
    Chart 3: Price Comparison between Stations
    Bar chart with the average prices of each station in the selected period.
    The cheapest station is highlighted.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = False
        self._build_ui()


    def _build_ui(self):
        root = QVBoxLayout(self)

        bar = QHBoxLayout()
        self.combo_fuel = PriceHistoryChart._fuel_combo()
        self.combo_period = PriceHistoryChart._period_combo()
        bar.addWidget(QLabel("Fuel Type:"))
        bar.addWidget(self.combo_fuel)
        bar.addSpacing(16)
        bar.addWidget(QLabel("Period:"))
        bar.addWidget(self.combo_period)
        bar.addStretch()

        btn = QPushButton("Refresh")
        btn.clicked.connect(self.refresh)
        bar.addWidget(btn)
        root.addLayout(bar)

        self.canvas = MplCanvas(self)
        root.addWidget(self.canvas)


    def refresh(self):
        fuel = self.combo_fuel.currentData()
        days = self.combo_period.currentData()

        # AVG per station from the DB;
        stations = models.get_all_stations()
        averages = []

        for s in stations:
            rows = models.get_price_history(s["id"], fuel, days)
            if rows:
                avg = sum(r["price"] for r in rows) / len(rows)
                averages.append((s["name"], avg))

        self.canvas.clear()
        ax = self.canvas.ax

        if not averages:
            ax.text(
                0.5, 0.5, "No Data...", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray"
            )

        else:
            # Sort by average price;
            averages.sort(key=lambda x: x[1])
            names = [a[0] for a in averages]
            prices = [a[1] for a in averages]

            # Cheapest green, the rest blue;
            colors = ["#4CAF50"] + [LINE_COLORS[0]] * (len(prices) - 1)
            bars = ax.barh(names, prices, color=colors, height=0.6)

            # Value at the end of the bar;
            for bar, price in zip(bars, prices):
                ax.text(
                    bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                    f"{price:.3f} €", va="center", fontsize=9
                )

            ax.set_xlabel(f"AVG {FUEL_LABELS[fuel]} Price in €")
            ax.grid(True, axis="x", linewidth=0.5, alpha=0.5)

            # X-Ax a bit wider for the label;
            if prices: ax.set_xlim(min(prices) * 0.998, max(prices) * 1.008)

        self.canvas.apply_theme(self._dark)


    def update_data(self, _stations):
        self.refresh()


    def set_dark(self, dark: bool):
        self._dark = dark
        self.canvas.apply_theme(dark)


class HourlyPriceChart(QWidget):
    """
    Chart 4: Daytime Analysis
    Show the AVG price per hour of the day over all stations.
    It is only showed when there are at least 50 data points, otherwise the chart would be unreliable.
    """
    MIN_DATAPOINTS = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = False
        self._build_ui()


    def _build_ui(self):
        root =QVBoxLayout(self)

        bar = QHBoxLayout()
        self.combo_fuel = PriceHistoryChart._fuel_combo()
        bar.addWidget(QLabel("Fuel Type:"))
        bar.addWidget(self.combo_fuel)
        bar.addStretch()

        btn = QPushButton("Refresh")
        btn.clicked.connect(self.refresh)
        bar.addWidget(btn)
        
        root.addLayout(bar)

        self.label_hint = QLabel(
            f"This Chart needs at least {self.MIN_DATAPOINTS}. "
            "The Chart is generated automatically once enough data is collected."
        )
        self.label_hint.setObjectName("label_status")
        self.label_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.label_hint)

        self.canvas = MplCanvas(self)
        root.addWidget(self.canvas)


    def refresh(self):
        fuel = self.combo_fuel.currentData()

        rows = models.get_hourly_averages(fuel)
        total_points = sum(r["cnt"] for r in rows) if rows else 0

        self.canvas.clear()
        ax = self.canvas.ax

        if total_points < self.MIN_DATAPOINTS:
            self.label_hint.show()
            self.label_hint.setText(
                f"{self.MIN_DATAPOINTS - total_points} until the Chart is available. "
                f"Daytime Analysis ({total_points}/{self.MIN_DATAPOINTS})"
            )
            ax.text(
                0.5, 0.5,
                f"{self.MIN_DATAPOINTS - total_points} until the Chart is available. "
                f"Daytime Analysis ({total_points}/{self.MIN_DATAPOINTS})",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color="gray", multialignment="center"
            )

        else:
            self.label_hint.hide()
            hours = [r["hour"] for r in rows]
            prices = [r["avg_price"] for r in rows]

            ax.plot(
                hours, prices, color=LINE_COLORS[2],
                linewidth=CHART_HOURLY_AVG_LINEWIDTH,
                marker=CHART_HOURLY_AVG_MARKER,
                markersize=CHART_HOURLY_AVG_MARKER_SIZE
            )
            ax.fill_between(hours, prices, alpha=0.1, color=LINE_COLORS[2])

            # Mark the cheapest hour;
            min_idx = prices.index(min(prices))
            ax.annotate(
                f"Cheapest Period\n{hours[min_idx]:02d}:00 Uhr",
                xy=(hours[min_idx], prices[min_idx]),
                xytext=(hours[min_idx] + 1.5, prices[min_idx] - 0.005),
                arrowprops=dict(arrowstyle="->", color="gray"),
                fontsize=9, color="gray"
            )

            ax.set_xlabel("Time")
            ax.set_ylabel(f"AVG {FUEL_LABELS[fuel]} Price in €")
            ax.set_xticks(range(0, 24, 2))
            ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)], rotation=45, ha="right")
            ax.grid(True, linewidth=0.5, alpha=0.5)

        self.canvas.apply_theme(self._dark)


    def update_data(self, _stations):
        self.refresh()


    def set_dark(self, dark: bool):
        self._dark = dark
        self.canvas.apply_theme(dark)



# ---------------------------------------------------------------------------------------------------
# StatsTab - holds all four Charts;
# ---------------------------------------------------------------------------------------------------
class StatsTab(QWidget):
    """
    Main Widget of the statistics tabs.
    Contains four sub-tabs, one for each chart.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = False
        self._build_ui()


    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        self.sub_tabs = QTabWidget()

        self.chart_history = PriceHistoryChart(self)
        self.chart_daily = DailyAverageChart(self)
        self.chart_comparison = StationComparisonChart(self)
        self.chart_hourly = HourlyPriceChart(self)

        self.sub_tabs.addTab(self.chart_history, "Price History")
        self.sub_tabs.addTab(self.chart_daily, "Daily Average")
        self.sub_tabs.addTab(self.chart_comparison, "Station Comparison")
        self.sub_tabs.addTab(self.chart_hourly, "Hourly Analysis")

        root.addWidget(self.sub_tabs)

        # Refresh automatically when changing tabs;
        self.sub_tabs.currentChanged.connect(self._on_tab_changed)


    def _on_tab_changed(self, index: int):
        widget = self.sub_tabs.widget(index)
        if hasattr(widget, "refresh"):
            widget.refresh()


    def update_data(self, stations: list[dict]):
        """
        Called by the main window after each API refresh.
        """
        current = self.sub_tabs.currentWidget()
        if hasattr(current, "update_data"):
            current.update_data(stations)


    def set_theme(self, dark: bool):
        """
        Called by the main window when the theme is changed.
        Updates the currently visible chart.
        """
        self._dark = dark
        current = self.sub_tabs.currentWidget()
        if hasattr(current, "set_dark"):
            current.set_dark(dark)