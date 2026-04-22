"""
Example script demonstrating the LLM-based venue suggestion feature.

Make sure ANTHROPIC_API_KEY is set in your environment:
    export ANTHROPIC_API_KEY=sk-ant-...

Or add it to your .env file.
"""

from compromeets.clients.anthropic_client import AnthropicClient
from compromeets.services.llm_agent_service import LLMAgentService


def main():
    # Initialize the client and service
    client = AnthropicClient()
    service = LLMAgentService(anthropic_client=client)

    # Example 1: Equidistance preference (fairness)
    print("=" * 60)
    print("Example 1: Equidistance (fair travel times)")
    print("=" * 60)
    venues = service.suggest_venues(
        locations=["N7 8LT", "SW1A 1AA", "E1 6AN"], preference="equidistance", venue_type="sports pub"
    )

    for i, venue in enumerate(venues, 1):
        print(f"\n{i}. {venue['venue_name']}")
        print(f"   Location: {venue['location']}")
        print(f"   Why: {venue['why']}")
        print(f"   Maps: {venue['maps']}")

    # Example 2: Best rating preference (quality first)
    print("\n" + "=" * 60)
    print("Example 2: Best Rating (quality venues)")
    print("=" * 60)
    venues = service.suggest_venues(
        locations=["Shoreditch", "Camden", "Greenwich"], preference="best_rating", venue_type="restaurant"
    )

    for i, venue in enumerate(venues, 1):
        print(f"\n{i}. {venue['venue_name']}")
        print(f"   Location: {venue['location']}")
        print(f"   Why: {venue['why']}")
        print(f"   Maps: {venue['maps']}")

    # Example 3: Minimum overall travel time
    print("\n" + "=" * 60)
    print("Example 3: Minimum Travel Time (efficiency)")
    print("=" * 60)
    venues = service.suggest_venues(
        locations=["King's Cross", "Angel", "Old Street"], preference="minimum_overall_travel_time", venue_type="cafe"
    )

    for i, venue in enumerate(venues, 1):
        print(f"\n{i}. {venue['venue_name']}")
        print(f"   Location: {venue['location']}")
        print(f"   Why: {venue['why']}")
        print(f"   Maps: {venue['maps']}")

    # Cleanup
    client.close()
    print("\n" + "=" * 60)
    print("Done! Note: Check your Anthropic console for cache hit stats.")
    print("The system prompt should be cached after the first call,")
    print("saving ~90% of input token costs on subsequent calls.")
    print("=" * 60)


if __name__ == "__main__":
    main()
