#!/bin/bash

set -e

INSTALL_DIR="${1:-$HOME/.local/share/open-scribe}"
BIN_DIR="${2:-$HOME/.local/bin}"

echo "Configuring shell environments..."

# Detect available shells and configure them
configure_shell() {
    local shell_name=$1
    local config_file=$2
    local profile_file=$3

    echo "Configuring $shell_name..."

    # Create backup if config file exists
    if [[ -f "$config_file" ]]; then
        cp "$config_file" "${config_file}.backup.$(date +%s)"
    fi

    # Create config file if it doesn't exist
    touch "$config_file"

    # Check if open-scribe path is already in config
    if ! grep -q "OPEN_SCRIBE_HOME" "$config_file"; then
        cat >> "$config_file" << 'EOF'

# Open-Scribe configuration
export OPEN_SCRIBE_HOME="${OPEN_SCRIBE_HOME:-$HOME/.local/share/open-scribe}"
export PATH="$HOME/.local/bin:$PATH"

# Source scribe function if available
if [[ -f "$OPEN_SCRIBE_HOME/scribe.sh" ]]; then
    source "$OPEN_SCRIBE_HOME/scribe.sh"
fi
EOF
        echo "✅ Added to $shell_name configuration"
    else
        echo "⚠️  Already configured in $shell_name"
    fi
}

# Zsh configuration
if [[ -f "$HOME/.zshrc" ]]; then
    configure_shell "zsh" "$HOME/.zshrc" "$HOME/.zprofile"
fi

# Bash configuration
if [[ -f "$HOME/.bashrc" ]]; then
    configure_shell "bash" "$HOME/.bashrc" "$HOME/.bash_profile"
elif [[ -f "$HOME/.bash_profile" ]]; then
    configure_shell "bash" "$HOME/.bash_profile"
fi

# Fish shell configuration (if available)
if [[ -f "$HOME/.config/fish/config.fish" ]]; then
    echo "Configuring fish shell..."
    mkdir -p "$HOME/.config/fish/conf.d"
    if [[ ! -f "$HOME/.config/fish/conf.d/open-scribe.fish" ]]; then
        cat > "$HOME/.config/fish/conf.d/open-scribe.fish" << 'EOF'
# Open-Scribe configuration
set -gx OPEN_SCRIBE_HOME $HOME/.local/share/open-scribe
set -gx PATH $HOME/.local/bin $PATH

# Source scribe function if available
if test -f $OPEN_SCRIBE_HOME/scribe.fish
    source $OPEN_SCRIBE_HOME/scribe.fish
end
EOF
        echo "✅ Added to fish shell configuration"
    else
        echo "⚠️  Already configured in fish shell"
    fi
fi

# Create wrapper scripts in BIN_DIR
echo "Creating wrapper scripts..."

# Create bash/zsh wrapper
cat > "$BIN_DIR/scribe" << 'EOF'
#!/bin/bash
INSTALL_DIR="${OPEN_SCRIBE_HOME:-$HOME/.local/share/open-scribe}"
if [[ -f "$INSTALL_DIR/scribe.sh" ]]; then
    source "$INSTALL_DIR/scribe.sh"
    scribe "$@"
else
    echo "❌ Error: open-scribe not found at $INSTALL_DIR"
    exit 1
fi
EOF
chmod +x "$BIN_DIR/scribe"

# Note: PowerShell configuration should be done manually on Windows
# Users can import the scribe.ps1 module or add it to their PowerShell profile

echo "✅ Wrapper scripts created"
echo ""
echo "Installation complete!"
echo "Please run: source ~/.bashrc (or ~/.zshrc)"
echo "Then test with: scribe --help"
