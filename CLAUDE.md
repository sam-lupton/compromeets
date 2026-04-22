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

## After making changes

After any code change, run:

```bash
make fmt       # auto-fix formatting and lint issues
make test      # run the fast test suite (unit + contracts)
make typecheck # basedpyright — must exit with 0 errors, 0 warnings
```

All three must pass before committing. If `make fmt` changes any files, stage them before committing. Do not filter `make typecheck` output — check the raw exit code. The pre-push hook runs `make typecheck` and `make test` automatically before every push.

## Toolchain

| Command | Purpose |
|---|---|
| `make fmt` | Auto-fix formatting and lint (ruff format + ruff check --fix) |
| `make lint` | Lint check only, no fixes |
| `make test` | Unit + contract tests |
| `make test-cov` | Unit tests with coverage report |
| `make test-integration` | Integration tests (real API calls — skipped by default) |
| `make security` | Bandit SAST scan (medium severity+) |
| `make hooks` | Install pre-commit hooks (run once after cloning) |
| `uv run mypy compromeets/` | Type checking |
| `uv run fastapi dev compromeets/app/main.py` | Start dev server |

Line length: 120. Lint config: `pyproject.toml [tool.ruff]`.

## Testing Conventions

```
tests/
  unit/        Fast, dependency-free. Mock direct dependencies only.
  contracts/   CDCT tests. Use fixture responses, not real API calls.
  integration/ Real external calls. Marked @pytest.mark.integration, skipped by default.
```

`make test` runs `tests/unit/` and `tests/contracts/`. Never run integration tests unless explicitly testing external API behaviour — they hit real services and incur cost.

## Key Domain Facts

- Postcodes are UK format (e.g. `N7 8LT`).
- Coordinates are WGS84 / EPSG:4326 throughout.
- Travel-time isochrones are computed via `r5py` against a local transport network (OSM + GTFS). The network takes ~30 s to load — it is built once at startup in the FastAPI lifespan.
- Google Places API is the only paid external dependency. Unit and contract tests must never call it.
