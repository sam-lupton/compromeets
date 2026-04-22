import logging
import os
from types import TracebackType

import httpx

from compromeets.models.domain import GooglePlacesResponse, PlaceSearchLocationData

logger = logging.getLogger(__name__)


class GooglePlacesClient:
    """Class for interacting with the Google Places API"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in GOOGLE_PLACES_API_KEY environment variable")
        self.nearby_url = "https://places.googleapis.com/v1/places:searchNearby"
        self.text_url = "https://places.googleapis.com/v1/places:searchText"
        self.client = httpx.Client(timeout=10.0)

    def search_nearby(
        self,
        location_data: PlaceSearchLocationData,
        types: list[str],
        max_result_count: int = 10,
    ) -> GooglePlacesResponse:
        logger.debug(f"Searching nearby with types: {types}")
        try:
            response = self.client.post(
                self.nearby_url,
                headers={
                    "X-Goog-Api-Key": self.api_key or "",
                    "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.location",
                    "Content-Type": "application/json",
                },
                json={
                    "includedTypes": types,
                    "maxResultCount": max_result_count,
                    "locationRestriction": {
                        "circle": {"center": location_data.location_dict(), "radius": location_data.radius}
                    },
                },
            )
            response.raise_for_status()
            return GooglePlacesResponse.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            logger.error(f"Google Places API error: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Google Places API error: {e.response.text}") from e

    def search_text(
        self,
        text: str,
        location_data: PlaceSearchLocationData,
        types: list[str] | None = None,
        max_result_count: int = 10,
    ) -> GooglePlacesResponse:
        """Search for places using text query. Types parameter is optional for custom venue descriptions."""
        payload = {
            "textQuery": text,
            "maxResultCount": max_result_count,
            "locationBias": {"circle": {"center": location_data.location_dict(), "radius": location_data.radius}},
        }

        if types:
            payload["includedTypes"] = types

        logger.debug(f"Searching with text query: '{text}', types: {types}")
        try:
            response = self.client.post(
                self.text_url,
                headers={
                    "X-Goog-Api-Key": self.api_key or "",
                    "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.location",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return GooglePlacesResponse.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            logger.error(f"Google Places API error: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Google Places API error: {e.response.text}") from e

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "GooglePlacesClient":
        return self

    def __exit__(
        self, exc_type: BaseException | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.close()
