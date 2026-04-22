RUN := uv run
export PYTHONPATH := $(CURDIR)

setup-transxchange:
	@echo "Installing transxchange2gtfs Node.js dependencies..."
	cd tools/transxchange2gtfs && npm install
	@echo "✓ Setup complete"

fmt:
	$(RUN) ruff format
	$(RUN) ruff check --fix

lint:
	$(RUN) ruff check

release-patch:
	$(RUN) bump-my-version bump patch

release-minor:
	$(RUN) bump-my-version bump minor

release-major:
	$(RUN) bump-my-version bump major

test:
	$(RUN) python -m pytest tests/unit/

test-cov:
	$(RUN) python -m pytest --cov=compromeets tests/unit/

test-integration:
	$(RUN) python -m pytest tests/integration/

test-integration-cov:
	$(RUN) python -m pytest --cov=compromeets tests/integration/