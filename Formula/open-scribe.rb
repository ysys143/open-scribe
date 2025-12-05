class OpenScribe < Formula
  desc "YouTube video transcription tool with multiple engines"
  homepage "https://github.com/ysys143/open-scribe"
  url "https://github.com/ysys143/open-scribe/archive/refs/tags/0.1.0.tar.gz"
  sha256 "37721505352e2330974bd6b3ffab43fa692aa22d6349bb4c82c05cc378b4afb9"
  license "MIT"

  depends_on "python@3.11"
  depends_on "uv"

  def install
    # Create installation directory
    prefix_dir = libexec

    # Copy project files to libexec
    cp_r ".", prefix_dir

    # Create Python virtual environment
    system "uv", "venv", "#{prefix_dir}/.venv"

    # Install dependencies using uv
    system "uv", "pip", "install", "--upgrade", "pip", "setuptools", "wheel", "-p", "#{prefix_dir}/.venv"
    system "uv", "pip", "install", "-r", "#{prefix_dir}/requirements.txt", "-p", "#{prefix_dir}/.venv"

    # Create wrapper script with .env initialization
    bin.mkpath
    (bin/"scribe").write <<~EOS
      #!/bin/bash

      INSTALL_DIR="#{prefix_dir}"
      ENTRY="${INSTALL_DIR}/main.py"
      VENV_ACTIVATE="${INSTALL_DIR}/.venv/bin/activate"
      ENV_FILE="$HOME/.open-scribe/.env"

      # Helper function to initialize .env file interactively
      function _initialize_env() {
        local ENV_FILE="$1"

        # If .env already exists, don't reinitialize
        if [[ -f "$ENV_FILE" ]]; then
          return 0
        fi

        # If OPENAI_API_KEY is already set via environment, create .env from it
        if [[ -n "$OPENAI_API_KEY" ]]; then
          mkdir -p "$(dirname "$ENV_FILE")"
          {
            echo "# Open-Scribe Configuration"
            echo "# Generated on $(date)"
            echo ""
            echo "# OpenAI API Key (required for GPT-4o and Whisper API)"
            echo "OPENAI_API_KEY=$OPENAI_API_KEY"
          } > "$ENV_FILE"
          echo "✅ Created $ENV_FILE from OPENAI_API_KEY environment variable"
          return 0
        fi

        # Interactive setup
        echo ""
        echo "🔧 First time setup: Open-Scribe needs configuration"
        echo ""
        echo "OpenAI API Key is required to use transcription features."
        echo "Get your key at: https://platform.openai.com/api-keys"
        echo ""

        read -p "Enter your OpenAI API Key (or press Enter to skip): " API_KEY

        if [[ -z "$API_KEY" ]]; then
          echo "⚠️  Skipped API key setup. You can set it later:"
          echo "   export OPENAI_API_KEY='your-key-here'"
          echo "   Or edit: $ENV_FILE"
          return 0
        fi

        mkdir -p "$(dirname "$ENV_FILE")"
        {
          echo "# Open-Scribe Configuration"
          echo "# Generated on $(date)"
          echo ""
          echo "# OpenAI API Key (required for GPT-4o and Whisper API)"
          echo "OPENAI_API_KEY=$API_KEY"
        } > "$ENV_FILE"
        chmod 600 "$ENV_FILE"
        echo "✅ Configuration saved to $ENV_FILE"
      }

      # Helper function to check and update yt-dlp
      function _check_and_update_ytdlp() {
        local VENV_PATH="$1"
        local VERSION_CHECK_FILE="${VENV_PATH}/../.ytdlp_version_check"
        local CURRENT_DATE=$(date +%Y%m%d)

        # Check if we already checked today
        if [[ -f "$VERSION_CHECK_FILE" ]]; then
          local LAST_CHECK=$(cat "$VERSION_CHECK_FILE" 2>/dev/null || echo "0")
          if [[ "$LAST_CHECK" == "$CURRENT_DATE" ]]; then
            return 0
          fi
        fi

        echo "🔍 yt-dlp 버전 확인 중..."
        local CURRENT_VERSION=$(uv pip list -p "$VENV_PATH" 2>/dev/null | grep yt-dlp | awk '{print $2}' || echo "not_found")

        if [[ "$CURRENT_VERSION" != "not_found" ]]; then
          echo "📦 yt-dlp 업데이트 확인 중..."
          local UPDATE_OUTPUT=$(uv pip install --upgrade yt-dlp -p "$VENV_PATH" 2>&1)
          if echo "$UPDATE_OUTPUT" | grep -q "Successfully installed"; then
            echo "✅ yt-dlp가 업데이트되었습니다"
          else
            echo "✅ yt-dlp가 최신 버전입니다: $CURRENT_VERSION"
          fi
        fi

        mkdir -p "$(dirname "$VERSION_CHECK_FILE")"
        echo "$CURRENT_DATE" > "$VERSION_CHECK_FILE"
      }

      # Initialize .env if not exists
      _initialize_env "$ENV_FILE"

      # Load environment variables from .env
      if [[ -f "$ENV_FILE" ]]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
      fi

      # Activate virtualenv
      if [[ -f "$VENV_ACTIVATE" ]]; then
        source "$VENV_ACTIVATE"
      fi

      # Check and update yt-dlp if URL is provided
      if [[ $# -gt 0 && ("$1" == http://* || "$1" == https://*) ]]; then
        _check_and_update_ytdlp "$INSTALL_DIR/.venv"
      fi

      # Run transcription
      exec "#{prefix_dir}/.venv/bin/python" "$ENTRY" "$@"
    EOS
    (bin/"scribe").chmod 0755
  end

  def post_install
    puts <<~EOS
      ✅ Open-Scribe installed successfully!

      To get started:
        scribe "https://www.youtube.com/watch?v=VIDEO_ID"

      On first run, you'll be prompted for your OpenAI API Key.
      Get your key at: https://platform.openai.com/api-keys

      Options:
        scribe "URL" --engine whisper-api --summary
        scribe "URL" --timestamp --srt
        scribe "PLAYLIST_URL" --parallel 4

      For more help:
        scribe --help
    EOS
  end

  test do
    system "#{bin}/scribe", "--help"
  end
end
