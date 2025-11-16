run=uv run

fmt:
	${RUN} ruff format
	${RUN} ruff check --fix

lint:
	${RUN} ruff check

release-patch:
	${RUN} bump-my-version bump patch

release-minor:
	${RUN} bump-my-version bump minor

release-major:
	${RUN} bump-my-version bump major

test:
	${RUN} pytest

test-cov:
	${RUN} pytest --cov=compromeets