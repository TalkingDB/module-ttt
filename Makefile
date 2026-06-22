SHELL := /bin/bash

DEFAULT_MODE := git
MODE ?= $(DEFAULT_MODE)

.DEFAULT_GOAL := help

# Detect if Infisical is initialized
INFISICAL_PRESENT := $(shell test -f .infisical.json && echo "true" || echo "false")

COMMON_CMD = poetry run python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --loop uvloop --http httptools

local:
	@if [ "$(INFISICAL_PRESENT)" = "true" ]; then \
		echo "Running with Infisical..."; \
		infisical run --watch -- $(COMMON_CMD) --reload --reload-dir ./ --reload-dir ../base-tdb-models --reload-dir ../base-tdb-clients --reload-dir ../base-tdb-helpers --reload-dir ../package-content-elementizer; \
	else \
		echo "Running with .env file"; \
		$(COMMON_CMD) --reload --reload-dir ./ --reload-dir ../base-tdb-models --reload-dir ../base-tdb-clients --reload-dir ../base-tdb-helpers --reload-dir ../package-content-elementizer; \
	fi

run:
	@if [ "$(INFISICAL_PRESENT)" = "true" ]; then \
		echo "Running with Infisical..."; \
		infisical run -- $(COMMON_CMD) --workers 4; \
	else \
		echo "Running with .env file"; \
		$(COMMON_CMD) --workers 4; \
	fi

sync:
	@echo "🔄 Running sync_git_deps.py with mode: $(MODE)"
	python3 sync_git_deps.py --mode "$(MODE)"

sync-dry-run:
	@echo "🔍 Dry-run sync for validation (mode: $(MODE))"
	python3 sync_git_deps.py --mode "$(MODE)" --dry-run

install-hooks:
	@echo "Installing git hooks..."
	@cp -f git-hooks/* .git/hooks/
	@chmod +x .git/hooks/* 2>/dev/null || true
	@echo "Git hooks installed!"

docker-publish:
	@bash docker-publish.sh

help:
	@echo ""
	@echo "Targets:"
	@echo "  make local   → start local stack"
	@echo "  make sync MODE=<git|local>      → sync git deps (default: git)"
	@echo "  make sync-dry-run MODE=<git|local> → validate deps without changing files"
	@echo "  install-hooks → install git hooks"
	@echo ""
