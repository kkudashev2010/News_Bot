import http.client
import json
import os
from urllib.parse import quote
from loguru import logger

from dotenv import load_dotenv

conn = http.client.HTTPSConnection("booking-com15.p.rapidapi.com")

headers = {
    "x-rapidapi-key": "6e546ecd12msh242fc058d6df145p1ec861jsn246f46226a01",
    "x-rapidapi-host": "booking-com15.p.rapidapi.com",
}

load_dotenv()
API_KEY = os.getenv("API_KEY")


def search_hotels(params: dict):
    """
    Поиск отелей по параметрам (Booking API)
    Обязательные поля: dest_id, search_type, arrival_date, departure_date
    """
    import urllib.parse
    import json
    import http.client
    import logging

    logger = logging.getLogger(__name__)
    conn = http.client.HTTPSConnection("booking-com15.p.rapidapi.com")
    logger.error(f"conn {conn}")
    query = urllib.parse.urlencode(
        {
            "dest_id": params.get("dest_id"),
            "search_type": params.get("search_type", "CITY"),
            "arrival_date": params.get("arrival_date"),
            "departure_date": params.get("departure_date"),
            "adults": params.get("adults", 1),
            "children_age": params.get("children_age", "0"),
            "room_qty": params.get("room_qty", 1),
            "price_min": params.get("price_min", 0),
            "price_max": params.get("price_max", 0),
            "page_number": 1,
            "languagecode": "ru",
            "units": "metric",
        }
    )
    logger.error(f"query {query}")

    headers = {
        "x-rapidapi-key": os.getenv("API_KEY"),
        "x-rapidapi-host": "booking-com15.p.rapidapi.com",
    }

    conn.request("GET", f"/api/v1/hotels/searchHotels?{query}", headers=headers)
    res = conn.getresponse()
    logger.error(f"res {res}")
    data = res.read().decode("utf-8")
    logger.error(f"data {data}")
    logger.info("Result", res)
    logger.info("Дата", data)

    try:
        json_data = json.loads(data)
        logger.error(f"json_data {json_data}")
        # logger.info('Json data', json_data)
    except Exception as e:
        logger.info(f"Ошибка при парсинге JSON: {e}")
        return {}

    return json_data


def filter_destinations(data, dest_type=None, search_type=None):
    """
    Фильтрует список словарей по dest_type и search_type.
    Возвращает только те элементы, которые соответствуют условиям.
    """

    filtered = []
    for item in data["data"]:
        if item["search_type"] == "city":
            logger.info(item["dest_id"], item["name"])

    return filtered


def get_dest_id(city: str):
    """Получение dest_id по названию города (гибкий парсер)"""
    conn = http.client.HTTPSConnection("booking-com15.p.rapidapi.com")

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "booking-com15.p.rapidapi.com",
    }

    encoded_city = quote(city)
    conn.request(
        "GET", f"/api/v1/hotels/searchDestination?query={encoded_city}", headers=headers
    )

    res = conn.getresponse()
    data = res.read()

    try:
        decoded_data = data.decode("utf-8")
        json_data = json.loads(decoded_data)
    except Exception as e:
        logger.info(f"Ошибка при разборе ответа API: {e}")
        return None

    destinations = []

    if isinstance(json_data.get("data"), list):
        destinations = json_data["data"]
    elif isinstance(json_data.get("data"), dict):
        inner = json_data["data"]
        if "destinations" in inner:
            destinations = inner["destinations"]
        elif "results" in inner:
            destinations = inner["results"]

    if not destinations:
        logger.info(
            "⚠ API не вернул список направлений. Структура:", list(json_data.items())
        )
        return None

    city_results = [
        {
            "name": d.get("name"),
            "dest_id": d.get("dest_id"),
            "dest_type": d.get("dest_type"),
        }
        for d in destinations
        if d.get("dest_type") == "CITY"
    ]

    if not city_results:
        city_results = destinations

    return {"data": city_results}
