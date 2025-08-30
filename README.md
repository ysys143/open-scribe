# Open-Scribe

YouTube 비디오를 다양한 엔진으로 전사하고 요약하는 오픈소스 CLI 도구입니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

## 동작 방식

### YouTube Transcript API 엔진 선택 시

* YouTube 자막 데이터를 직접 가져옴
* 오디오 다운로드 불필요
* 가장 빠른 처리 속도

### 다른 엔진 선택 시

* yt-dlp Python 라이브러리로 오디오 자동 다운로드
* 선택한 엔진으로 오디오 파일 전사
* 실시간 다운로드 및 전사 진행률 표시 (`--progress` 옵션)

### 파일 저장 위치

* 전사 결과: `~/Documents/GitHub/yt-trans/transcript/`
* 오디오 파일: `~/Documents/GitHub/yt-trans/audio/`
* 비디오 파일: `~/Documents/GitHub/yt-trans/video/`
* Downloads 폴더 복사본: `~/Downloads/` (옵션)
* 사용자 지정 파일명: `--filename` 옵션으로 변경 가능

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
* 처리 전 사용자 확인 (20초 타임아웃)

### 파일 덮어쓰기 보호

* 기존 파일 존재 시 덮어쓰기 확인 프롬프트
* 20초 타임아웃 후 기본 동작 수행
* `--force` 옵션으로 프롬프트 생략

## 사용 예시

```sh
# 기본 전사 (YouTube 자막 API)
python trans.py "https://www.youtube.com/watch?v=VIDEO_ID" --engine youtube

# whisper.cpp로 로컬 전사 + 요약 + 타임코드
python trans.py "https://youtu.be/VIDEO_ID" --engine whisper-local --summary --timestamp

# 비디오 다운로드 + SRT 자막 생성 + 진행상황 표시
python trans.py "URL" --video --srt --progress

# 재생목록 전체 처리
python trans.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# 강제 재전사 + 파일명 지정
python trans.py "URL" --force --engine whisper-api --filename my_video
```

## 필수 요구사항

* Python 3.8+
* OpenAI API 키 (`.env` 파일에 설정)
* whisper.cpp (로컬 전사 시)
* ffmpeg (미디어 처리용)

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여

Open-Scribe는 오픈소스 프로젝트입니다. 기여를 환영합니다!

## 문의

프로젝트 관련 문의사항은 이슈 트래커를 이용해 주세요.
