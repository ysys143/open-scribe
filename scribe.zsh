# Open-Scribe zsh helper
# - Supports both YouTube URLs and local audio file paths
# - Expands ~ and env vars for local paths
# - Activates project-local .venv before running
# - No hardcoded paths: resolves repo dir from this file path or $OPEN_SCRIBE_REPO_DIR

function scribe() {
  # Allow override via env var; fallback to default project path
  local DEFAULT_REPO_DIR="/Users/jaesolshin/Documents/GitHub/open-scribe"
  local REPO_DIR="${OPEN_SCRIBE_REPO_DIR:-$DEFAULT_REPO_DIR}"
  local ENTRY="${REPO_DIR}/main.py"
  local VENV_ACTIVATE="${REPO_DIR}/.venv/bin/activate"

  if [[ -z "$1" ]]; then
    echo "❌ 오류: YouTube URL 또는 로컬 오디오 파일 경로를 지정해주세요."
    echo "사용법: scribe <YouTube_URL|local_audio_path> [옵션들...]"
    return 1
  fi

  # Activate virtualenv if available
  if [[ -f "$VENV_ACTIVATE" ]]; then
    source "$VENV_ACTIVATE"
  fi

  # Input normalization: strip quotes and expand ~ / env vars for local paths only
  local RAW_INPUT="$1"; shift
  local EXPANDED_INPUT
  
  # Only expand for local paths, not URLs
  if [[ "$RAW_INPUT" == http://* || "$RAW_INPUT" == https://* ]]; then
    EXPANDED_INPUT="$RAW_INPUT"
  else
    EXPANDED_INPUT=$(eval echo "$RAW_INPUT")
  fi

  # Decide whether URL or local file
  if [[ "$EXPANDED_INPUT" == http://* || "$EXPANDED_INPUT" == https://* ]]; then
    python "$ENTRY" "$EXPANDED_INPUT" "$@"
  else
    # Treat as local audio path (main.py will revalidate)
    python "$ENTRY" "$EXPANDED_INPUT" "$@"
  fi
}

# Optional: alias for convenience
alias oscribe=scribe


