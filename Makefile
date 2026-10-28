PYTHON ?= python3

.PHONY: lint test compile check

lint:
	$(PYTHON) -m ruff check .

test:
	$(PYTHON) -m pytest -q

# Byte-compiles every module: catches syntax errors, not type errors. (It was
# called `typecheck` until October 2026, which it never was.)
compile:
	$(PYTHON) -m py_compile main.py shadow_mario/*.py shadow_mario/entities/*.py shadow_mario/scenes/*.py tools/*.py

check: lint compile test
