.PHONY: install uninstall purge update help

# Project root (where Makefile is located)
PROJECT_ROOT := $(shell pwd)

# XDG 레이아웃 (자세한 경로는 scripts/install.sh가 결정)
#   코드   : ~/.local/lib/open-scribe        ($OPEN_SCRIBE_HOME)
#   설정   : ~/.config/open-scribe/.env      ($XDG_CONFIG_HOME)
#   데이터 : ~/.local/share/open-scribe      ($XDG_DATA_HOME)
#   캐시   : ~/.cache/open-scribe            ($XDG_CACHE_HOME)
#   명령   : ~/.local/bin/scribe

help:
	@echo "Open-Scribe Installation & Management (XDG Base Directory)"
	@echo "=========================================================="
	@echo "Available targets:"
	@echo "  make install   - 코드를 ~/.local/lib/open-scribe 에 설치하고 명령/설정 구성"
	@echo "  make uninstall - 코드/명령/캐시 제거 (설정/데이터는 보존)"
	@echo "  make purge     - 설정/데이터까지 포함해 완전 삭제"
	@echo "  make update    - 코드/의존성 갱신 (재설치)"
	@echo "  make help      - 이 도움말 표시"

install: check-python
	@bash $(PROJECT_ROOT)/scripts/install.sh

uninstall:
	@bash $(PROJECT_ROOT)/scripts/uninstall.sh

purge:
	@bash $(PROJECT_ROOT)/scripts/uninstall.sh --purge

update: check-python
	@echo "Updating open-scribe (re-install)..."
	@bash $(PROJECT_ROOT)/scripts/install.sh
	@echo "[OK] Update complete!"

check-python:
	@command -v python3 >/dev/null 2>&1 || { \
		echo "[X] Error: Python 3 is not installed"; \
		echo ""; \
		echo "Please install Python 3.8 or later:"; \
		echo "  macOS (Homebrew):  brew install python@3.11"; \
		echo "  Ubuntu/Debian:     sudo apt-get install python3"; \
		echo "  Windows:           https://www.python.org/downloads/"; \
		echo ""; \
		exit 1; \
	}

check-make:
	@command -v make >/dev/null 2>&1 || { \
		echo "[X] Error: make is not installed"; \
		echo ""; \
		echo "Please install make:"; \
		echo "  macOS (Homebrew):  brew install make"; \
		echo "  Ubuntu/Debian:     sudo apt-get install build-essential"; \
		echo ""; \
		exit 1; \
	}

.DEFAULT_GOAL := help
