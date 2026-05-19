#!/bin/bash
set -euo pipefail

# Open-Scribe Cloud 배포 스크립트
# 사용법: ./deploy.sh [PROJECT_ID]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.gcloud"
REGION="asia-northeast3"
SERVICE="open-scribe"

# .env.gcloud 확인
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: $ENV_FILE 파일이 없습니다."
  echo "cp .env.gcloud.example .env.gcloud 후 값을 채워주세요."
  exit 1
fi

# .env.gcloud 로드
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
  key=$(echo "$key" | xargs)
  export "$key=$value"
done < "$ENV_FILE"

# 필수 값 체크
for var in OPENAI_API_KEY TELEGRAM_BOT_TOKEN NOTION_API_KEY NOTION_DATABASE_ID; do
  if [[ -z "${!var:-}" ]]; then
    echo "Error: $var 가 .env.gcloud에 설정되지 않았습니다."
    exit 1
  fi
done

# GCP 프로젝트 설정
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: GCP 프로젝트 ID를 지정해주세요."
  echo "사용법: ./deploy.sh <PROJECT_ID>"
  exit 1
fi

echo "=== Open-Scribe Cloud 배포 ==="
echo "프로젝트: $PROJECT_ID"
echo "리전: $REGION"
echo ""

# 1. GCP 프로젝트 설정 + API 활성화
echo "[1/4] GCP 설정..."
gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com secretmanager.googleapis.com

# 2. Secrets 등록
echo "[2/4] Secrets 등록..."
SECRET_KEYS=(OPENAI_API_KEY TELEGRAM_BOT_TOKEN NOTION_API_KEY NOTION_DATABASE_ID)
for key in "${SECRET_KEYS[@]}"; do
  value="${!key}"
  if gcloud secrets describe "$key" &>/dev/null; then
    echo "  $key: 새 버전 추가"
    echo -n "$value" | gcloud secrets versions add "$key" --data-file=-
  else
    echo "  $key: 생성"
    echo -n "$value" | gcloud secrets create "$key" --data-file=-
  fi
done

# 3. Cloud Run 배포
echo "[3/4] Cloud Run 배포..."
gcloud run deploy "$SERVICE" \
  --source "$SCRIPT_DIR" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest,NOTION_API_KEY=NOTION_API_KEY:latest,NOTION_DATABASE_ID=NOTION_DATABASE_ID:latest" \
  --set-env-vars="^@^OPEN_SCRIBE_ENGINE=${OPEN_SCRIBE_ENGINE:-gpt-4o-mini-transcribe}@OPENAI_SUMMARY_MODEL=${OPENAI_SUMMARY_MODEL:-gpt-5-mini}@OPENAI_SUMMARY_LANGUAGE=${OPENAI_SUMMARY_LANGUAGE:-Korean}@OPENAI_TRANSLATE_MODEL=${OPENAI_TRANSLATE_MODEL:-gpt-5-mini}@OPENAI_TRANSLATE_LANGUAGE=${OPENAI_TRANSLATE_LANGUAGE:-Korean}${WEBSHARE_PROXY_LIST_URL:+@WEBSHARE_PROXY_LIST_URL=${WEBSHARE_PROXY_LIST_URL}}" \
  --timeout=3600 \
  --memory=1Gi

# 4. Telegram Webhook 등록
echo "[4/4] Telegram Webhook 등록..."
CLOUD_RUN_URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')
WEBHOOK_URL="$CLOUD_RUN_URL/webhook"

RESULT=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}")
echo "  Webhook: $WEBHOOK_URL"
echo "  결과: $RESULT"

echo ""
echo "=== 배포 완료 ==="
echo "서비스 URL: $CLOUD_RUN_URL"
echo "Telegram 봇으로 YouTube URL을 보내보세요!"
