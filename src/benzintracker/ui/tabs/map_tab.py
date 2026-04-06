"""
map_tab.py - Mapview via Folium + QWebEngineView.

Procedure:
    1. update_data(stations) is being called by the main window with each refresh
    2. _build_map() creates a folium-map as HTML-String
    3. QWebEngineView loads the HTML-String directly (no temp files necessary)

Marker Colors:
    - green     -> Station open
    - grey      -> Station closed
    - blue      -> Own location

Popup for each marker:
    Name, Brand, Address, Distance, E5 / E10 / Diesel
"""
import folium

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineProfile

from benzintracker.database import models
from benzintracker import config


TOOLBAR_HEIGHT = 44
MAP_CENTER = (51.0, 10.0)
MAP_ZOOM_LEVEL = 6
MAP_ZOOM_START_LEVEL = 8


# Colors for the fuel type badges in the popup;
FUEL_COLORS = {
    "e5":       "4caf50",
    "e10":      "2196f3",
    "diesel":   "ff9800"
}

FUEL_LABELS = {
    "e5":       "E5",
    "e10":      "E10",
    "diesel":   "Diesel"
}


class _RefererInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Sets the referer-header for all tile-requests.
    Without the header OSM, CartoDB and other tile-provider block requests.
    """
    def interceptRequest(self, info):
        info.setHttpHeader(b"Referer", b"https://benzintracker.app")
        info.setHttpHeader(b"User-Agent", b"benzintracker/0.1.0 (desktop)")


class MapTab(QWidget):
    TILES_LIGHT = "CartoDB Positron"
    TILES_DARK = "CartoDB DarkMatter"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stations: list[dict] = []
        self._dark = False
        self._current_location: dict | None = models.get_default_location()

        # Install the interceptor onto the default profile;
        # It must be set before _build_ui() as the QWebEngineView references the profile at creation;
        self._interceptor = _RefererInterceptor()
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self._interceptor)

        self._build_ui()
        self._show_location_or_empty()

    
    
    # ---------------------------------------------------------------------------------------------------
    # UI;
    # ---------------------------------------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar;
        toolbar = QWidget()
        toolbar.setFixedHeight(TOOLBAR_HEIGHT)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        self.label_count = QLabel("No Data")
        self.label_count.setObjectName("label_status")

        self.combo_fuel = QComboBox()
        self.combo_fuel.addItems(["E5", "E10", "Diesel", "All"])
        self.combo_fuel.setCurrentText(
            config.DEFAULT_FUEL_TYPE.upper()
            if config.DEFAULT_FUEL_TYPE in ("e5", "e10") else "Diesel"
        )
        self.combo_fuel.currentTextChanged.connect(self._on_filter_changed)

        btn_center = QPushButton("Centered")
        btn_center.setObjectName("btn_secondary")
        btn_center.clicked.connect(self._center_map)

        toolbar_layout.addWidget(QLabel("Display:"))
        toolbar_layout.addWidget(self.combo_fuel)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.label_count)
        toolbar_layout.addWidget(btn_center)

        # Map;
        self.web_view = QWebEngineView()

        root.addWidget(toolbar)
        root.addWidget(self.web_view, stretch=1)
    


    # ---------------------------------------------------------------------------------------------------
    # Public Interface;
    # ---------------------------------------------------------------------------------------------------
    def update_data(self, stations: list[dict]):
        """
        Called by the main window after each refresh.
        """
        self._stations = stations
        self._current_location = models.get_default_location()
        self._render_map()
    


    # ---------------------------------------------------------------------------------------------------
    # Render Map;
    # ---------------------------------------------------------------------------------------------------
    def _show_location_or_empty(self):
        """
        Shows the default location with a pin (if there is a location saved).
        Otherwise it shows the empty map.
        """
        tiles = self.TILES_DARK if self._dark else self.TILES_LIGHT
        if self._current_location:
            center = [self._current_location["lat"], self._current_location["lng"]]
            m = folium.Map(locals=center, zoom_start=MAP_ZOOM_START_LEVEL, tiles=tiles)

            folium.Marker(
                location=center,
                tooltip="My Location",
                popup=folium.Popup(
                    f"<b>{self._current_location['name']}</b>",
                    max_width=200
                ),
                icon=folium.Icon(color="blue", icon="home", prefix="fa")
            ).add_to(m)

        else:
            m = folium.Map(
                location=[MAP_CENTER[0], MAP_CENTER[1]], zoom_start=6, tiles=tiles
            )
        
        self.web_view.setHtml(m._repr_html_())


    def _show_empty_map(self):
        """
        Show an empty map centered on Germany.
        """
        tiles = self.TILES_DARK if self._dark else self.TILES_LIGHT
        m = folium.Map(location=[MAP_CENTER[0], MAP_CENTER[1]], zoom_start=6, tiles=tiles)
        self.web_view.setHtml(m._repr_html_())


    def _render_map(self, center: list = None, zoom: int = 13):
        """
        Rebuilds the folium-map and loads it into the WebView.
        """
        if not self._stations and not self._current_location:
            self._show_empty_map()
            return

        if not self._stations and self._current_location:
            self._show_location_or_empty()
            return


        # Map Center: Own Location or first station;
        if center is None:
            if self._current_location: center = [self._current_location["lat"], self._current_location["lng"]]
            else: center = [self._stations[0]["lat"], self._stations[0]["lng"]]

        tiles = self.TILES_DARK if self._dark else self.TILES_LIGHT
        m = folium.Map(location=center, zoom_start=zoom, tiles=tiles)

        # Own Location;
        if self._current_location:
            folium.Marker(
                location=center,
                tooltip="My Location",
                popup=folium.Popup(
                    f"<b>{self._current_location['name']}</b>", max_width=200
                ),
                icon=folium.Icon(color="blue", icon="home", prefix="fa")
            ).add_to(m)

        # Fuel type filter;
        selected = self.combo_fuel.currentText().lower()

        # Station marker;
        visible = 0
        for s in self._stations:
            # Price for the display in the tooltip;
            if selected == "all":
                available = {
                    k: v for k, v in s["prices"].items() if v is not None
                }
                display_price = min(available.values()) if available else None
                tooltip_fuel = "ab"

            else:
                display_price = s["prices"].get(selected)
                tooltip_fuel = FUEL_LABELS.get(selected, selected.upper())

            color = "green" if s["is_open"] else "gray"

            # Tooltip: Name + Price;
            if display_price is not None:
                tooltip = f"{s['name']} | {tooltip_fuel} {display_price:.3f} €"
            else:
                tooltip = f"{s['name']} | No Price"

            folium.Marker(
                location=[s["lat"], s["lng"]],
                tooltip=tooltip,
                popup=folium.Popup(
                    self._build_popup_html(s),
                    max_width=260
                ),
                icon=folium.Icon(color=color, icon="tint", prefix="fa")
            ).add_to(m)
            visible += 1

        # Update Statusbar;
        self.label_count.setText(f"{visible} Station(s) displayed")

        # Load HTML into WebView;
        self.web_view.setHtml(m._repr_html_())


    def _build_popup_html(self, s: dict) -> str:
        """
        Create the HTML for the marker popup.
        """
        brand = f" ({s['brand']})" if s.get("brand") else ""
        status = "open" if s["is_open"] else "closed"
        status_color = "#4caf50" if s["is_open"] else "#9e9e9e"
        dist = f"{s['dist']:.1f} km" if s.get("dist") else ""

        # Price row;
        price_rows = ""
        for fuel_key, label in FUEL_LABELS.items():
            price = s["prices"].get(fuel_key)
            if price is not None:
                color = FUEL_COLORS[fuel_key]
                price_rows += (
                    f'<tr>'
                    f'<td style="padding:2px 6px;font-weight:bold;color:{color}">'
                    f'{label}</td>'
                    f'<td style="padding:2px 6px;text-align:right">'
                    f'{price:.3f} €</td>'
                    f'</tr>'
                )

            else:
                price_rows += (
                    f'<tr>'
                    f'<td style="padding:2px 6px;color:#aaa">{label}</td>'
                    f'<td style="padding:2px 6px;color:#aaa;text-align:right">'
                    f'-</td>'
                    f'</tr>'
                )

        return f"""
            <div style="font-family:sans-serif;font-size:13px;min-width:220px">
            <b style="font-size:14px">{s['name']}{brand}</b><br>
            <span style="color:{status_color};font-size:11px">● {status}</span>
            {'&nbsp;&nbsp;' + dist if dist else ''}
            <hr style="margin:6px 0;border-color:#eee">
            <table style="width:100%;border-collapse:collapse">
                {price_rows}
            </table>
            </div>
        """
    


    # ---------------------------------------------------------------------------------------------------
    # Slots;
    # ---------------------------------------------------------------------------------------------------
    def _on_filter_changed(self, _):
        """
        Rerender the map when the fuel type filter is changed.
        """
        if self._stations: self._render_map()


    def _center_map(self):
        """
        Center the map onto own location.
        """
        if self._stations: self._render_map()


    def focus_station(self, station_id: str):
        """
        Center the map onto a specific station.
        """
        station = next((s for s in self._stations if s["id"] == station_id), None)
        if station is None: return

        # Rerender the map with the specific station in the center;
        self._render_map(center=[station["lat"], station["lng"]], zoom=8)


    def set_theme(self, dark: bool):
        self._dark = dark
        if self._stations or self._current_location: self._render_map()
        else: self._show_empty_map()