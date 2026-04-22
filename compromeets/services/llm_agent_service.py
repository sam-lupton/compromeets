import json
import logging
from typing import Any

from compromeets.clients.anthropic_client import AnthropicClient
from compromeets.prompts.system_prompts import MEETING_LOCATION_RANKER_SYSTEM_PROMPT
from compromeets.prompts.user_templates import USER_TEMPLATE

logger = logging.getLogger(__name__)


class LLMAgentService:
    """Service for using LLM to suggest meeting venues"""

    def __init__(self, anthropic_client: AnthropicClient):
        self.client = anthropic_client

    def suggest_venues(self, locations: list[str], preference: str, venue_type: str) -> list[dict[str, Any]]:
        """
        Use LLM to suggest meeting venues based on participant locations and preferences.

        Args:
            locations: List of participant locations (postcodes, neighborhoods, etc.)
            preference: Selection algorithm (equidistance, minimum_overall_travel_time,
                       best_rating, affordability)
            venue_type: Type of venue to suggest (e.g., "sports pub", "cafe", "park")

        Returns:
            List of venue dictionaries with keys: venue_name, location, why, maps

        Raises:
            ValueError: If the LLM returns invalid JSON or fails to complete the request

        """
        # Format locations as bullet list
        locations_str = "\n".join(f"- {loc}" for loc in locations)

        # Build user prompt
        user_prompt = USER_TEMPLATE.format(locations=locations_str, preference=preference, venue_type=venue_type)

        logger.info(
            f"Requesting venue suggestions for {len(locations)} locations, "
            f"preference={preference}, venue_type={venue_type}"
        )

        # Call Claude with prompt caching
        response = self.client.complete(
            system=MEETING_LOCATION_RANKER_SYSTEM_PROMPT,
            user=user_prompt,
            use_caching=True,  # Cache the system prompt for cost savings
        )

        # Parse JSON response
        try:
            venues = json.loads(response)

            # Validate response structure
            if not isinstance(venues, list):
                raise ValueError("Expected a JSON array of venues")

            if len(venues) == 0:
                raise ValueError("LLM returned empty venue list")

            # Validate each venue has required keys
            required_keys = {"venue_name", "location", "why", "maps"}
            for i, venue in enumerate(venues):
                missing_keys = required_keys - set(venue.keys())
                if missing_keys:
                    raise ValueError(f"Venue {i} missing required keys: {missing_keys}")

            logger.info(f"Successfully generated {len(venues)} venue suggestions")
            return venues

        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            logger.error(f"Response was: {response}")
            raise ValueError(f"LLM returned invalid JSON: {e}\nResponse: {response[:500]}...") from e
