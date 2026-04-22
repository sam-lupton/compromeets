import logging
from contextlib import asynccontextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

import geopandas as gpd
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from compromeets.clients.anthropic_client import AnthropicClient
from compromeets.clients.google_places_client import GooglePlacesClient
from compromeets.services.isochrone_service import IsochroneService
from compromeets.services.llm_agent_service import LLMAgentService
from compromeets.services.meeting_area_service import MeetingAreaService
from compromeets.services.place_search_service import PlaceSearchService
from compromeets.services.postcode_resolver import PostcodeResolver
from compromeets.services.suggest_service import SuggestService
from compromeets.services.transport_network_provider import TransportNetworkProvider

# Setup templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: build expensive dependencies once
    print("Loading transport network and services...")

    # Load postcodes
    postcodes_gdf = pd.read_csv(  # pyright: ignore[reportCallIssue]
        "~/Downloads/ONSPD_NOV_2025/Data/ONSPD_NOV_2025_UK.csv",
        usecols=["pcds", "lat", "long"],  # pyright: ignore[reportArgumentType]
    )
    postcodes_gdf = gpd.GeoDataFrame(postcodes_gdf, geometry=gpd.points_from_xy(postcodes_gdf.long, postcodes_gdf.lat))
    postcode_resolver = PostcodeResolver(postcodes_gdf=postcodes_gdf)

    # Build transport network
    transport_network_provider = TransportNetworkProvider(
        osm_path=Path("compromeets/artifacts/greater-london-260121.osm.pbf"),
        gtfs_path=Path("compromeets/artifacts/london_transport_gtfs.zip"),
    )
    transport_network = transport_network_provider.get_transport_network()

    # Build service graph
    isochrone_service = IsochroneService(
        postcode_resolver=postcode_resolver,
        transport_network=transport_network,
    )
    meeting_area_service = MeetingAreaService()
    google_places_client = GooglePlacesClient()
    place_search_service = PlaceSearchService(google_places_client=google_places_client)

    suggest_service = SuggestService(
        isochrone_service=isochrone_service,
        meeting_area_service=meeting_area_service,
        place_search_service=place_search_service,
        google_places_client=google_places_client,
    )

    # Build LLM service
    anthropic_client = AnthropicClient()
    llm_agent_service = LLMAgentService(anthropic_client=anthropic_client)

    app.state.suggest_service = suggest_service
    app.state.llm_agent_service = llm_agent_service

    print("Services loaded!")

    yield

    google_places_client.close()
    anthropic_client.close()
    print("Cleanup complete")


app = FastAPI(lifespan=lifespan)


class SuggestRequest(BaseModel):
    postcodes: list[str]
    types: list[str]
    use_llm: bool = False
    preference: str = "equidistance"


def get_suggest_service(request: Request) -> SuggestService:
    return request.app.state.suggest_service


def get_llm_agent_service(request: Request) -> LLMAgentService:
    return request.app.state.llm_agent_service


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/suggest")
def suggest(
    request_body: SuggestRequest,
    service: SuggestService = Depends(get_suggest_service),
    llm_service: LLMAgentService = Depends(get_llm_agent_service),
):
    """API endpoint for suggesting meeting places"""
    try:
        if request_body.use_llm:
            # LLM-based suggestion
            venues = llm_service.suggest_venues(
                locations=request_body.postcodes,
                preference=request_body.preference,
                venue_type=", ".join(request_body.types),
            )
            return {"places": venues, "method": "llm"}
        else:
            # Algorithm-based suggestion (existing isochrone method)
            places = service.suggest_places(postcodes=request_body.postcodes, types=request_body.types)
            return {"places": places, "method": "algorithm"}
    except ValueError as e:
        logger.warning("Validation error in /suggest: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in /suggest")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}") from e
