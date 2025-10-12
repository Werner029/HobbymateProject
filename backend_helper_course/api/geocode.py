import asyncio

import aiohttp
from django.contrib.gis.geos import Point

from helper.gro import fetch_geocode


async def _get_coords(address: str):  # pragma: no cover
    async with aiohttp.ClientSession() as session:
        lat, lng = await fetch_geocode(session, address)
        if lat is None or lng is None:
            raise ValueError(f'Не удалось найти координаты для «{address}»')
        return lat, lng


def geocode_to_point(address: str) -> Point:  # pragma: no cover
    try:
        lat, lng = asyncio.run(_get_coords(address))
    except Exception:
        raise
    return Point(lng, lat, srid=4326)
