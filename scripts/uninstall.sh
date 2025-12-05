#!/bin/bash

set -e

INSTALL_DIR="${1:-$HOME/.local/share/open-scribe}"
BIN_DIR="${2:-$HOME/.local/bin}"
SHELL_CONFIG_DIR="${3:-$HOME}"

echo "Uninstalling open-scribe..."

# Remove installation directory
if [[ -d "$INSTALL_DIR" ]]; then
    echo "Removing $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
fi

# Remove wrapper scripts
if [[ -f "$BIN_DIR/scribe" ]]; then
    echo "Removing $BIN_DIR/scribe..."
    rm -f "$BIN_DIR/scribe"
fi

# Remove shell configuration
remove_from_shell() {
    local config_file=$1
    if [[ -f "$config_file" ]]; then
        echo "Removing open-scribe from $config_file..."

        # Create backup
        cp "$config_file" "${config_file}.backup.$(date +%s)"

        # Remove open-scribe configuration block
        sed -i.bak '/^# Open-Scribe configuration$/,/^fi$/d' "$config_file"
        sed -i.bak '/^export OPEN_SCRIBE_HOME/d' "$config_file"
        sed -i.bak '/^export PATH.*open-scribe/d' "$config_file"

        # Clean up backup from sed
        rm -f "${config_file}.bak"
    fi
}

# Remove from Zsh
if [[ -f "$SHELL_CONFIG_DIR/.zshrc" ]]; then
    remove_from_shell "$SHELL_CONFIG_DIR/.zshrc"
fi

# Remove from Bash
if [[ -f "$SHELL_CONFIG_DIR/.bashrc" ]]; then
    remove_from_shell "$SHELL_CONFIG_DIR/.bashrc"
fi

if [[ -f "$SHELL_CONFIG_DIR/.bash_profile" ]]; then
    remove_from_shell "$SHELL_CONFIG_DIR/.bash_profile"
fi

# Remove from Fish shell
if [[ -f "$SHELL_CONFIG_DIR/.config/fish/conf.d/open-scribe.fish" ]]; then
    echo "Removing open-scribe from fish shell..."
    rm -f "$SHELL_CONFIG_DIR/.config/fish/conf.d/open-scribe.fish"
fi

echo "✅ Uninstall complete!"
echo "Please run: source ~/.bashrc (or ~/.zshrc)"
echo "Or reload your shell to complete the removal"
echo ""
echo "Note: For Windows PowerShell, manually remove the scribe.ps1 import from your profile"
