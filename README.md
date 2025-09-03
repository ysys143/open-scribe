# Open-Scribe v2.0

YouTube 비디오를 다양한 엔진으로 전사하고 요약하는 모듈화된 오픈소스 CLI 도구입니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: modular](https://img.shields.io/badge/code%20style-modular-green.svg)](https://github.com/open-scribe/open-scribe)

## 설치

1. 필요한 패키지 설치:
```sh
pip install -r requirements.txt
```

2. 환경 변수 설정:
```sh
cp .env.example .env
# .env 파일을 편집하여 OpenAI API 키 입력
```

3. Scribe 명령어 등록 (선택사항):
```sh
# 터미널에서 바로 사용 가능하도록 설정
source scribe.zsh
```

## 사용법

### 새로운 모듈화 구조 (권장)
```sh
python main.py [url] [options]
```

### Scribe 명령어 사용
```sh
scribe [url] [options]
```

### 기존 스크립트 (호환성 유지)
```sh
python trans.py [url] [options]
```

> **참고**: `scribe` 명령어는 Oh My Zsh에 자동 등록되어 있어 터미널에서 바로 사용할 수 있습니다.

### 전사 엔진 옵션

`--engine` 또는 `-e` 옵션으로 선택 (기본값: gpt-4o-mini-transcribe)

* `gpt-4o-transcribe` (별칭: `high`) - OpenAI GPT-4o 고품질
* `gpt-4o-mini-transcribe` (별칭: `medium`) - OpenAI GPT-4o-mini 중간품질 (기본값)
* `whisper-api` (별칭: `whisper-cloud`) - OpenAI Whisper API
* `whisper-cpp` (별칭: `whisper-local`) - whisper.cpp 로컬 실행
* `youtube-transcript-api` (별칭: `youtube`) - YouTube 자막 API

### 주요 옵션

* `--stream` / `--no-stream` - 실시간 출력 여부 (기본: True)
* `--downloads` / `--no-downloads` - Downloads 폴더 저장 여부 (기본: True)
* `--summary` - AI 요약 생성 (GPT-4o-mini 사용)
* `--verbose` - 상세 요약 출력
* `--audio` - 오디오 파일 보관
* `--video` - 비디오 다운로드
* `--srt` - SRT 자막 파일 생성
* `--translate` - 한국어로 번역
* `--force` / `-f` - 기존 파일 덮어쓰기, 재전사 강제 실행
* `--help` - 도움말 표시
* `--progress` - 전사 진행상황 표시 (퍼센트 및 ETA)
* `--timestamp` - 전사 결과에 타임코드 포함
* `--filename NAME` - 저장 파일명 지정 (기본: 영상 제목 기반 자동 생성)
* `--parallel N` / `-p N` - 재생목록 병렬 처리 (N개 워커 사용)

## 동작 방식

### YouTube Transcript API 엔진 선택 시

* YouTube 자막 데이터를 직접 가져옴
* 오디오 다운로드 불필요
* 가장 빠른 처리 속도

### 다른 엔진 선택 시

* `yt-dlp` Python 라이브러리로 오디오 자동 다운로드 (subprocess 대신 직접 API 사용)
* 선택한 엔진으로 오디오 파일 전사
* 25MB 초과 파일 자동 압축 (OpenAI API 제한 대응)
* 실시간 다운로드 및 전사 진행률 표시 (`--progress` 옵션)
* 워커 수 동적 계산으로 시스템 리소스 최적 활용

### 파일 저장 위치

기본 경로 (환경 변수로 변경 가능):
* 전사 결과: `~/Documents/open-scribe/transcript/`
* 오디오 파일: `~/Documents/open-scribe/audio/`
* 비디오 파일: `~/Documents/open-scribe/video/`
* Downloads 폴더 복사본: `~/Downloads/` (옵션)
* 데이터베이스: `~/Documents/open-scribe/transcription_jobs.db`

환경 변수로 경로 설정:
```bash
export OPEN_SCRIBE_BASE_PATH=~/my-transcripts  # 기본 경로 변경
export OPEN_SCRIBE_AUDIO_PATH=~/my-audio       # 오디오 경로 변경
export OPEN_SCRIBE_TRANSCRIPT_PATH=~/my-texts  # 전사 경로 변경
```

### AI 요약 기능

* GPT-4o-mini를 사용한 한국어 요약
* 간단 요약 (기본): 3줄 이내 핵심 요약
* 상세 요약 (`--verbose`):

  1. 3줄 이내 핵심 요약
  2. 시간대별 내용 정리 (타임코드 포함)
  3. 상세 분석 및 비판적 의견

## 고급 기능

### 비디오 및 자막 처리

* `--video`: 비디오 파일 다운로드
* `--srt`: SRT 자막 파일 생성 (타임코드 포함)
* `--translate`: 한국어로 번역 (영어 콘텐츠의 경우)

### 데이터베이스 작업 추적

* SQLite 데이터베이스로 모든 전사 작업 자동 추적
* 중복 작업 방지 (이미 전사된 경우 확인 프롬프트)
* 저장 필드: ID, URL, 제목, 엔진, 상태, 요약, 타임스탬프

### 재생목록 처리

* YouTube 재생목록 자동 감지
* 전체 재생목록 일괄 처리 옵션
* 병렬 처리 지원 (`--parallel N` 옵션)
* 처리 전 사용자 확인 (20초 타임아웃)
* 성공/실패 통계 표시

### 파일 덮어쓰기 보호

* 기존 파일 존재 시 덮어쓰기 확인 프롬프트
* 20초 타임아웃 후 기본 동작 수행
* `--force` 옵션으로 프롬프트 생략

## 사용 예시

### Scribe 명령어 사용
```sh
# 기본 전사 (YouTube 자막 API)
scribe "https://www.youtube.com/watch?v=VIDEO_ID" --engine youtube

# whisper.cpp로 로컬 전사 + 요약 + 타임코드
scribe "https://youtu.be/VIDEO_ID" --engine whisper-local --summary --timestamp

# 비디오 다운로드 + SRT 자막 생성 + 진행상황 표시
scribe "URL" --video --srt --progress

# 재생목록 전체 처리
scribe "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# 재생목록 병렬 처리 (4개 워커)
scribe "https://www.youtube.com/playlist?list=PLAYLIST_ID" --parallel 4

# 강제 재전사 + 파일명 지정
scribe "URL" --force --engine whisper-api --filename my_video
```

### Python 스크립트 직접 실행
```sh
# 모듈화된 v2.0 구조 사용 (권장)
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --engine youtube-transcript-api
python main.py "https://youtu.be/VIDEO_ID" --engine whisper-cpp --summary --timestamp

# 레거시 스크립트 (호환성 유지)
python trans.py "https://www.youtube.com/watch?v=VIDEO_ID" --engine youtube
python trans.py "https://youtu.be/VIDEO_ID" --engine whisper-local --summary --timestamp
```

## 환경 변수 설정

### 필수 설정
```bash
OPENAI_API_KEY=your_api_key_here  # OpenAI API 키 (GPT-4o, Whisper API 사용 시)
```

### OpenAI 모델 설정 (선택사항)
```bash
# 최신 모델 사용 (2025년 기준)
OPENAI_SUMMARY_MODEL=gpt-5-mini      # 요약 생성 모델
OPENAI_CORRECT_MODEL=gpt-5-mini      # 자막 교정 모델  
OPENAI_TRANSLATE_MODEL=gpt-5-mini    # 번역 모델
OPENAI_SUMMARY_LANGUAGE=auto         # 요약 언어 자동 감지
OPENAI_TRANSLATE_LANGUAGE=Korean     # 번역 대상 언어
```

### 경로 설정 (선택사항)
```bash
# 기본 경로 설정
OPEN_SCRIBE_BASE_PATH=~/Documents/open-scribe

# 개별 경로 설정
OPEN_SCRIBE_AUDIO_PATH=~/Documents/open-scribe/audio
OPEN_SCRIBE_VIDEO_PATH=~/Documents/open-scribe/video
OPEN_SCRIBE_TRANSCRIPT_PATH=~/Documents/open-scribe/transcript
OPEN_SCRIBE_DOWNLOADS_PATH=~/Downloads
OPEN_SCRIBE_DB_PATH=~/Documents/open-scribe/transcription_jobs.db

# Whisper.cpp 설정 (로컬 전사 시)
WHISPER_CPP_MODEL=~/whisper.cpp/models/ggml-base.bin
WHISPER_CPP_EXECUTABLE=~/whisper.cpp/build/bin/whisper-cli
```

### 기본 옵션 설정 (선택사항)
```bash
# 전사 엔진 및 동작 설정
OPEN_SCRIBE_ENGINE=youtube-transcript-api   # 기본 전사 엔진
OPEN_SCRIBE_STREAM=true                     # 스트리밍 출력
OPEN_SCRIBE_DOWNLOADS=true                  # Downloads 폴더 저장
OPEN_SCRIBE_SUMMARY=true                    # AI 요약 생성
OPEN_SCRIBE_VERBOSE=true                    # 상세 요약
OPEN_SCRIBE_TIMESTAMP=false                 # 타임스탬프 포함

# 병렬 처리 설정
MIN_WORKER=1                               # 최소 워커 수
MAX_WORKER=5                               # 최대 워커 수 (시스템 리소스 기반 자동 계산)
```

## 필수 요구사항

* Python 3.8+
* OpenAI API 키 (`.env` 파일에 설정)
* whisper.cpp (로컬 전사 시)
* ffmpeg (미디어 처리용)

### Scribe 명령어 설치 (선택사항)
```bash
# Oh My Zsh에 자동 등록 (권장)
source scribe.zsh

# 또는 수동으로 등록
cp scribe.zsh ~/.oh-my-zsh/custom/
echo 'source ~/.oh-my-zsh/custom/scribe.zsh' >> ~/.zshrc
```

### 플랫폼 호환성

* **macOS/Linux**: 완전 지원
* **Windows**: 지원 (타임아웃 기능이 다르게 동작할 수 있음)

## 프로젝트 구조

### 모듈화된 아키텍처 (v2.0)
```
open-scribe/
├── main.py                 # 메인 진입점
├── src/                    # 핵심 모듈
│   ├── cli.py             # CLI 인터페이스
│   ├── config.py          # 설정 관리
│   ├── database.py        # SQLite 데이터베이스
│   ├── downloader.py      # YouTube 다운로드
│   ├── transcribers/      # 전사 엔진 모듈
│   │   ├── base.py       # 추상 기본 클래스
│   │   ├── openai.py     # OpenAI/Whisper API
│   │   ├── whisper_cpp.py # whisper.cpp 로컬
│   │   └── youtube_api.py # YouTube 자막 API
│   ├── processors/        # 후처리 모듈
│   │   ├── summary.py    # AI 요약 생성
│   │   └── subtitle.py   # SRT 자막 생성
│   └── utils/             # 유틸리티 함수
│       ├── audio.py      # 오디오 처리/압축
│       ├── file.py       # 파일 작업
│       ├── progress.py   # 진행률 표시
│       └── validators.py # URL 검증
├── trans.py               # 레거시 스크립트 (호환성)
└── docs/                  # 문서
```

### 핵심 적용 기술 및 기법

#### 🏗️ 아키텍처 패턴
- **추상 팩토리 패턴**: `BaseTranscriber` 추상 클래스로 전사 엔진 통합 인터페이스 제공
- **전략 패턴**: 런타임에 전사 엔진 동적 선택 (`openai.py`, `youtube.py`, `whisper_cpp.py`)
- **모듈화 설계**: 단일 책임 원칙에 따른 계층별 분리 (`src/` 디렉토리 구조)

#### 🚀 성능 최적화
- **동적 워커 계산**: `WorkerCalculator`가 시스템 리소스 기반으로 최적 병렬 워커 수 자동 계산
- **청크 기반 병렬 처리**: `worker_pool.py`로 대용량 오디오 파일 분할 처리
- **스마트 오디오 압축**: `audio.py`에서 25MB 초과 시 점진적 비트레이트 감소 (64k→24k)
- **메모리 효율 스트리밍**: 실시간 전사 결과 출력으로 메모리 사용량 최소화

#### 🛡️ 안정성 및 복원력
- **자동 폴백 시스템**: `fallback.py`로 엔진 실패 시 다른 엔진으로 자동 전환
- **재시도 로직**: 네트워크 오류 시 지수 백오프 재시도 패턴
- **상태 추적**: SQLite 기반 작업 상태 영속화 (`database.py`)
- **파일 검증**: 다운로드 후 파일 무결성 및 크기 검증

#### 📊 모니터링 및 진단
- **실시간 진행률**: `progress.py`에서 퍼센트, ETA, 처리 속도 표시
- **시스템 리소스 모니터링**: `psutil` 기반 CPU/메모리 사용량 추적
- **처리 시간 메트릭**: 각 단계별 소요 시간 측정 및 최적화 가이드
- **에러 분류**: 네트워크/API/파일 오류별 세분화된 예외 처리

#### 🔧 환경 적응성
- **환경 변수 기반 설정**: `config.py`에서 12가지 환경 변수 지원
- **다중 플랫폼 호환**: macOS/Linux/Windows 크로스 플랫폼 지원
- **동적 경로 관리**: 사용자 환경에 따른 자동 경로 설정
- **API 모델 동적 선택**: GPT-5, GPT-5-mini 등 최신 모델 지원

#### 🌐 국제화 및 번역
- **언어 자동 감지**: 콘텐츠 언어 자동 판별 후 번역 여부 결정
- **다단계 번역 파이프라인**: `translator.py`에서 원문→한국어 고품질 번역
- **자막 형식 변환**: `srt_converter.py`로 다양한 자막 형식 지원
- **타임코드 동기화**: 번역 시 원본 타임스탬프 유지

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여

Open-Scribe는 오픈소스 프로젝트입니다. 기여를 환영합니다!

## 문의

프로젝트 관련 문의사항은 이슈 트래커를 이용해 주세요.
