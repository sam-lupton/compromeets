# Compromeets — Claude Context

A Python app for finding the optimal meeting point between multiple people, using public transit isochrones and Google Places.

## Architecture

Modular monolith — intentionally. All modules are Python packages under `compromeets/`. The FastAPI app in `compromeets/app/` is the only entry point. Do not propose extracting a module into a separate service unless there is a concrete operational reason (see global CLAUDE.md).

```
clients/          External API wrappers (GooglePlacesClient, AnthropicClient)
services/         Business logic (IsochroneService, PlaceSearchService, SuggestService, …)
models/domain.py  Shared Pydantic schemas — the single source of truth for all data contracts
models/inputs.py  FastAPI request/response models
prompts/          LLM prompt templates
```

The main pipeline: `SuggestService` → `IsochroneService` → `MeetingAreaService` → `PlaceSearchService` → `GooglePlacesClient`

## Formal Contract Boundaries

The boundary below has a full CDCT contract in `tests/contracts/`:

| Consumer | Provider | Contract schema |
|---|---|---|
| `PlaceSearchService` | `GooglePlacesClient` | `GooglePlacesResponse` in `models/domain.py` |

When adding a new client or cross-module dependency, add a row here and create the corresponding contract test file.

## Development Pipeline

Follow the global pipeline from `~/.claude/CLAUDE.md`. Repo-specific notes:

- **Readme-Driven**: Update this file's module table above when adding a new service.
- **Type-Driven**: All service return types must be Pydantic models defined in `models/domain.py`. Never return bare `dict` or `tuple[str, float]` across a service boundary.
- **CDCT**: New clients go in `clients/`. Every client needs a contract test in `tests/contracts/`. The fixture response in the contract test should be a real sample from the API docs or a captured response.
- **BDD**: Follow the `test_given_<context>_when_<action>_then_<outcome>` naming convention. See `tests/unit/test_place_search_service.py` for a worked example.

## Toolchain

| Tool | Purpose | Command |
|---|---|---|
| `uv` | Package manager + runner | `uv run <cmd>` |
| `pytest` | Tests | `uv run pytest tests/unit/` |
| `ruff` | Lint + format | `uv run ruff check . && uv run ruff format .` |
| `mypy` | Type checking | `uv run mypy compromeets/` |
| FastAPI | Web framework | `uv run fastapi dev compromeets/app/main.py` |

Line length: 120. Lint config: `pyproject.toml [tool.ruff]`.

## Testing Conventions

```
tests/
  unit/        Fast, dependency-free. Mock direct dependencies only.
  contracts/   CDCT tests. Use fixture responses, not real API calls.
  integration/ Real external calls. Marked @pytest.mark.integration, skipped by default.
```

Run only the fast suite: `uv run pytest tests/unit/ tests/contracts/`

## Key Domain Facts

- Postcodes are UK format (e.g. `N7 8LT`).
- Coordinates are WGS84 / EPSG:4326 throughout.
- Travel-time isochrones are computed via `r5py` against a local transport network (OSM + GTFS). The network takes ~30 s to load — it is built once at startup in the FastAPI lifespan.
- Google Places API is the only paid external dependency. Unit and contract tests must never call it.
