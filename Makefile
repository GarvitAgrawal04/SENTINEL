# `make run` does the same as `bash setup.sh`. Needs only Python 3.10+, Git and make.
PYTHON ?= python3
HOST   ?= 127.0.0.1
PORT   ?= 8000
BIN    := .venv/bin

.PHONY: run install test selftest scan bench clean help

help:
	@echo "make run       set up (first time) and start the API on http://$(HOST):$(PORT)"
	@echo "make install   create .venv, install pinned dependencies, create .env"
	@echo "make test      run the test suite"
	@echo "make scan      scan this repository with Sentinel"
	@echo "make bench     run precision_gate check against MAIN and HELDOUT corpora"
	@echo "make clean     remove .venv and caches (keeps .env)"

.venv/.installed: requirements.txt requirements-dev.txt pyproject.toml
	$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else "Python 3.10 or newer is required")'
	$(PYTHON) -m venv .venv
	$(BIN)/python -m pip install --quiet --upgrade pip
	$(BIN)/python -m pip install --quiet -r requirements-dev.txt
	$(BIN)/python -m pip install --quiet --no-deps -e .
	@touch $@

.env:
	cp .env.example .env

install: .venv/.installed .env

run: install
	$(BIN)/python -m uvicorn sentinel.api:app --host $(HOST) --port $(PORT)

test: install
	$(BIN)/python -m pytest -q

selftest: install
	$(BIN)/python -m sentinel.cli selftest

scan: install
	$(BIN)/python -m sentinel.cli scan .

MAIN    ?= $(SENTINEL_CORPUS_MAIN)
HELDOUT ?= $(SENTINEL_CORPUS_HELDOUT)

bench: install
	@test -n "$(MAIN)" -a -n "$(HELDOUT)" || (echo "error: set MAIN and HELDOUT (or SENTINEL_CORPUS_MAIN and SENTINEL_CORPUS_HELDOUT) environment variables" && exit 1)
	$(BIN)/python bench/precision_gate.py check $(MAIN) $(HELDOUT)

clean:
	rm -rf .venv .pytest_cache build dist *.egg-info
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
