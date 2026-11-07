# Troubleshooting Guide

## 목차
1. [설치 문제](#설치-문제)
2. [전사 오류](#전사-오류)
3. [데이터베이스 문제](#데이터베이스-문제)
4. [API 관련 오류](#api-관련-오류)
5. [성능 문제](#성능-문제)
6. [파일 시스템 오류](#파일-시스템-오류)
7. [네트워크 문제](#네트워크-문제)
8. [디버깅 및 FAQ](#디버깅-팁)

---

## 설치 문제

### 문제: pip install 실패
```
ERROR: Could not find a version that satisfies the requirement textual
```

**해결책:**
```bash
# Python 버전 확인 (3.8+ 필요)
python --version

# pip 업그레이드
pip install --upgrade pip

# 가상환경 사용
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate  # Windows

# 패키지 재설치
pip install -r requirements.txt
```

### 문제: ffmpeg not found
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**해결책:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# ffmpeg.org에서 다운로드 후 PATH 추가
```

---

## 전사 오류

### 문제: OpenAI API 키 오류
```
Error: Invalid API key provided
```

**해결책:**
```bash
# .env 파일 확인
cat .env
# OPENAI_API_KEY=sk-... 형식이어야 함

# API 키 유효성 확인
python -c "
import openai
openai.api_key = 'your-key'
print(openai.Model.list())
"
```

### 문제: 25MB 파일 크기 제한
```
Error: Audio file too large for API (>25MB)
```

**해결책:**
```bash
# 자동 압축 활성화 (기본값)
python main.py URL --engine whisper-api

# 수동 압축
ffmpeg -i input.mp3 -b:a 64k output.mp3

# 로컬 엔진 사용
python main.py URL --engine whisper-cpp
```

### 문제: 타임스탬프가 표시되지 않음

**해결책:**
```python
# 엔진별 타임스탬프 지원 확인
- whisper-api: 지원 (verbose_json 형식)
- gpt-4o: 미지원 (청크 분할로 근사치 생성)
- youtube-transcript-api: 지원 (자막 기반)
- whisper-cpp: 지원

# 타임스탬프 옵션 명시
python main.py URL --timestamp --engine whisper-api
```

---

## 데이터베이스 문제

### 문제: Database is locked
```
sqlite3.OperationalError: database is locked
```

**해결책:**
```bash
# 프로세스 확인 및 종료
ps aux | grep python
kill -9 [PID]

# 데이터베이스 백업 및 재생성
cp transcription_jobs.db transcription_jobs.db.backup
rm transcription_jobs.db
python -c "from src.database import TranscriptionDatabase; db = TranscriptionDatabase()"

# WAL 모드 활성화 (동시 접근 개선)
sqlite3 transcription_jobs.db "PRAGMA journal_mode=WAL;"
```

### 문제: 검색이 느림

**해결책:**
```sql
-- 인덱스 확인
sqlite3 transcription_jobs.db "
SELECT name FROM sqlite_master WHERE type='index';
"

-- 인덱스 재생성
sqlite3 transcription_jobs.db "
CREATE INDEX IF NOT EXISTS idx_title ON transcription_jobs(title);
CREATE INDEX IF NOT EXISTS idx_created_at ON transcription_jobs(created_at);
VACUUM;
"
```

---

## API 관련 오류

### 문제: Rate limit exceeded
```
openai.error.RateLimitError: Rate limit reached
```

**해결책:**
```python
# 재시도 로직 구현 (자동)
# src/transcribers/openai.py에 이미 구현됨

# 수동 대기
import time
time.sleep(60)  # 1분 대기

# 병렬 처리 워커 수 감소
python main.py PLAYLIST_URL --parallel 1
```

### 문제: Timeout error

**해결책:**
```python
# 타임아웃 증가
export OPENAI_TIMEOUT=300  # 5분

# 또는 코드에서
client = OpenAI(timeout=300)
```

---

## 성능 문제

### 문제: 전사가 매우 느림

**해결책:**
```bash
# 더 빠른 엔진 사용
python main.py URL --engine youtube-transcript-api  # 가장 빠름

# 병렬 처리 활성화
python main.py PLAYLIST_URL --parallel 4

# GPU 가속 (whisper.cpp)
./whisper.cpp/build/bin/whisper-cli --use-gpu
```

### 문제: 메모리 부족
```
MemoryError: Unable to allocate array
```

**해결책:**
```bash
# 청크 크기 감소
export CHUNK_SIZE=300  # 5분 단위로 분할

# 스트리밍 모드 사용
python main.py URL --stream

# 워커 수 감소
python main.py URL --parallel 1
```

---

## 파일 시스템 오류

### 문제: Permission denied
```
PermissionError: [Errno 13] Permission denied: '/path/to/file'
```

**해결책:**
```bash
# 권한 확인
ls -la ~/Documents/open-scribe/

# 권한 부여
chmod -R 755 ~/Documents/open-scribe/

# 소유자 변경
chown -R $USER:$USER ~/Documents/open-scribe/
```

### 문제: 디스크 공간 부족

**해결책:**
```bash
# 공간 확인
df -h

# 임시 파일 정리
rm -rf ~/Documents/open-scribe/audio/*.tmp
rm -rf ~/Documents/open-scribe/temp_audio/*

# 오래된 파일 삭제
find ~/Documents/open-scribe -name "*.mp3" -mtime +30 -delete
```

---

## 네트워크 문제

### 문제: YouTube 다운로드 실패
```
ERROR: Unable to extract video data
```

**해결책:**
```bash
# yt-dlp 업데이트
pip install --upgrade yt-dlp

# 쿠키 사용 (로그인 필요 시)
yt-dlp --cookies cookies.txt URL

# VPN/프록시 설정
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

### 문제: SSL 인증서 오류

**해결책:**
```bash
# 인증서 업데이트 (macOS)
brew install ca-certificates

# Python 인증서 업데이트
pip install --upgrade certifi

# 임시 해결 (보안 주의)
export PYTHONHTTPSVERIFY=0
```

---

## 디버깅 팁

### 상세 로그 활성화
```bash
# 환경 변수 설정
export DEBUG=1
export LOG_LEVEL=DEBUG

# 또는 실행 시
python main.py URL --verbose
```

### 데이터베이스 직접 확인
```bash
# SQLite CLI
sqlite3 transcription_jobs.db

# 테이블 구조 확인
.schema

# 최근 작업 확인
SELECT * FROM transcription_jobs ORDER BY created_at DESC LIMIT 10;
```

### 프로세스 모니터링
```bash
# CPU/메모리 사용량
htop
# 또는
top -u $USER

# 파일 핸들 확인
lsof | grep python

# 네트워크 연결 확인
netstat -an | grep ESTABLISHED
```

---

## 자주 묻는 질문 (FAQ)

### Q: 가장 빠른 전사 방법은?
**A:** 
1. YouTube 자막 API (자막 있는 경우)
2. whisper.cpp + GPU
3. Whisper API
4. GPT-4o-mini
5. GPT-4o

### Q: 비용을 절감하려면?
**A:**
- YouTube 자막 API 우선 사용 (무료)
- whisper.cpp 로컬 실행 (무료)
- GPT-4o-mini 사용 (GPT-4o보다 저렴)

### Q: 오프라인에서 사용 가능한가요?
**A:**
- whisper.cpp 엔진만 오프라인 지원
- 다운로드된 오디오 파일 필요
- 요약/번역은 온라인 필요

---

## 지원 및 문의

### 버그 리포트
GitHub Issues: https://github.com/open-scribe/open-scribe/issues

### 커뮤니티
- Discord: [참여 링크]
- 포럼: [포럼 링크]

### 직접 문의
- Email: support@open-scribe.org

---

최종 업데이트: 2025-09-08