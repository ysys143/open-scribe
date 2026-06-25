#!/bin/bash
#
# Open-Scribe uninstaller (XDG Base Directory 준수)
#
# 기본 동작: 코드/명령/캐시/셸설정 제거. 설정(.env)과 데이터(전사물/DB)는 보존.
# 완전 삭제: --purge 옵션을 주면 설정/데이터까지 모두 삭제.
#
# 사용법:
#   bash scripts/uninstall.sh            # 코드/명령/캐시 제거 (설정/데이터 보존)
#   bash scripts/uninstall.sh --purge    # 설정/데이터 포함 완전 삭제

set -euo pipefail

PURGE=0
if [ "${1:-}" = "--purge" ]; then
  PURGE=1
  shift
fi

# --- 경로 결정 (XDG, 환경변수로 override 가능) ---
LIB_DIR="${OPEN_SCRIBE_HOME:-$HOME/.local/lib/open-scribe}"
CONFIG_DIR="${OPEN_SCRIBE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/open-scribe}"
DATA_DIR="${OPEN_SCRIBE_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/open-scribe}"
CACHE_DIR="${OPEN_SCRIBE_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/open-scribe}"
BIN_DIR="${OPEN_SCRIBE_BIN_DIR:-$HOME/.local/bin}"

# 위치 인자 호환 ($1=LIB_DIR, $2=BIN_DIR) — --purge가 아닐 때만
[ "${1:-}" ] && LIB_DIR="$1"
[ "${2:-}" ] && BIN_DIR="$2"

echo "Open-Scribe 제거..."

# 코드 + venv
if [ -d "$LIB_DIR" ]; then
  echo "  코드 제거: $LIB_DIR"
  rm -rf "$LIB_DIR"
fi

# 명령 래퍼
if [ -f "$BIN_DIR/scribe" ]; then
  echo "  명령 제거: $BIN_DIR/scribe"
  rm -f "$BIN_DIR/scribe"
fi

# 캐시 (런타임 재생성 가능)
if [ -d "$CACHE_DIR" ]; then
  echo "  캐시 제거: $CACHE_DIR"
  rm -rf "$CACHE_DIR"
fi

# 셸 rc에서 등록 블록 제거 (신규 XDG + 구버전 모두)
remove_block() {
  local rc="$1"
  [ -f "$rc" ] || return 0
  cp "$rc" "$rc.backup.$(date +%s)"
  # 신규: '# open-scribe (XDG)' + 이어지는 export 2줄
  sed -i.bak '/# open-scribe (XDG)/,+2d' "$rc"
  # 구버전: '# Open-Scribe configuration' ~ 'fi' 블록 및 잔여 export
  sed -i.bak '/# Open-Scribe configuration/,/^fi$/d' "$rc"
  sed -i.bak '/export OPEN_SCRIBE_HOME/d' "$rc"
  sed -i.bak '/export PATH.*open-scribe/d' "$rc"
  rm -f "$rc.bak"
  echo "  셸 설정 정리: $rc"
}
remove_block "$HOME/.zshrc"
remove_block "$HOME/.bashrc"
remove_block "$HOME/.bash_profile"

# Fish (구버전 호환)
if [ -f "$HOME/.config/fish/conf.d/open-scribe.fish" ]; then
  rm -f "$HOME/.config/fish/conf.d/open-scribe.fish"
  echo "  fish 설정 제거"
fi

# 설정/데이터 처리
if [ "$PURGE" = "1" ]; then
  echo "[--purge] 설정/데이터까지 삭제합니다."
  [ -d "$CONFIG_DIR" ] && { echo "  설정 제거: $CONFIG_DIR"; rm -rf "$CONFIG_DIR"; }
  [ -d "$DATA_DIR" ]   && { echo "  데이터 제거: $DATA_DIR"; rm -rf "$DATA_DIR"; }
else
  echo ""
  echo "설정/데이터는 보존했습니다:"
  echo "  설정   : $CONFIG_DIR   (.env)"
  echo "  데이터 : $DATA_DIR     (전사물/DB)"
  echo "완전히 지우려면: bash scripts/uninstall.sh --purge"
fi

echo ""
echo "[OK] 제거 완료. 셸을 재시작하거나 source ~/.zshrc 하세요."
