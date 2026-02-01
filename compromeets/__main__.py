from pathlib import Path

import geopandas as gpd
import pandas as pd

from compromeets.clients.google_places_client import GooglePlacesClient
from compromeets.services.isochrone_service import IsochroneService
from compromeets.services.meeting_area_service import MeetingAreaService
from compromeets.services.place_search_service import PlaceSearchService
from compromeets.services.postcode_resolver import PostcodeResolver
from compromeets.services.suggest_service import SuggestService
from compromeets.services.transport_network_provider import TransportNetworkProvider


def main():
    postcodes = ["E14 2DF", "N7 0AA", "SW2 1AB"]

    # Load transport network
    gtfs_path = Path("compromeets/artifacts/london_transport_gtfs.zip")
    osm_path = Path("compromeets/artifacts/greater-london-260121.osm.pbf")

    transport_network_provider = TransportNetworkProvider(osm_path=osm_path, gtfs_path=gtfs_path)
    transport_network = transport_network_provider.get_transport_network()

    postcodes_gdf = pd.read_csv("~/Downloads/ONSPD_NOV_2025/Data/ONSPD_NOV_2025_UK.csv")[["pcds", "lat", "long"]]
    postcodes_gdf = gpd.GeoDataFrame(postcodes_gdf, geometry=gpd.points_from_xy(postcodes_gdf.long, postcodes_gdf.lat))
    postcode_resolver = PostcodeResolver(postcodes_gdf=postcodes_gdf)

    isochrone_service = IsochroneService(postcode_resolver=postcode_resolver, transport_network=transport_network)
    meeting_area_service = MeetingAreaService()
    google_places_client = GooglePlacesClient()
    place_search_service = PlaceSearchService(google_places_client=google_places_client)
    suggest_service = SuggestService(
        isochrone_service=isochrone_service,
        meeting_area_service=meeting_area_service,
        place_search_service=place_search_service,
        google_places_client=google_places_client,
    )
    places = suggest_service.suggest_places(postcodes=postcodes, types=["pub"])  # noqa

    breakpoint()


if __name__ == "__main__":
    main()
