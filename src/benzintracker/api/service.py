"""
service.py - Connects the API-Client with the database layer.

The GUI calls only those functions and doesn't need to know how the API or database works.

Procedure of a Refresh:
    1. API query (fetch_stations or fetch_prices)
    2. Upsert answer into the core-data
    3. Write prices into the prices-table
    4. Get the processed data for the map and tables
"""
from benzintracker.api.tankerkonig import TankerkonigClient, TankerkonigError
from benzintracker.database import models
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



    # ---------------------------------------------------------------------------------------------------
    # 1. API Query;
    # ---------------------------------------------------------------------------------------------------
    raw_stations = client.fetch_stations(lat=lat, lng=lng, radius_km=radius_km)
    


    # ---------------------------------------------------------------------------------------------------
    # 2. Save station data and write new prices;
    # ---------------------------------------------------------------------------------------------------
    results = []
    for s in raw_stations:
        # Normalize the station data and upsert;
        models.upsert_station({
            "id":                   s["id"],
            "name":                 s.get("name", ""),
            "brand":                s.get("brand", ""),
            "street":               s.get("street", ""),
            "house_number":         s.get("houseNumber", ""),
            "city":                 s.get("place", ""),
            "city_code":            s.get("postCode", ""),
            "lat":                  s["lat"],
            "lng":                  s["lng"],
            "is_open":              int(s.get("isOpen", False))
        })

        prices = {}
        for fuel in TankerkonigClient.FUEL_TYPES:
            price = s.get(fuel)
            if price is not None:
                models.insert_price(s["id"], fuel, float(price))

            prices[fuel] = float(price) if price is not None else None

        results.append({
            "id":                   s["id"],
            "name":                 s.get("name", ""),
            "brand":                s.get("brand", ""),
            "street":               s.get("street", ""),
            "house_number":         s.get("houseNumber", ""),
            "city":                 s.get("place", ""),
            "city_code":            s.get("postCode", ""),
            "lat":                  s["lat"],
            "lng":                  s["lng"],
            "dist":                 s.get("dist", 0.0),
            "is_open":              int(s.get("isOpen", False)),
            "prices":               prices
        })

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

    results = {}
    for station_id, price_data in raw_prices.items():
        prices = {}

        for fuel in TankerkonigClient.FUEL_TYPES:
            price = price_data.get(fuel)
            if price is not None:
                models.insert_price(station_id, fuel, float(price))

            prices[fuel] = float(price) if price is not None else None

        results[station_id] = prices

    return results