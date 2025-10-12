import asyncio
import os

import aiohttp
import dotenv

dotenv.load_dotenv()
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
GOOGL_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'


async def fetch_geocode(
    session: aiohttp.ClientSession,
    address: str,
):  # pragma: no cover
    params = {'address': address, 'key': API_KEY}
    async with session.get(GOOGL_API_URL, params=params) as resp:
        resp.raise_for_status()
        data = await resp.json()
    if not data.get('results'):
        return None, None
    loc = data['results'][0]['geometry']['location']
    return loc['lat'], loc['lng']


async def reverse_geocode(session, lat, lng):  # pragma: no cover
    params = {'latlng': f'{lat},{lng}', 'key': API_KEY, 'language': 'ru'}
    async with session.get(GOOGL_API_URL, params=params) as resp:
        resp.raise_for_status()
        data = await resp.json()
    for result in data.get('results', []):
        for comp in result.get('address_components', []):
            if 'country' in comp['types']:
                return comp['long_name']
    return None


async def main():  # pragma: no cover
    addresses = []
    async with aiohttp.ClientSession() as session:
        for address in addresses:
            lat, lng = await fetch_geocode(session, address)
            print(f'Координаты для «{address}» →', lat, lng)
            country = await reverse_geocode(session, lat, lng)
            print(f'Страна для {address} -> {country}')


if __name__ == '__main__':  # pragma: no cover
    asyncio.run(main())
