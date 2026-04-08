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
import matplotlib.dates as mdates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QComboBox, QListWidget, QListWidgetItem,
    QPushButton, QAbstractItemView, QSizePolicy,
    QFileDialog, QMessageBox, QApplication
)
from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt

from benzintracker.database import models
from benzintracker import config
from benzintracker.translator import tr, translator


# ---------------------------------------------------------------------------------------------------
# Color Palette for the Lines (up to 8 Stations);
# ---------------------------------------------------------------------------------------------------
LINE_COLORS = [
    "#2196F3", "#4CAF50", "#FF9800", "#E91E63",
    "#9C27B0", "#00BCD4", "#FF5722", "#607D8B"
]

FUEL_OPTIONS = ["e5", "e10", "diesel"]
FUEL_LABELS = { "e5": "E5", "e10": "E10", "diesel": "Diesel" }

FIGSIZE_DEFAULT              = (8, 4)
STATION_SELECTION_MAX_HEIGHT = 100
CHART_LINEWIDTH              = 1.8
CHART_MARKER                 = "o"
CHART_MARKER_SIZE            = 3
FIGURE_EXPORT_DPI            = 150


def _period_options() -> dict:
    return {
        tr("stats.period_7"):          7,
        tr("stats.period_30"):        30,
        tr("stats.period_90"):        90,
        tr("stats.period_all"):     3650
    }


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
        self._data_text = None


    def clear(self):
        self.ax.clear()
        self._data_text = None


    def redraw(self):
        self.fig.canvas.draw()


    def set_date_range(self, date_from: str, date_to: str):
        if self._data_text is not None:
            try: self._data_text.remove()
            except Exception: pass

        self._data_text = self.fig.text(
            0.99, 0.01, f"{date_from} - {date_to}",
            ha="right", va="bottom", fontsize=7,
            alpha=0.6, transform=self.fig.transFigure
        )

    
    def export(self, parent=None):
        """
        Open a savefile dialog and export the stat.
        """
        default = f"chart_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.png"
        path, _ = QFileDialog.getSaveFileName(
            parent, tr("stats.export_dlg_title"), default,
            tr("stats.export_dlg_file_desc")
        )

        if not path: return

        try:
            self.fig.savefig(path, dpi=FIGURE_EXPORT_DPI, bbox_inches="tight")
            QMessageBox.information(
                parent, tr("stats.export_success_title"),
                tr("stats.export_success_message", path=path)
            )

        except Exception as e:
            QMessageBox.critical(
                parent, tr("stats.export_failed_title"),
                str(e)
            )


    def apply_theme(self, dark: bool):
        """
        Adapts the background and foreground colors according to the active theme.
        """
        palette = QApplication.instance().palette()
        bg = palette.color(QPalette.ColorRole.Base).name()
        fg = palette.color(QPalette.ColorRole.Text).name()
        grid = palette.color(QPalette.ColorRole.Mid).name()

        self.fig.patch.set_facecolor(bg)
        self.ax.set_facecolor(bg)
        self.ax.tick_params(colors=fg)
        self.ax.xaxis.label.set_color(fg)
        self.ax.yaxis.label.set_color(fg)
        self.ax.title.set_color(fg)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(grid)
        self.ax.grid(color=grid, linewidth=0.5)

        if self._data_text is not None:
            self._data_text.set_color(fg)

        self.redraw()



# ---------------------------------------------------------------------------------------------------
# Helper Functions;
# ---------------------------------------------------------------------------------------------------
def _fuel_combo() -> QComboBox:
    c = QComboBox()
    for key, label in FUEL_LABELS.items():
        c.addItem(label, userData=key)
    c.setCurrentText(FUEL_LABELS.get(config.DEFAULT_FUEL_TYPE, "E5"))

    return c


def _period_combo() -> QComboBox:
    c = QComboBox()
    for label, days in _period_options().items():
        c.addItem(label, userData=days)
    c.setCurrentIndex(0)

    return c


def _make_toolbar(with_period: bool = True, with_export: bool = True):
    """
    Create a toolbar row with fuel-combo and optionally period-combo, refresh-button and export-btn.
    Return (bar_layout, combo_fuel, combo_period, btn_export).
    combo_period and btn_export could be None.
    """
    bar = QHBoxLayout()
    combo_fuel = _fuel_combo()
    bar.addWidget(QLabel(tr("stats.label_fuel")))
    bar.addWidget(combo_fuel)

    combo_period = None
    if with_period:
        combo_period = _period_combo()
        bar.addSpacing(16)
        bar.addWidget(QLabel(tr("stats.label_period")))
        bar.addWidget(combo_period)

    bar.addStretch()

    btn_refresh = QPushButton(tr("stats.btn_refresh"))
    bar.addWidget(btn_refresh)

    btn_export = None
    if with_export:
        btn_export = QPushButton(tr("stats.btn_export"))
        btn_export.setObjectName("btn_secondary")
        bar.addWidget(btn_export)

    return bar, combo_fuel, combo_period, btn_refresh, btn_export



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

        bar, self.combo_fuel, self.combo_period, btn_refresh, btn_export = \
            _make_toolbar(with_period=True, with_export=True)

        btn_refresh.clicked.connect(self.refresh)
        btn_export.clicked.connect(lambda: self.canvas.export(self))
        root.addLayout(bar)

        # Stations Selection;
        root.addWidget(QLabel(tr("stats.label_stations")))
        self.station_list = QListWidget()
        self.station_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.station_list.setMaximumHeight(STATION_SELECTION_MAX_HEIGHT)
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

        station_ids = (
            [item.data(Qt.ItemDataRole.UserRole) for item in sel]
            if sel else
            [self.station_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(min(self.station_list.count(), 8))]
        )

        self.canvas.clear()
        ax = self.canvas.ax

        has_data = False
        all_dates = []
        for idx, sid in enumerate(station_ids[:8]):
            rows = models.get_price_history(sid, fuel, days)
            if not rows: continue

            times = [datetime.fromisoformat(r["recorded_at"]) for r in rows]
            prices = [r["price"] for r in rows]
            all_dates += [r["recorded_at"][:10] for r in rows]
            station = models.get_station_by_id(sid)
            label = station["name"] if station else sid[:8]

            color = LINE_COLORS[idx % len(LINE_COLORS)]
            ax.plot(
                times, prices, label=label, color=color,
                linewidth=CHART_LINEWIDTH,
                marker=CHART_MARKER,
                markersize=CHART_MARKER_SIZE
            )
            has_data = True

        if not has_data:
            ax.text(
                0.5, 0.5, tr("stats.no_data"), ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray"
            )

        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.canvas.fig.autofmt_xdate()
            ax.set_ylabel(tr("stats.ylabel_price_plain", fuel=FUEL_LABELS[fuel]))
            ax.legend(fontsize=9, framealpha=0.7)
            ax.grid(True, linewidth=0.5, alpha=0.5)

            if all_dates:
                self.canvas.set_date_range(min(all_dates), max(all_dates))

        self.canvas.apply_theme(self._dark)


    def update_data(self, _stations):
        self._populate_stations()
        self.refresh()

    
    def set_dark(self, dark: bool):
        self._dark = dark
        self.refresh()

    
    def retranslate(self):
        self._populate_stations()


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

        bar, self.combo_fuel, self.combo_period, btn_refresh, btn_export = \
            _make_toolbar(with_period=True, with_export=True)

        btn_refresh.clicked.connect(self.refresh)
        btn_export.clicked.connect(lambda: self.canvas.export(self))
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
                0.5, 0.5, tr("stats.no_data"), ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray"
            )

        else:
            dates = [datetime.strptime(r["day"], "%Y-%m-%d") for r in rows]
            prices = [r["avg_price"] for r in rows]
            ax.plot(
                dates, prices, color=LINE_COLORS[0],
                linewidth=CHART_LINEWIDTH,
                marker=CHART_MARKER,
                markersize=CHART_MARKER_SIZE
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
                    linewidth=1, alpha=0.6, label=tr("stats.legend_trend")
                )
                ax.legend(fontsize=9)

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.canvas.fig.autofmt_xdate()
            ax.set_ylabel(tr("stats.ylabel_price", fuel=FUEL_LABELS[fuel]))
            ax.grid(True, linewidth=0.5, alpha=0.5)
            self.canvas.set_date_range(rows[0]["day"], rows[-1]["day"])

        self.canvas.apply_theme(self._dark)


    def update_data(self, _stations):
        self.refresh()


    def set_dark(self, dark: bool):
        self._dark = dark
        self.refresh()


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

        bar, self.combo_fuel, self.combo_period, btn_refresh, btn_export = \
            _make_toolbar(with_period=True, with_export=True)
        
        btn_refresh.clicked.connect(self.refresh)
        btn_export.clicked.connect(lambda: self.canvas.export(self))
        root.addLayout(bar)

        self.canvas = MplCanvas(self)
        root.addWidget(self.canvas)


    def refresh(self):
        fuel = self.combo_fuel.currentData()
        days = self.combo_period.currentData()

        # AVG per station from the DB;
        averages = []

        for s in models.get_all_stations():
            rows = models.get_price_history(s["id"], fuel, days)
            if rows:
                avg = sum(r["price"] for r in rows) / len(rows)
                averages.append((s["name"], avg))

        self.canvas.clear()
        ax = self.canvas.ax

        if not averages:
            ax.text(
                0.5, 0.5, tr("stats.no_data"), ha="center", va="center",
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

            fg = QApplication.instance().palette().color(QPalette.ColorRole.Text).name()

            # Value at the end of the bar;
            for bar, price in zip(bars, prices):
                ax.text(
                    bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                    f"{price:.3f} €", va="center", fontsize=9, color=fg
                )

            ax.set_xlabel(tr("stats.xlabel_avg_price", fuel=FUEL_LABELS[fuel]))
            ax.grid(True, axis="x", linewidth=0.5, alpha=0.5)

            # X-Ax a bit wider for the label;
            if prices: ax.set_xlim(min(prices) * 0.998, max(prices) * 1.008)

            dates = models.get_date_range(fuel)
            if dates and dates[0]:
                self.canvas.set_date_range(dates[0][:10], dates[1][:10])

        self.canvas.apply_theme(self._dark)


    def update_data(self, _stations):
        self.refresh()


    def set_dark(self, dark: bool):
        self._dark = dark
        self.refresh()


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

        bar, self.combo_fuel, _, btn_refresh, btn_export = \
            _make_toolbar(with_period=False, with_export=True)

        btn_refresh.clicked.connect(self.refresh)
        btn_export.clicked.connect(lambda: self.canvas.export(self))
        root.addLayout(bar)

        self.label_hint = QLabel(
            tr("stats.hourly_locked_info", min_datapoints=self.MIN_DATAPOINTS)
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
            self.label_hint.setText(tr(
                    "stats.hourly_locked",
                    n=self.MIN_DATAPOINTS - total_points,
                    have=total_points,
                    need=self.MIN_DATAPOINTS
            ))
            ax.text(
                0.5, 0.5,
                tr("stats.hourly_locked_ax_text", n=self.MIN_DATAPOINTS - total_points),
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color="gray", multialignment="center"
            )

        else:
            self.label_hint.hide()
            hours = [r["hour"] for r in rows]
            prices = [r["avg_price"] for r in rows]

            ax.plot(
                hours, prices, color=LINE_COLORS[2],
                linewidth=CHART_LINEWIDTH,
                marker=CHART_MARKER,
                markersize=CHART_MARKER_SIZE
            )
            ax.fill_between(hours, prices, alpha=0.1, color=LINE_COLORS[2])

            # Mark the cheapest hour;
            min_idx = prices.index(min(prices))
            ax.annotate(
                tr("stats.hourly_cheapest", hour=f"{hours[min_idx]:02d}"),
                xy=(hours[min_idx], prices[min_idx]),
                xytext=(hours[min_idx] + 1.5, prices[min_idx] - 0.005),
                arrowprops=dict(arrowstyle="->", color="gray"),
                fontsize=9, color="gray"
            )

            ax.set_xlabel(tr("stats.xlabel_time"))
            ax.set_ylabel(tr("stats.xlabel_avg_price", fuel=FUEL_LABELS[fuel]))
            ax.set_xticks(range(0, 24, 2))
            ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)], rotation=45, ha="right")
            ax.grid(True, linewidth=0.5, alpha=0.5)

            dates = models.get_date_range(fuel)
            if dates and dates[0]:
                self.canvas.set_date_range(dates[0][:10], dates[1][:10])

        self.canvas.apply_theme(self._dark)


    def update_data(self, _stations):
        self.refresh()


    def set_dark(self, dark: bool):
        self._dark = dark
        self.refresh()



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
        translator.language_changed.connect(self.retranslate)


    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        self.sub_tabs = QTabWidget()

        self.chart_history = PriceHistoryChart(self)
        self.chart_daily = DailyAverageChart(self)
        self.chart_comparison = StationComparisonChart(self)
        self.chart_hourly = HourlyPriceChart(self)

        self.sub_tabs.addTab(self.chart_history, tr("stats.tab_history"))
        self.sub_tabs.addTab(self.chart_daily, tr("stats.tab_daily"))
        self.sub_tabs.addTab(self.chart_comparison, tr("stats.tab_comparison"))
        self.sub_tabs.addTab(self.chart_hourly, tr("stats.tab_hourly"))

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
        for i in range(self.sub_tabs.count()):
            widget = self.sub_tabs.widget(i)
            if hasattr(widget, "set_dark"):
                widget.set_dark(dark)


    def retranslate(self):
        self.sub_tabs.setTabText(0, tr("stats.tab_history"))
        self.sub_tabs.setTabText(1, tr("stats.tab_daily"))
        self.sub_tabs.setTabText(2, tr("stats.tab_comparison"))
        self.sub_tabs.setTabText(3, tr("stats.tab_hourly"))