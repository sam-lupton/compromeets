import logging
import os
from types import TracebackType

import httpx

logger = logging.getLogger(__name__)


class GooglePlacesClient:
    """Class for interacting with the Google Places API"""

    def __init__(
        self, api_key: str | None = None, base_url: str = "https://places.googleapis.com/v1/places:searchNearby"
    ):
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in GOOGLE_PLACES_API_KEY environment variable")
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)

    def search_nearby(
        self,
        location: dict[str, float],
        radius: float,
        types: list[str],
        max_result_count: int = 10,
    ) -> dict:
        response = self.client.post(
            self.base_url,
            headers={
                "X-Goog-Api-Key": self.api_key or "",
                "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.location",
                "Content-Type": "application/json",
            },
            json={
                "includedTypes": types,
                "maxResultCount": max_result_count,
                "locationRestriction": {"circle": {"center": location, "radius": int(radius)}},
            },
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "GooglePlacesClient":
        return self

    def __exit__(
        self, exc_type: BaseException | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.close()
