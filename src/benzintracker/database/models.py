"""
models.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: Contains all models for the CRUD opersations on the tables.
=========================================================================================

CRUD for Tables:
    - stations              -> Core-data of the stations
    - prices                -> Price history
    - locations             -> Saved locations

Each function opens and closes the connection and can be used independent from each other.
GUI and Collector-Script.
"""
from datetime import datetime
from benzintracker.database.db import get_connection


# ---------------------------------------------------------------------------------------------------
# Basics;
# ---------------------------------------------------------------------------------------------------
def upsert_station(station: dict):
    """
    Add or update a station (if it doesn't exist yet).
    Expects a dict with fields from the station table.
    """
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO stations (id, name, brand, street, house_number, city, post_code, lat, lng, is_open)
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
            station["id"], station.get("name", ""), station.get("brand", ""),
            station.get("street", ""), station.get("house_number", ""),
            station.get("city", ""), station.get("post_code", ""),
            station["lat"], station["lng"], station.get("is_open", 1),
        ))
    conn.close()


def get_all_stations() -> list[dict]:
    """
    Return all saved stations.
    """
    conn = get_connection()
    rows = conn.execute("SELECT * FROM stations ORDER BY name").fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_station_by_id(station_id: str) -> dict | None:
    """
    Get information of a single station by its id.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM stations WHERE id = ?", (station_id,)).fetchone()
    conn.close()

    return dict(row) if row else None


def get_date_range(fuel_type: str) -> list[str]:
    conn = get_connection()
    row = conn.execute(
        "SELECT MIN(recorded_at), MAX(recorded_at) FROM prices WHERE fuel_type = ?",
        (fuel_type,)
    ).fetchone()
    conn.close()

    return row


# ---------------------------------------------------------------------------------------------------
# Prices;
# ---------------------------------------------------------------------------------------------------
def insert_price(station_id: str, fuel_type: str, price: float):
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn:
        conn.execute("""
            INSERT INTO prices (station_id, fuel_type, price, recorded_at)
            VALUES (?, ?, ?, ?)
        """, (station_id, fuel_type, price, now,))

    conn.close()


def get_latest_prices(fuel_type: str = "e5") -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.id, s.name, s.brand, s.city, s.lat, s.lng, p.price, p.fuel_type, p.recorded_at
        FROM prices p
        JOIN stations s ON s.id = p.station_id
        WHERE p.fuel_type = ?
        AND p.recorded_at = (
            SELECT MAX(p2.recorded_at)
            FROM prices p2
            WHERE p2.station_id = p.station_id
            AND p2.fuel_type = p.fuel_type
        )
        ORDER BY p.price ASC
    """, (fuel_type,)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_price_history(station_id: str, fuel_type: str, days: int = 30) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT price, recorded_at
        FROM prices
        WHERE station_id = ?
        AND fuel_type = ?
        AND recorded_at >= datetime('now', ?)
        ORDER BY recorded_at ASC
    """, (station_id, fuel_type, f"-{days} days",)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_average_prices_per_day(fuel_type: str = "e5", days: int = 30) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT DATE(recorded_at) AS day, AVG(price) AS avg_price
        FROM prices
        WHERE fuel_type = ?
        AND recorded_at >= datetime('now', ?)
        GROUP BY day
        ORDER BY day ASC
    """, (fuel_type, f"-{days} days",)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_hourly_averages(fuel_type: str) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT CAST(strftime('%H', recorded_at) AS INTEGER) AS hour,
            AVG(price) AS avg_price,
            COUNT(*) AS cnt
        FROM prices
        WHERE fuel_type = ?
        GROUP BY hour
        ORDER BY hour
    """, (fuel_type,)).fetchall()
    conn.close()

    return rows



# ---------------------------------------------------------------------------------------------------
# Locations;
# ---------------------------------------------------------------------------------------------------
def save_location(name: str, lat: float, lng: float, radius_km: float = 5.0, is_default: bool = False):
    conn = get_connection()
    with conn:
        if is_default:
            # Reset previous location;
            conn.execute("UPDATE locations SET is_default = 0")

        conn.execute("""
            INSERT INTO locations (name, lat, lng, radius_km, is_default)
            VALUES (?, ?, ?, ?, ?)
        """, (name, lat, lng, radius_km, int(is_default),))
    conn.close()


def get_all_locations() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM locations ORDER BY is_default DESC, name ASC
    """).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_default_location() -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM locations WHERE is_default = 1 LIMIT 1").fetchone()
    conn.close()

    return dict(row) if row else None


def set_default_location(location_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("UPDATE locations SET is_default = 0")
        conn.execute("UPDATE locations SET is_default = 1 WHERE id = ?", (location_id,))
    conn.close()


def delete_location(location_id: int):
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))
    conn.close()



# ---------------------------------------------------------------------------------------------------
# Database;
# ---------------------------------------------------------------------------------------------------
def reset_database() -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM prices")
        conn.execute("DELETE FROM stations")
        conn.execute("DELETE FROM locations")
    conn.close()