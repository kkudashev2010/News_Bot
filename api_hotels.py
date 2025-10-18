import requests
from loader import RAPIDAPI_KEY
import datetime


def search_hotels(city, checkin, checkout, price_min, price_max, limit=5):
    if not RAPIDAPI_KEY:
        res = []
        for i in range(1, limit+1):
            res.append({
                'id': f'mock_{i}',
                'name': f'Sample Hotel {i} in {city}',
                'link': f'https://example.com/hotel/{i}',
                'description': f'Demo hotel {i} description.',
                'price': 20.0 * i,
                'checkin': checkin,
                'checkout': checkout,
                'photos': [f'https://placehold.co/600x400?text=Hotel+{i}'],
                'latitude': str(55.0 + i*0.01),
                'longitude': str(37.0 + i*0.01),
            })
        return res

    try:
        url = 'https://hotels4.p.rapidapi.com/locations/v3/search'
        headers = {'X-RapidAPI-Key': RAPIDAPI_KEY, 'X-RapidAPI-Host': 'hotels4.p.rapidapi.com'}
        params = {'q': city}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Parsing depends on API; here we return empty to force developer to implement mapping.
        return []
    except Exception as e:
        print('API error in search_hotels:', e)
        return []
