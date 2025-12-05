.PHONY: install uninstall update help

# Installation directory
INSTALL_DIR := $(HOME)/.local/share/open-scribe
BIN_DIR := $(HOME)/.local/bin
SHELL_CONFIG_DIR := $(HOME)

# Project root (where Makefile is located)
PROJECT_ROOT := $(shell pwd)

help:
	@echo "Open-Scribe Installation & Management"
	@echo "======================================"
	@echo "Available targets:"
	@echo "  make install   - Install open-scribe to ~/.local/share/open-scribe"
	@echo "  make uninstall - Remove open-scribe and shell configuration"
	@echo "  make update    - Update open-scribe and dependencies"
	@echo "  make help      - Show this help message"

install:
	@echo "Installing open-scribe..."
	@echo "Target directory: $(INSTALL_DIR)"
	@mkdir -p $(INSTALL_DIR)
	@mkdir -p $(BIN_DIR)
	@echo "Copying project files..."
	@cp -r $(PROJECT_ROOT)/* $(INSTALL_DIR)/
	@echo "Setting up Python environment with uv..."
	@cd $(INSTALL_DIR) && uv venv
	@cd $(INSTALL_DIR) && uv pip install -r requirements.txt
	@echo "Running shell configuration script..."
	@bash $(INSTALL_DIR)/scripts/install.sh $(INSTALL_DIR) $(BIN_DIR)
	@echo ""
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Please run: source ~/.bashrc  (or ~/.zshrc / PowerShell profile)"
	@echo "Then test with: scribe --help"

uninstall:
	@echo "Uninstalling open-scribe..."
	@bash $(PROJECT_ROOT)/scripts/uninstall.sh $(INSTALL_DIR) $(BIN_DIR) $(SHELL_CONFIG_DIR)
	@echo "✅ Uninstall complete!"

update:
	@echo "Updating open-scribe..."
	@cd $(INSTALL_DIR) && git pull
	@cd $(INSTALL_DIR) && uv pip install --upgrade -r requirements.txt
	@echo "✅ Update complete!"

.DEFAULT_GOAL := help
