
# YouTube 비디오 전사 도구

YouTube 비디오를 다양한 엔진으로 전사하고 요약하는 CLI 도구입니다.

## 설치

```sh
pip install -r requirements.txt
```

## 사용법

```sh
python trans.py [url] [options]
```

### 전사 엔진 옵션
`--engine` 또는 `-e` 옵션으로 선택 (기본값: gpt-4o-mini-transcribe)

- `gpt-4o-transcribe` (별칭: `high`) - OpenAI GPT-4o 고품질
- `gpt-4o-mini-transcribe` (별칭: `medium`) - OpenAI GPT-4o-mini 중간품질 (기본값)
- `whisper-api` (별칭: `whisper-cloud`) - OpenAI Whisper API
- `whisper-cpp` (별칭: `whisper-local`) - whisper.cpp 로컬 실행
- `youtube-transcript-api` (별칭: `youtube`) - YouTube 자막 API

### 주요 옵션
- `--stream` / `--no-stream` (`-s` / `-ns`) - 실시간 출력 여부 (기본: True)
- `--downloads` / `--no-downloads` (`-d` / `-nd`) - Downloads 폴더 저장 여부 (기본: True)
- `--summary` / `--no-summary` - AI 요약 생성 (GPT-4o-mini 사용) (기본: True)
- `--verbose` / `--no-verbose` (`-v`) - 상세한 요약 출력 (기본: True)
- `--timestamp` (`-t`) - 타임스탬프 포함 (기본: False)
- `--audio` - 오디오 파일 보관 (기본: False)
- `--video` - 비디오 다운로드 (기본: False)
- `--srt` - SRT 자막 파일 생성 (기본: False)
- `--translate` - 한국어로 번역 (기본: False)
- `--force` (`-f`) - 기존 파일 덮어쓰기, 재전사 강제 실행
- `--help` - 도움말 표시

   
## 동작 방식

### YouTube Transcript API 엔진 선택 시
- YouTube의 자막 데이터를 직접 가져옴
- 오디오 다운로드 불필요
- 가장 빠른 처리 속도

### 다른 엔진 선택 시
- yt-dlp Python 라이브러리로 오디오 자동 다운로드
- 선택한 엔진으로 오디오 파일 전사
- 실시간 다운로드 진행률 표시

### 파일 저장 위치
- 전사 결과: `~/Documents/GitHub/yt-trans/transcript/`
- 오디오 파일: `~/Documents/GitHub/yt-trans/audio/`
- 비디오 파일: `~/Documents/GitHub/yt-trans/video/`
- Downloads 폴더 복사본: `~/Downloads/` (옵션)

### AI 요약 기능
- GPT-4o-mini를 사용한 한국어 요약
- 간단 요약 (기본): 3줄 이내 핵심 요약
- 상세 요약 (`--verbose`): 
  1. 3줄 이내 핵심 요약
  2. 시간대별 내용 정리
  3. 상세한 분석 및 비판적 의견

## 고급 기능

### 비디오 및 자막 처리
- `--video`: 비디오 파일 다운로드
- `--srt`: SRT 자막 파일 생성
- `--translate`: 한국어로 번역 (영어 콘텐츠의 경우)

### 데이터베이스 작업 추적
- SQLite 데이터베이스로 모든 전사 작업 자동 추적
- 중복 작업 방지 (이미 전사된 경우 확인 프롬프트)
- 저장 필드: ID, URL, 제목, 엔진, 상태, 요약, 타임스탬프

### 재생목록 처리
- YouTube 재생목록 자동 감지
- 전체 재생목록 일괄 처리 옵션
- 처리 전 사용자 확인 (20초 타임아웃)

### 파일 덮어쓰기 보호
- 기존 파일 존재 시 덮어쓰기 확인 프롬프트
- 20초 타임아웃 후 기본 동작 수행
- `--force` 옵션으로 프롬프트 생략

## 사용 예시

```sh
# 기본 전사 (요약과 상세 출력 포함)
python trans.py "https://www.youtube.com/watch?v=VIDEO_ID"

# YouTube API로 빠른 전사 (타임스탬프 포함)
python trans.py "https://youtu.be/VIDEO_ID" --engine youtube --timestamp

# whisper.cpp로 로컬 전사 (요약 없이)
python trans.py "URL" --engine whisper-local --no-summary

# 비디오 다운로드 + SRT 자막 생성
python trans.py "URL" --video --srt

# 재생목록 전체 처리
python trans.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# 스트리밍 없이 진행 표시줄로 전사
python trans.py "URL" --no-stream

# 강제 재전사 (타임스탬프 포함)
python trans.py "URL" --force --timestamp --engine whisper-api
```

## 환경 변수 설정

기본 옵션을 환경 변수로 설정할 수 있습니다:

```bash
# 기본값 설정 예시
export YT_TRANS_ENGINE="youtube-transcript-api"  # 기본 엔진
export YT_TRANS_STREAM="true"                    # 스트리밍 출력 (true/false)
export YT_TRANS_DOWNLOADS="true"                 # Downloads 폴더 저장 (true/false)
export YT_TRANS_SUMMARY="true"                   # AI 요약 생성 (true/false)
export YT_TRANS_VERBOSE="true"                   # 상세 요약 (true/false)
export YT_TRANS_TIMESTAMP="false"                # 타임스탬프 포함 (true/false)
export YT_TRANS_AUDIO="false"                    # 오디오 보관 (true/false)
export YT_TRANS_VIDEO="false"                    # 비디오 다운로드 (true/false)
export YT_TRANS_SRT="false"                      # SRT 생성 (true/false)
export YT_TRANS_TRANSLATE="false"                # 한국어 번역 (true/false)
```

`.bashrc` 또는 `.zshrc`에 추가하여 영구적으로 설정할 수 있습니다.

## 필수 요구사항

- Python 3.8+
- OpenAI API 키 (`.env` 파일에 설정)
- whisper.cpp (로컬 전사 시)
- ffmpeg (미디어 처리용)

# 추가

타임코드
전사 진행상황 표시 
파일명

python trans.py "https://youtu.be/xiMdnDsgycg?si=2g4arM4KTAUIDNuH" --stream --summary

1. 전사 파일명을 영상 id가 아니라 제목으로
2. id는 영상에서 추출한 영상 id
3. no-stream 옵션 시 전사 진행상황 progress bar 표시
4. 타임코드 추가

모듈성 강화



python trans.py "https://youtu.be/YujDNH_hSx4?si=O8RP6CbB5Y7WRhGc" --engine whisper-cpp --timestamp --no-stream --force  