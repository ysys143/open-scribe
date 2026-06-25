#!/bin/bash
#
# Open-Scribe installer (XDG Base Directory 준수)
#
# 레이아웃:
#   코드   : $OPEN_SCRIBE_HOME            (기본 ~/.local/lib/open-scribe)
#   설정   : $XDG_CONFIG_HOME/open-scribe (기본 ~/.config/open-scribe)    -> .env
#   데이터 : $XDG_DATA_HOME/open-scribe   (기본 ~/.local/share/open-scribe) -> audio/video/transcript/DB
#   캐시   : $XDG_CACHE_HOME/open-scribe  (기본 ~/.cache/open-scribe)      -> .ytdlp_version_check
#   명령   : $BIN_DIR/scribe              (기본 ~/.local/bin)
#
# 사용법:
#   bash scripts/install.sh                       # 기본(XDG) 경로로 설치
#   bash scripts/install.sh <LIB_DIR> <BIN_DIR>   # 경로 명시(호환용)

set -euo pipefail

# --- repo 루트 (이 스크립트의 한 단계 위) ---
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- 경로 결정 (XDG, 환경변수로 override 가능) ---
LIB_DIR="${OPEN_SCRIBE_HOME:-$HOME/.local/lib/open-scribe}"
CONFIG_DIR="${OPEN_SCRIBE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/open-scribe}"
DATA_DIR="${OPEN_SCRIBE_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/open-scribe}"
CACHE_DIR="${OPEN_SCRIBE_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/open-scribe}"
BIN_DIR="${OPEN_SCRIBE_BIN_DIR:-$HOME/.local/bin}"

# 위치 인자 호환 ($1=LIB_DIR, $2=BIN_DIR)
[ "${1:-}" ] && LIB_DIR="$1"
[ "${2:-}" ] && BIN_DIR="$2"

echo "Open-Scribe 설치 (XDG Base Directory)"
echo "  코드   : $LIB_DIR"
echo "  설정   : $CONFIG_DIR"
echo "  데이터 : $DATA_DIR"
echo "  캐시   : $CACHE_DIR"
echo "  명령   : $BIN_DIR/scribe"
echo ""

mkdir -p "$LIB_DIR" "$CONFIG_DIR" "$DATA_DIR" "$CACHE_DIR" "$BIN_DIR"

# --- 코드 복사 (데이터/비밀/캐시/벤더 제외) ---
echo "코드 복사 중..."
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
    --exclude '.env' --exclude '.env.*' --exclude '*.log' \
    --exclude 'audio' --exclude 'video' --exclude 'transcript' \
    --exclude 'temp_audio' --exclude '*.db' \
    --exclude '.ytdlp_version_check' \
    "$SRC_DIR"/ "$LIB_DIR"/
else
  cp -R "$SRC_DIR"/. "$LIB_DIR"/
  rm -rf "$LIB_DIR/.git" "$LIB_DIR/.venv"
fi

# --- Python 가상환경 + 의존성 (uv 우선) ---
echo "Python 환경 구성 중..."
if command -v uv >/dev/null 2>&1; then
  uv venv "$LIB_DIR/.venv"
  uv pip install --python "$LIB_DIR/.venv/bin/python" --upgrade pip setuptools wheel
  uv pip install --python "$LIB_DIR/.venv/bin/python" -r "$LIB_DIR/requirements.txt"
else
  python3 -m venv "$LIB_DIR/.venv"
  "$LIB_DIR/.venv/bin/pip" install --upgrade pip setuptools wheel
  "$LIB_DIR/.venv/bin/pip" install -r "$LIB_DIR/requirements.txt"
fi

# --- 설정 .env 시드 (없을 때만; 기존 설정은 보존) ---
if [ ! -f "$CONFIG_DIR/.env" ]; then
  if [ -f "$SRC_DIR/.env.example" ]; then
    cp "$SRC_DIR/.env.example" "$CONFIG_DIR/.env"
    chmod 600 "$CONFIG_DIR/.env"
    echo "설정 템플릿 생성: $CONFIG_DIR/.env"
    echo "  -> OPENAI_API_KEY 등 값을 채워주세요."
  fi
else
  echo "기존 설정 유지: $CONFIG_DIR/.env"
fi

# --- 구버전 위치 감지 시 안내 (자동 이동은 하지 않음: 데이터 보호) ---
if [ -f "$HOME/.open-scribe/.env" ] && [ "$CONFIG_DIR" != "$HOME/.open-scribe" ]; then
  echo "[안내] 구버전 설정이 남아 있습니다: ~/.open-scribe/.env"
  echo "       필요한 값을 $CONFIG_DIR/.env 로 옮겨주세요."
fi
if [ -d "$HOME/Documents/open-scribe" ] && [ "$DATA_DIR" != "$HOME/Documents/open-scribe" ]; then
  echo "[안내] 구버전 데이터가 남아 있습니다: ~/Documents/open-scribe"
  echo "       옮기려면: mv ~/Documents/open-scribe/* \"$DATA_DIR\"/"
fi

# --- scribe 명령 래퍼 ---
echo "명령 래퍼 생성: $BIN_DIR/scribe"
cat > "$BIN_DIR/scribe" <<EOF
#!/bin/bash
export OPEN_SCRIBE_HOME="\${OPEN_SCRIBE_HOME:-$LIB_DIR}"
if [[ -f "\$OPEN_SCRIBE_HOME/scribe.sh" ]]; then
  source "\$OPEN_SCRIBE_HOME/scribe.sh"
  scribe "\$@"
else
  echo "[X] open-scribe 코드가 \$OPEN_SCRIBE_HOME 에 없습니다. 재설치하세요."
  exit 1
fi
EOF
chmod +x "$BIN_DIR/scribe"

# --- 셸 rc에 PATH/HOME 등록 (중복 방지) ---
register_shell() {
  local rc="$1"
  [ -f "$rc" ] || return 0
  if grep -q '# open-scribe (XDG)' "$rc"; then
    echo "  이미 등록됨: $rc"
    return 0
  fi
  cp "$rc" "$rc.backup.$(date +%s)"
  cat >> "$rc" <<EOF

# open-scribe (XDG)
export OPEN_SCRIBE_HOME="$LIB_DIR"
export PATH="$BIN_DIR:\$PATH"
EOF
  echo "  등록됨: $rc"
}
echo "셸 설정 등록 중..."
register_shell "$HOME/.zshrc"
register_shell "$HOME/.bashrc"

echo ""
echo "[OK] 설치 완료!"
echo "   새 셸을 열거나: source ~/.zshrc  (또는 ~/.bashrc)"
echo "   확인:           scribe --help"
