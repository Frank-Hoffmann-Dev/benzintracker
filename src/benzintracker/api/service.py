"""
service.py - Connects the API-Client with the database layer.

The GUI calls only those functions and doesn't need to know how the API or database works.

Procedure of a Refresh:
    1. API query (fetch_stations or fetch_prices)
    2. Upsert answer into the core-data
    3. Write prices into the prices-table
    4. Get the processed data for the map and tables
"""
from datetime import datetime

from benzintracker.api.tankerkonig import TankerkonigClient, TankerkonigError
from benzintracker.database.db import get_connection
from benzintracker import config


def refresh_for_location(
        lat: float, lng: float,
        radius_km: float = None,
        api_key: str = ""
) -> list[dict]:
    """
    Main function for the periodic refresh (called by 'QTimer').

    Query for all stations in a specific area, save data in the database and
    return the event-list to the GUI.

    :return:            List of dicts containing information about stations + prices,
                        sorted by distance. Each dict has the fields:
                        id, name, brand, city, lat, lng, dist, isOpen, price, fuel_type

    Throws 'TankerkonigError' when error occur (GUI show the error).
    """
    client = TankerkonigClient(api_key=api_key)

    raw_stations = client.fetch_stations(lat=lat, lng=lng, radius_km=radius_km)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    results = []
    conn = get_connection()
    try:
        with conn:
            for s in raw_stations:
                # Stammdaten upserten
                conn.execute("""
                    INSERT INTO stations
                        (id, name, brand, street, house_number,
                         city, post_code, lat, lng, is_open)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name         = excluded.name,
                        brand        = excluded.brand,
                        street       = excluded.street,
                        house_number = excluded.house_number,
                        city         = excluded.city,
                        post_code    = excluded.post_code,
                        lat          = excluded.lat,
                        lng          = excluded.lng,
                        is_open      = excluded.is_open
                """, (
                    s["id"],
                    s.get("name", ""),
                    s.get("brand", ""),
                    s.get("street", ""),
                    s.get("houseNumber", ""),
                    s.get("place", ""),
                    s.get("postCode", ""),
                    s["lat"],
                    s["lng"],
                    int(s.get("isOpen", False)),
                ))
 
                # Alle drei Kraftstoffpreise speichern
                prices = {}
                for fuel in TankerkonigClient.FUEL_TYPES:
                    price = s.get(fuel)
                    if price is not None:
                        conn.execute(
                            "INSERT INTO prices "
                            "(station_id, fuel_type, price, recorded_at) "
                            "VALUES (?, ?, ?, ?)",
                            (s["id"], fuel, float(price), now)
                        )
                    prices[fuel] = float(price) if price is not None else None
 
                results.append({
                    "id":      s["id"],
                    "name":    s.get("name", ""),
                    "brand":   s.get("brand", ""),
                    "city":    s.get("place", ""),
                    "lat":     s["lat"],
                    "lng":     s["lng"],
                    "dist":    s.get("dist", 0.0),
                    "is_open": s.get("isOpen", False),
                    "prices":  prices,
                })
    finally:
        conn.close()
 
    return results


def refresh_prices_only(
        station_ids: list[str],
        api_key: str = ""
) -> dict[str, dict]:
    """
    Updates only the prices for already known stations.
    Faster then 'refresh_for_location' as there is no need for the geo-search.
    Can be used for shorter refresh intervals.

    :return:                dict { station_id: price }
    """
    client = TankerkonigClient(api_key=api_key)
    raw_prices = client.fetch_prices(station_ids)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    results = {}
    conn = get_connection()
    try:
        with conn:
            for station_id, price_data in raw_prices.items():
                prices = {}
                for fuel in TankerkonigClient.FUEL_TYPES:
                    price = price_data.get(fuel)
                    if price is not None:
                        conn.execute(
                            "INSERT INTO prices "
                            "(station_id, fuel_type, price, recorded_at) "
                            "VALUES (?, ?, ?, ?)",
                            (station_id, fuel, float(price), now)
                        )
                    prices[fuel] = float(price) if price is not None else None
                results[station_id] = prices
    finally:
        conn.close()
 
    return results