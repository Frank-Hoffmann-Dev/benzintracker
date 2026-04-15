"""
db.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 15.04.2026
License: MIT
Description: SQLite Database Inteface
=========================================================================================
"""
import sqlite3
import os
import math

from benzintracker import config


EARTH_RADIUS = 6371.0       # For Haversine Calculation;


def get_connection() -> sqlite3.Connection:
    """
    Return a SQLite connection.
    'row_factory' makes rows as usable as dicts: row["name"] instead of row[0]
    """
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)

    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")        # Activate foreign keys;
    #conn.execute("PRAGMA journal_mode = WAL")       # Write ahead logging;
    conn.execute("PRAGMA synchronous = NORMAL")     # Better than FULL, safer than OFF;

    # Register as custom function;
    conn.create_function("haversine", 4, _haversine)
    
    return conn


def init_db():
    """
    Create table if it not already exists.
    Executed with every start.
    """
    conn = get_connection()
    statements = [
        """
        CREATE TABLE IF NOT EXISTS stations (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            brand           TEXT,
            street          TEXT,
            house_number    TEXT,
            city            TEXT,
            post_code       TEXT,
            lat             REAL NOT NULL,
            lng             REAL NOT NULL,
            is_open         INTEGER DEFAULT 1       -- 1 = open, 0 = closed
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS prices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id      TEXT NOT NULL REFERENCES stations(id),
            fuel_type       TEXT NOT NULL,  -- e5, e10, diesel
            price           REAL NOT NULL,
            recorded_at     TEXT NOT NULL   -- ISO-8601: "2024-03-15 14:30:00"
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS locations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            lat             REAL NOT NULL,
            lng             REAL NOT NULL,
            radius_km       REAL DEFAULT 5.0,
            is_default      INTEGER DEFAULT 0   -- 1 = loaded at start
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_prices_station
            ON prices(station_id, recorded_at)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_prices_time
            ON prices(recorded_at);
        """
    ]
    with conn:
        for stmt in statements:
            conn.execute(stmt)

    conn.close()
    print(f"Initialized Database: {config.DB_PATH}")


def _haversine(lat_1: float, lng_1: float, lat_2: float, lng_2: float) -> float:
    """
    Calculate the distance in km between two coordinates (Haversine).
    """
    dlat = math.radians(lat_2 - lat_1)
    dlng = math.radians(lng_2 - lng_1)

    a = math.sin(dlat / 2)**2 \
        + math.cos(math.radians(lat_1)) \
        * math.cos(math.radians(lat_2)) \
        * math.sin(dlng / 2)**2

    return EARTH_RADIUS * 2 * math.asin(math.sqrt(a))


if __name__ == "__main__":
    init_db()