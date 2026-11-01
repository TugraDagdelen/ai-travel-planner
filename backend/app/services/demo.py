"""Explicitly synthetic demo fixtures. These never make network requests."""

from app.schemas.discovery import Destination

DEMO_DESTINATIONS = [
    Destination(
        id="demo:istanbul",
        name="İstanbul",
        country="Türkiye",
        country_code="TR",
        region="İstanbul",
        latitude=41.0082,
        longitude=28.9784,
        timezone="Europe/Istanbul",
    ),
    Destination(
        id="demo:barcelona",
        name="Barcelona",
        country="Spain",
        country_code="ES",
        region="Catalonia",
        latitude=41.3874,
        longitude=2.1686,
        timezone="Europe/Madrid",
    ),
    Destination(
        id="demo:paris",
        name="Paris",
        country="France",
        country_code="FR",
        region="Île-de-France",
        latitude=48.8566,
        longitude=2.3522,
        timezone="Europe/Paris",
    ),
    Destination(
        id="demo:paris-tx",
        name="Paris",
        country="United States",
        country_code="US",
        region="Texas",
        latitude=33.66,
        longitude=-95.55,
        timezone="America/Chicago",
    ),
]
