PYTHON ?= python3

.PHONY: lint test typecheck check

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest -q

typecheck:
	$(PYTHON) -m py_compile main.py shadow_mario/*.py shadow_mario/entities/*.py shadow_mario/scenes/*.py

check: lint typecheck test
