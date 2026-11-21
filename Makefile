install:
	uv venv
	uv sync

run:
	uv run identia-python

test:
	uv run pytest
