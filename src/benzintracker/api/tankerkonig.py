"""
tankerkonig.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: Client for the Tankerkönig API (https://creativecommons.tankerkoenig.de/)
=========================================================================================

Endpoints:
    - /list.php         Gas station + current prices in an area
    - /prices.php       Current prices for a list of known gas stations

The class throws its own excepction (TankerkonigError) when errors occur.
"""
import requests
from benzintracker import config
from benzintracker.__init__ import __version__


SESSION_TIMEOUT = 10


class TankerkonigError(Exception):
    """
    Thrown when invalid answers or API error occur.
    """
    pass


class TankerkonigClient:
    """
    Encapsule all requests to the Tankerkonig API.

    Example:
        client = TankerkonigClient(api_key="your-key")
        stations = client.fetch_stations(lat=52.52, lng=13.40, radius_km=5)
    """

    # All fuel types the API provides;
    FUEL_TYPES = ("e5", "e10", "diesel")

    def __init__(self, api_key: str = ""):
        # Fallback onto the key in the config file if no key specified;
        self.api_key = api_key or config.API_KEY
        self.base_url = config.API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({ "User-Agent": f"benzintracker/{__version__}" })



    # ---------------------------------------------------------------------------------------------------
    # Public Methods;
    # ---------------------------------------------------------------------------------------------------
    def fetch_stations(self, lat: float, lng: float, radius_km: float = None) -> list[dict]:
        """
        Return the stations with their current prices in an specific area.

        :param lat:                 Latitude of the location
        :param lng:                 Longitude of the location
        :param radius_km:           Search radius in km (Default is set in config)

        :return:                    List of dicts, each with the fields:
                                    id, name, brand, street, houseNumber, city, cityCode,
                                    lat, lng, dist, isOpen, e5, e10, diesel
        """
        radius = radius_km or config.DEFAULT_RADIUS_KM

        params = {
            "apikey": self.api_key,
            "lat": lat,
            "lng": lng,
            "rad": radius,
            "type": "all",      # Always all types;
            "sort": "dist"      # Sort by distance;
        }

        data = self._get("/list.php", params)
        stations = data.get("stations", [])

        return stations


    def fetch_prices(self, station_ids: list[str]) -> dict[str, dict]:
        """
        Gets the current prices of a list of stations by their station-IDs.
        Useful for period updates on already safed stations.

        :param station_ids:             List of Tankerkonig-UUIDs (max. 10 per request)

        :return:                        Dict { station_id: { "e5":1.799, "e10": 1.759, "diesel": 1.689 } }
        """
        if not station_ids: return {}

        params = {
            "apikey": self.api_key,
            "ids": ",".join(station_ids)
        }

        data = self._get("/prices.php", params)

        return data.get("prices", {})

    

    # ---------------------------------------------------------------------------------------------------
    # Helper Methods;
    # ---------------------------------------------------------------------------------------------------
    def _get(self, endpoint: str, params: dict) -> dict:
        """
        GET-Request to the API, returns the parsed JSON.
        Throws 'TankerkonigError' when network or API error occur.
        """
        if not self.api_key:
            raise TankerkonigError(
                "No API-KEY set! "
                "Please add a key in the settings or your environment variable (TANKERKONIG_API_KEY). "
                "If you don't have an API-KEY, you can request one here 'https://creativecommons.tankerkoenig.de/'"
            )

        url = self.base_url + endpoint
        try:
            response = self.session.get(url, params=params, timeout=SESSION_TIMEOUT)
            response.raise_for_status()
        
        except requests.exceptions.ConnectionError:
            raise TankerkonigError(
                "No connection to the Tankerkönig-API. "
                "Check your internet connection."
            )

        except requests.exceptions.Timeout:
            raise TankerkonigError(
                "The request to the Tankerkönig-API took too long."
            )

        except requests.exceptions.HTTPError as e:
            raise TankerkonigError(f"HTTP-Error: {e}")

        try: data = response.json()
        except ValueError: raise TankerkonigError("Received an invalid answer from the API (no JSON).")

        # The API signals errors in the body of the send JSON: "ok": false;
        if not data.get("ok", False):
            message = data.get("message", "Unknown API error.")
            raise TankerkonigError(f"API-Error: {message}")

        return data


    def validate_api_key(self) -> bool:
        """
        Test the api-key with a minimal request.
        Return True if the key is valid, else False.

        Meant for the input in the settings.
        """
        try:
            # Known coordinates (Middle of Germany), minimal radius;
            self.fetch_stations(lat=51.0, lng=10.0, radius_km=1)
            return True
        
        except TankerkonigError: return False