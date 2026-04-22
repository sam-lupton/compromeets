# Orchestrates end to end location finding process

from compromeets.clients.google_places_client import GooglePlacesClient
from compromeets.models.domain import PlaceResult
from compromeets.services.isochrone_service import IsochroneService
from compromeets.services.meeting_area_service import MeetingAreaService
from compromeets.services.place_search_service import PlaceSearchService


class SuggestService:
    def __init__(
        self,
        isochrone_service: IsochroneService,
        meeting_area_service: MeetingAreaService,
        place_search_service: PlaceSearchService,
        google_places_client: GooglePlacesClient,
    ):
        self.isochrone_service = isochrone_service
        self.meeting_area_service = meeting_area_service
        self.place_search_service = place_search_service

    def suggest_places(self, postcodes: list[str], types: list[str]) -> list[PlaceResult]:
        """Suggest meeting places for a list of postcodes"""
        isochrones, _ = self.isochrone_service.postcodes_to_isochrones(postcodes)
        meeting_area_polygon, _ = self.meeting_area_service.find_meeting_area(isochrones=isochrones)
        places = self.place_search_service.search_nearby(search_area=meeting_area_polygon, types=types)
        return places
