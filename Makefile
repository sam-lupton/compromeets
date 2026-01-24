RUN := uv run
PYTHONPATH := $(CURDIR)

setup-transxchange:
	@echo "Installing transxchange2gtfs Node.js dependencies..."
	cd tools/transxchange2gtfs && npm install
	@echo "✓ Setup complete"

fmt:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) ruff format
	PYTHONPATH="$(PYTHONPATH)" $(RUN) ruff check --fix

lint:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) ruff check

release-patch:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) bump-my-version bump patch

release-minor:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) bump-my-version bump minor

release-major:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) bump-my-version bump major

test:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) python -m pytest tests/unit/

test-cov:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) python -m pytest --cov=compromeets tests/unit/

test-integration:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) python -m pytest tests/integration/

test-integration-cov:
	PYTHONPATH="$(PYTHONPATH)" $(RUN) python -m pytest --cov=compromeets tests/integration/