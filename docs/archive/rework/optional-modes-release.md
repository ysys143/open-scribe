# 선택 모드 릴리스·실검증 — 담당 F

## 현재 상태 — FINAL_READY 최종 설치·마지막 probe, 2026-11-06 KST

671개 검사 동결 코드로 양쪽 설치를 완료했다. 마지막 ASR 1회는 7.0526875초 범위의 자원 qualification을 통과했다. CORRECT 1회는 stale telemetry로 중단돼 자격을 얻지 못했으며, 조건부 helper flow와 전체 로컬 E2E는 전제 미충족으로 defer다. 추가 추론·재시도 없이 종료했다. 아래 표가 최신 상태이며 뒤의 표는 날짜별 이전 단계의 원본 기록이다.

| 구분 | 최신 결과 |
| --- | --- |
| 코드 동결 | D 671 tests/146.201s 표본, 110개 aggregate `b084f1f757fdf3f1a5283313f8183eabda93483adb9c786e1d3c9dbf48ae4247`; F 전후 byte 변경 0. A 지정 세 파일 해시 일치 |
| 양쪽 설치 | upgrade exit 0, 각각 설치 대상 68개 파일 byte 일치. 양쪽 이번 dependency 추가·버전 변경 0 |
| 설치 CLI | 양쪽 각각 기본 off·미준비 fail-safe·cloud diarization·speaker names·unsupported 거절 5경로 통과. 모의 HTTP만 사용 |
| 설정·기본 모델 | 양쪽 active settings·RC·Git index·HEAD byte 지문 유지. 기존 ASR/요약 모델 그대로, 선택 기능 5개 모두 off |
| 모델 보존 | MacBook 기존 ASR/correction 파일 목록·크기·mtime 불변. Mac mini 로컬 그룹·모델 없음 유지 |
| CORRECT 마지막 1회 | 정상 pressure·가용 14,913,470,464바이트에서 시작. 10.3625초 후 stale telemetry로 exit 1. 자격 0, 이번 prompt/generated/decoder JSON 형태·의미 검토는 미판정 |
| CORRECT 실패 원인 관측 | sample age 3.902398초 > 기존 max_age 3초. 실패 시 pressure normal·가용 15,353,790,464바이트. stale은 확인, GIL 원인은 미확정. 결과/raw는 관측되지 않음 |
| ASR 마지막 1회 | 정상 pressure·가용 13,700,988,928바이트에서 시작, exit 0. 새 evidence `af17f6a1342d4ea99a9ef90d062dd21e` 1개, qualified audio 7.0526875초 |
| 수락된 ASR peak | host 1,109,377,024바이트, accelerator 1,527,556,552바이트. 3 GiB qualification/4 GiB stop 이내, final sample age 0.456435초 |
| 현재 qualification | 새 private root: ASR 1·CORRECT 0. 이전 실패 root: evidence 0 그대로. 성공 prompt qualification 없음 |
| helper flow/E2E | CORRECT 자격 부재로 조건부 pending-relisten helper flow 미실행. 전체 ASR+LLM E2E defer. ASR 자격도 해당 7.0526875초·버전·옵션만 유효 |
| 과금 | 이번 추가 유료 POST 0. 이전 실제 API 3회/재개 추가 0 유지. 공유 원장 89건·USD 0.165969878158062·unknown 0 불변 |
| 자원·정확도 경계 | helper 1/CPU 2/free 8 GiB/qual 3 GiB/stop 4 GiB/timeout/offline/기존 telemetry grace 유지. 형식 adapter 코드 검증을 실제 내용 정답·CER·이름 정확도로 승격하지 않음 |
| repo 변경 | F 제품 코드 수정 0, 보고서만 갱신. 과거 실패·655/662/671 지문·기존 백업은 보존 |

최신 private state: `/Users/jaesolshin/.local/state/open-scribe/release-validation/20261105T171644Z-final-02a96c/`. 마지막 절에 새 evidence·telemetry·raw 부재 진단과 최신 backup/rollback을 기록했다.

## 이력 4 요약 — 이전 READY_FULL, 2026-11-06 01:16 KST 이후

양쪽 소프트웨어 런타임 업데이트와 설치 CLI 검증, 짧은 실제 API 3호출을 완료했다. 로컬 qualification은 ASR·교정 모두 실패했으므로 로컬 재청취 E2E 통과나 전체 기능 완료를 선언하지 않는다. 아래 현재 표가 최신 상태이며, 뒤의 preflight·PREP_READY 표는 날짜별 과거 관측이다.

| 구분 | 현재 결과 |
| --- | --- |
| 동결 코드 | D 범위 110개 SHA-256 대조 변경 0; manifest `4ce8b3d0c5bcc8dc2348a49526112a83631baa61c08d71d7caea7ab5ff9e198b` |
| MacBook 설치 | upgrade 성공, 설치된 bundle 68개 파일 byte 일치; 기존 122개 distribution 버전 변경 0, `mlx-lm==0.32.2`만 추가 |
| Mac mini 설치 | BatchMode SSH upgrade 성공, 설치된 bundle 68개 파일 byte 일치; 기존 core dependency 변경 0, 로컬 group·모델 추가 0 |
| 설치 CLI 검증 | 양쪽 각각 5경로: default off, relisten 미준비, standalone cloud diarization, speaker names, unsupported 설정 거절. 실제 외부 API 없이 완료 |
| 활성 설정 | 양쪽 기존 `settings.json` byte 불변, ASR·요약 모델 선택 유지. alignment·diarization·embedding·relisten·speaker_names 전부 off; 새 필드는 기본 merge만 |
| 모델 준비 | MacBook 기존 ASR + 새 correction artifact 준비. correction 11개/351,386,061바이트 무결성 검증 완료. Mac mini 모델 준비 없음 |
| ASR qualification | 7.0526875초 영문 합성 음성, 2회 시도. telemetry/자원 검증 중단, 성공 evidence 0. 실제 ASR+LLM E2E는 defer |
| correction qualification | 실제 디코더 1회 실행, prompt 576·생성 194·상한 512토큰·finish stop. JSON 검증 실패로 자격 거절. 성공 evidence 0 |
| A 원인진단 인계 | 아래 증거 경로·예외·보존 한계를 기록. 생성 raw JSON은 F가 보존하지 못해 원인 미확정; 추가 추론 중지, 실패/defer 유지 |
| 실제 음성 API | 28초 Whisper Turbo ASR 1회 + Scribe standalone diarization 1회. 원문·단어 시간·입력 byte 불변, 단어 화자 unknown 13개 보존; 재개/격리 캐시 실행 추가 호출·과금 0 |
| 합성 영상 이름 API | 사람 없는 명찰 영상 + 명시적 synthetic labeled transcript, LLM 1회. 이름 후보 1개는 suggested·confirmed=false; registry·named 변동 0. 실제 개인 영상 검증 아님 |
| 실제 과금 | 총 3 POST, 이번 USD 0.002014951111110802. 공유 scope validation 누계 USD 0.165969878158062, unknown 0·quarantine 0, ceiling USD 10 |
| 보존 | 양쪽 설정·RC·Git index·HEAD 불변, 원격 repo clean 유지. F의 repo 쓰기는 이 보고서뿐이며 제품 코드 수정 0 |
| 남은 미완 | 로컬 성공 qualification/재청취 E2E, 모호한 실제 단어 화자. CER·사람 검증 정확도·새 default·전체 60분 검증을 주장하지 않음 |

현재 영수증·자체 스크립트는 repo 밖 `/Users/jaesolshin/.local/state/open-scribe/release-validation/20261105T161653Z-cbf6fe3b/`에 있다. READY_FULL 실행 상세·실측 한계·비용·원복 경로는 문서 마지막 실행 단계에 기록한다.

## 이력 1 — 최초 읽기 전용 preflight, 2026-11-06 00:31 KST

최초 preflight 상태: `prepared/probe_only`. 읽기 전용 사전 조사는 완료했으며 설치·릴리스·최종 smoke·모델 실측은 수행하지 않았다. 이 기록은 READY 또는 릴리스 통과 판정이 아니다.

관측 시각: 2026-11-06 KST, 본 프로브 종료 시각 00:31:38~40. A~D의 공유 작업본은 구현 진행 중인 시점 표본이다. 설치와 최종 smoke는 사용자가 정한 메인 READY 신호 후 추가 위임 대상이며, 이번 턴에서는 대기 폴링하지 않는다.

### 적용한 지시와 변경 경계

- 읽은 스킬: `.agents/skills/install-open-scribe/SKILL.md`, `/Users/jaesolshin/.agents/skills/machine-sync/SKILL.md`.
- 구형 설치 스킬의 전역 비밀 저장소 생성, 키 `.env` 복사·캐시, 셸 source, 개인 경로 `wrapperSource`는 적용하지 않았다. 사용자 지시인 앱 하나의 `settings.json`, process env 키만, 기본 API only·로컬 off가 우선한다.
- 배포 대상은 특정 실행 런타임이다. 프로젝트 Git·대화·프로필 이관을 수행하지 않았고 대상 저장소를 변경하지 않았다.
- 담당 F의 쓰기는 이 보고서 하나다. 소스·Git index·설정·설치본·키·모델·다른 세션을 변경하지 않았다. 패키지 설치, 모델 다운로드·파일 내용 읽기, 개인 오디오 전송, API 호출, 메시지, 커밋·push도 실행하지 않았다.
- 환경 전체나 프로세스 argv는 조회하지 않았다. 인증 변수는 명시한 이름의 프로브 프로세스 내 존재 개수만 관측했으며 키 파일은 읽지 않았다.

### 두 머신의 경로와 코드 상태

두 머신의 계정 홈은 `/Users/jaesolshin`이며 Darwin arm64다.

| 항목 | 소스 MacBook | 대상 Mac mini |
| --- | --- | --- |
| 관측 hostname | `Jaesolui-MacBookPro.local` | `Jaesolui-Macmini.local` |
| SSH 별칭 | 현재 머신 | `jaesol-macmini` |
| 명령 | `/Users/jaesolshin/.local/bin/scribe` | 동일 경로 |
| 명령이 가리키는 설치 코드 | `/Users/jaesolshin/.local/lib/open-scribe` | 동일 경로 |
| 설치 Python | 위 경로의 `.venv/bin/python` | 동일 상대 경로 |
| 선택된 설정 경로 | `/Users/jaesolshin/.config/open-scribe/settings.json` 존재 | 동일 경로 존재 |
| 데이터 디렉터리 후보 | `/Users/jaesolshin/.local/share/open-scribe` 존재, 실행 코드 아님 | 동일 |
| 프로젝트 | `/Users/jaesolshin/Documents/GitHub/open-scribe` | 동일 경로 |
| 프로젝트 HEAD | `3880fcfe007965711cb89a2f4778db09d2918bfd` | 동일 |
| 프로젝트 작업 트리 | 공유 구현의 기존 미커밋 변경 있음 | 최종 전체 porcelain 출력 빈 문자열: clean |
| 프로젝트 venv | 존재, Python 3.12.11 | 없음 |

대상은 최초 프로브의 추적 파일 검사에 이어 `git --no-optional-locks status --porcelain=v1` 전체 조회도 실행했고 출력이 비어 있었다. 대상 Git 상태는 사용자에게 전달받은 clean 상태와 일치했다.

두 설치본의 `main.py`, `scribe.sh`, `src/core/settings.py`, `src/core/credentials.py`, `src/core/application.py`는 관측한 파일별 SHA-256이 양쪽에서 각각 일치했다. 현재 공유 작업본과는 settings/application이 다르다. 두 설치본 모두 `src/core/relisten.py`, `src/core/cloud_diarization.py`, `src/core/speaker_names.py`가 없다. 따라서 현재 설치본이 이번 선택 모드 구현을 포함한다고 볼 수 없다.

| 파일 | 양쪽 설치본 SHA-256 | 소스 작업본 SHA-256 |
| --- | --- | --- |
| `src/core/settings.py` | `7f7bc26cc39b0a6d8f3d736455ab0314dfa619ca2c4dfb3844c89e74a8bfc931` | `f5280995a0b15bb1686a87c1972e8a9399420bcefbc3d1e6545e7cc58afc9155` |
| `src/core/application.py` | `905eae4f81c0b5d67bfd3c2ddd25ef0ef7aad3be9217e2372de3349bb986c0ab` | `841574e3e8e09bbe2e217464368858d0f54e7cacebef2f33714a02ea09c92c82` |

위 해시는 관측 시점의 표본이며 구현 진행 중인 소스의 최종 해시가 아니다.

設定 경로는 프로브에 전달된 환경에서 `OPEN_SCRIBE_SETTINGS`·XDG 경로 override가 없을 때의 선택 결과다. 실행 중인 다른 프로세스의 `--config`·환경·동작 상태는 조사하지 않았다. `.zshrc`에서 설치 디렉터리 등록 경로를 확인했지만 셸 파일을 source하지 않았다. `aliases.zsh`에서 발견된 구형 `.env` 경로는 주석이었고 활성 scribe 행은 0개였다.

두 명령 래퍼와 설치본 `scribe.sh`·`credentials.py`의 정적 검사에서는 `.env` 및 개인 키 파일 참조가 없었다. 대상의 구형 Git 저장소 안 `scribe.sh`에는 `.env` 참조가 있으므로 현재 별도 설치본과 혼동하면 안 된다. 해당 구형 래퍼는 실행하지 않았다.

### 실행 도구와 의존성 metadata

아래 버전은 해당 실행 파일의 `--version` 또는 `-version` 출력이다. 외부 모델 카탈로그의 지원 여부나 품질 판정이 아니다.

| 도구 | MacBook | Mac mini |
| --- | --- | --- |
| PATH의 `python3` | `/opt/homebrew/bin/python3`, 3.15.2 | `/usr/bin/python3`, 3.9.6 |
| `python3.12` | `/opt/homebrew/bin/python3.12`, 3.12.10 | `/Users/jaesolshin/.local/bin/python3.12`, 3.12.3 |
| `python3.13` | `/opt/homebrew/bin/python3.13`, 3.13.7 | `/Users/jaesolshin/.local/bin/python3.13`, 3.13.2 |
| `uv` | `/Users/jaesolshin/.local/bin/uv`, 0.11.21 | 동일 경로, 0.11.21 |
| `ffmpeg` | `/opt/homebrew/bin/ffmpeg`, 8.1.2 | `/opt/homebrew/bin/ffmpeg`, 9.0.1 |
| `ffprobe` | `/opt/homebrew/bin/ffprobe`, 8.1.2 | `/opt/homebrew/bin/ffprobe`, 9.0.1 |
| `deno` | `/opt/homebrew/bin/deno`, 2.6.4 | `/opt/homebrew/bin/deno`, 2.9.6 |
| 설치본 Python | 3.12.10 | 3.12.3 |

Mac mini의 비대화형 SSH PATH에서는 `shutil.which('ffmpeg')`와 `shutil.which('ffprobe')`가 모두 `None`이었다. 절대 경로로는 두 도구가 exit 0으로 실행됐다. 후속 설치 실행 환경에서는 `/opt/homebrew/bin` 경로가 필요하다. 현재 셸이나 설정을 수정하지 않았다. PATH 기본 Python에 의존하지 않고 이미 존재하는 CPython 3.12 경로를 지정할 수 있다.

`importlib.metadata.version()`만 사용했으며 ML 모듈을 import하거나 추론하지 않았다.

| distribution | MacBook 설치 venv | Mac mini 설치 venv | MacBook 프로젝트 venv |
| --- | --- | --- | --- |
| `mlx` | 0.32.4 | 없음 | 없음 |
| `mlx-audio` | 0.6.4 | 없음 | 없음 |
| `mlx-lm` | 없음 | 없음 | 없음 |
| `transformers` | 5.22.1 | 없음 | 없음 |
| `torch` | 2.15.0 | 없음 | 없음 |
| `pyannote-audio` | 4.0.7 | 없음 | 없음 |
| `speechbrain` | 1.1.2 | 없음 | 없음 |
| `requests` | 2.34.2 | 2.34.2 | 2.32.5 |
| `psutil` | 7.0.0 | 7.0.0 | 7.0.0 |

현재 소스의 `requirements.local.in`과 `requirements.local.txt`에는 `mlx-lm==0.32.2` 항목이 존재한다. 이는 의존성 선언 관측이며 설치·호환성·모델 실측 통과를 의미하지 않는다. 로컬 lock의 대상은 CPython 3.12/macOS arm64다.

### 설정의 API only·로컬 off 상태

현재 두 `settings.json`의 허용된 stage 필드만 선별 출력했다. 나머지 설정 및 자격 값은 출력하지 않았다.

| 단계 | 양쪽 설정의 enabled | provider | 관측 의미 |
| --- | --- | --- | --- |
| `asr` | true | `auto` | 원격 전사 선택 |
| `summary` | true | `auto` | 원격 요약 선택 |
| `alignment` | false | `mlx` | 로컬 정렬 off |
| `diarization` | false | `pyannote` | 로컬 화자 분리 off |
| `embedding` | false | `speechbrain` | 로컬 임베딩 off |
| `translate` | false | `auto` | off |
| `correct` | false | `auto` | off |
| `relisten` | 양쪽 파일·설치 defaults에 항목 없음 | 소스 defaults는 `mlx` | 소스 defaults의 enabled=false; 설치본 미구현 |
| `speaker_names` | 양쪽 파일·설치 defaults에 항목 없음 | 소스 defaults는 `auto` | 소스 defaults의 enabled=false; 설치본 미구현 |

설정에 저장된 모델 문자열은 양쪽 모두 ASR `nvidia/nemotron-3.5-transcribe`, 요약·번역·교정 `openai/gpt-6-luna`였다. 이 이름의 현재 공급자 제공 여부를 조회하거나 API를 호출하지 않았다.

소스 `defaults()`를 AST로 읽은 결과 `alignment`, `diarization`, `embedding`, `relisten`, `speaker_names`는 모두 false였다. `Settings.load()`의 코드상 파일 선택은 명시 경로/`OPEN_SCRIBE_SETTINGS`/XDG 기본 경로 순이고, 누락 stage는 내장 기본값으로 합친다. 실제 통합 경로 실행 검증은 이번 preflight에 포함되지 않았다.

명시한 인증 변수 5개(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, `NOTION_API_KEY`)는 로컬 비로그인 프로브 및 대상 SSH 프로브 환경에서 각각 존재 개수가 모두 0이었다. 이는 이 프로브 환경만의 결과다. 로그인 셸·다른 앱 프로세스의 인증 상태나 키 정본 부재를 의미하지 않으며, 실제 API 인증은 미검증이다.

### 준비 모델 디렉터리 관측

모델은 디렉터리 이름·존재와 파일 존재만 조사했다. 모델 파일 byte 내용·해시·개인 오디오는 읽거나 전송하지 않았다. HF cache도 디렉터리 항목만 조회했다.

MacBook의 `/Users/jaesolshin/.local/share/open-scribe/models`에 다음 5개 디렉터리가 존재했다.

- `qwen3-asr-0.6b-4bit`
- `qwen3-forced-aligner-0.6b-4bit`
- `pyannote-community-1`
- `speechbrain-ecapa-voxceleb`
- `whisper-large-v3-turbo-4bit`

MacBook 설정의 alignment·diarization·embedding 모델 경로는 위 대응 디렉터리를 가리키며 존재했다. 이들 기능은 모두 off다. Mac mini 설정의 해당 모델 경로는 null이고, 앱 모델 루트 `~/.local/share/open-scribe/models`, `~/.cache/open-scribe/models`, `~/.open-scribe/models`도 없었다.

텍스트 LLM의 `llm_model_dir`는 현재 두 설정 파일에 없다. 확인한 앱 모델 루트와 기본 HF hub snapshot 목록에서는 준비된 텍스트 생성 LLM 디렉터리를 찾지 못했다. 이 조회는 머신 전체 모델 검색이 아니며, Qwen ASR·forced aligner 또는 이미지 text encoder 이름을 텍스트 LLM 준비 근거로 세지 않았다.

판정: 두 머신 모두 재청취용 텍스트 LLM 준비와 `mlx-lm` 설치를 확인하지 못했다. 모델 실측은 0회, 정확도·메모리 qualification도 이번 턴에서 0회다. 모델 실측 통과로 보고할 근거가 없다.

### 확인한 런타임 배포 방식

현재 `scripts/install.sh`는 코드 복사 allowlist와 `src`·`bot`의 Python 소스를 별도 staging 런타임에 복사하며, Git·대화·키·사용자 데이터·모델을 복사하지 않는다. 기본 코드는 `~/.local/lib/open-scribe`, 명령은 `~/.local/bin/scribe`다. 기존 설치 교체는 `--upgrade`를 사용하고 이전 런타임·명령을 백업하며 실패 시 복원하는 구조다.

설치기의 `--settings FILE`은 기존 설정을 검증하며 다시 쓰지 않는다. `--init-settings`·`--migrate-settings`·`--register-shell`은 별도 명시 옵션이다. 실제 설치기는 실행하지 않았다. 구형 설치 스킬과 Makefile의 `.env` 설명을 활성 설정 계약으로 사용하지 않았다.

의존성 경로는 core 기본 설치, `--with-local-deps` 로컬 lock 설치, `--skip-deps --venv DIR` 기존 venv 읽기 전용 참조로 나뉜다. 현재 스크립트는 일반 upgrade 시 이전 venv의 local distribution metadata를 검사해 감지된 로컬 그룹을 보존한다. MacBook 설치본에는 기존 로컬 그룹이 있고 Mac mini는 core metadata만 관측됐다. 기존 venv에 없는 `mlx-lm`을 `--skip-deps`가 보충해 주지는 않는다.

대상 저장소의 clean HEAD 코드를 이번 구현의 배포 원본으로 간주하지 않는다. 이번 조사는 배포 payload를 만들거나 전송하지 않았다. READY 후 추가 위임에서는 공유 구현의 확정 표본을 기준으로 런타임 배포와 최종 smoke를 구분해 기록해야 한다.

### 증거와 미실행 항목

주요 실행·출력은 다음과 같다. 모두 읽기 전용이며 Python 프로브에는 `-I -B`를 사용했다.

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 jaesol-macmini 'hostname; id -un; printf "home=%s\n" "$HOME"'
exit 0
Jaesolui-Macmini.local
jaesolshin
home=/Users/jaesolshin

git rev-parse HEAD
3880fcfe007965711cb89a2f4778db09d2918bfd

대상 Python subprocess:
git -C /Users/jaesolshin/Documents/GitHub/open-scribe rev-parse HEAD
exit 0: 3880fcfe007965711cb89a2f4778db09d2918bfd
git -C /Users/jaesolshin/Documents/GitHub/open-scribe --no-optional-locks status --porcelain=v1 --untracked-files=no
exit 0: output=""
최종 대상 전체 상태:
git -C /Users/jaesolshin/Documents/GitHub/open-scribe --no-optional-locks status --porcelain=v1
exit 0: output=""

양쪽 설치 .venv/bin/python -I -B -c <importlib.metadata 전용 프로브>
exit 0; mlx-lm: null (PackageNotFoundError)

대상 /opt/homebrew/bin/ffmpeg -version
exit 0: ffmpeg version 9.0.1
대상 shutil.which('ffmpeg') / shutil.which('ffprobe')
None / None
```

초기 파일 목록/문서 읽기 명령은 존재하지 않는 `pyproject.toml` 때문에 각각 exit 2/1을 반환했다. 이후 설치·의존성 근거는 실제 존재하는 `scripts/install.sh`·`requirements*.txt/in`에서 읽었다. 두 머신의 본 프로브와 추가 프로브는 모두 exit 0이었다. 앞선 도구 조합 코드 한 번은 JS template 문법 오류로 실행 전에 실패했고, 고친 후 프로브가 실행됐다.

| 검증 항목 | 이번 상태 |
| --- | --- |
| 두 머신 SSH·경로·도구 존재/버전 | 관측 완료 |
| 현재 설정/API only·로컬 off | 파일·소스 AST 관측 완료 |
| MLX LM metadata·텍스트 LLM 디렉터리 | metadata 부재, 조회 범위 내 준비 디렉터리 미발견 |
| 새 선택 모드 통합 테스트 | 미실행, A~D 구현 진행 표본 |
| E 독립 review 결과 확인 | 미실행 |
| 런타임 설치·교체·전송 | 미실행, 사용자 지정 READY 후 추가 위임 단계 |
| 설치 후 최종 smoke | 전제 미충족: 이번 설치를 실행하지 않음 |
| 유료 API·실인증·모델 추론/qualification | 미실행 |

이 기록의 완료 범위는 읽기 전용 preflight와 보고서 작성이다. 설치·최종 smoke·실측은 미완이며 이번 기록에서 통과로 표시하지 않았다.

## 이력 2 — 공개 후보·ASR metadata 추가 조사, 2026-11-06 00:44 KST

상태는 계속 `prepared/probe_only`다. 2026-11-06 KST 추가 지시에 따라 공개 카탈로그·config·라이선스와 기존 ASR 준비 메타데이터만 읽었다. READY 신호를 받지 않았으며 설치·가중치 다운로드·추론·qualification은 실행하지 않았다. 이번 쓰기도 이 보고서 하나다. 공개 JSON·문서는 메모리에서 읽었고 모델 파일로 저장하지 않았다.

### 공개 후보의 식별·revision·gating·라이선스

후보 [mlx-community/Qwen3-0.6B-4bit](https://huggingface.co/mlx-community/Qwen3-0.6B-4bit)는 실제 HF 카탈로그에 존재한다. 인증 헤더 없이 공개 API가 HTTP 200을 반환했으며 `private=false`, `gated=false`, `disabled=false`, `pipeline_tag=text-generation`, `library_name=mlx`였다. 카탈로그 관측 시각은 2026-11-06 00:44:42 KST다. [카탈로그 API 및 파일 metadata](https://huggingface.co/api/models/mlx-community/Qwen3-0.6B-4bit?blobs=true)

- 고정 revision: `73e3e38d981303bc594367cd910ea6eb48349da8`.
- 카탈로그 `lastModified`: `2025-04-28T21:26:13.000Z`.
- 모델 카드의 라이선스 표기: `apache-2.0`. 해당 revision의 README는 원본 Qwen LICENSE로 연결하며, 그 링크의 본문도 Apache License Version 2.0임을 확인했다. 파생 저장소 자체의 11개 파일에는 별도 `LICENSE` 파일이 없다. [고정 README](https://huggingface.co/mlx-community/Qwen3-0.6B-4bit/blob/73e3e38d981303bc594367cd910ea6eb48349da8/README.md), [카드가 가리키는 LICENSE](https://huggingface.co/Qwen/Qwen3-0.6B/blob/main/LICENSE)

### 파일 합계와 A의 admission 조건

HF API의 `siblings[].size` 전수 합계이며 크기 누락은 0개다. 가중치의 LFS pointer 크기가 아닌 실물 크기를 합산했다. 아래는 원격 metadata이며 가중치를 내려받아 검증한 결과가 아니다. [파일 metadata](https://huggingface.co/api/models/mlx-community/Qwen3-0.6B-4bit?blobs=true)

| 파일 | 바이트 |
| --- | ---: |
| `.gitattributes` | 1,570 |
| `README.md` | 873 |
| `added_tokens.json` | 707 |
| `config.json` | 937 |
| `merges.txt` | 1,671,853 |
| `model.safetensors` | 335,450,584 |
| `model.safetensors.index.json` | 49,731 |
| `special_tokens_map.json` | 613 |
| `tokenizer.json` | 11,422,654 |
| `tokenizer_config.json` | 9,706 |
| `vocab.json` | 2,776,833 |
| 전체 11개 합계 | 351,386,061 |

전체 약 0.327254 GiB로 사용자 조건인 3 GiB 이하이며, 현재 `inspect_model(..., task='correct')`의 더 엄격한 전체 bundle 1 GiB 제한에도 metadata상 들어간다. 후속 다운로드가 별도로 지시되더라도 실제 로컬 bundle의 캐시 부수 파일을 포함한 stat 합계를 다시 검사해야 한다. 모델 메모리 사용량이 0.327254 GiB라는 뜻은 아니다.

공개 LFS metadata가 제시한 `model.safetensors` SHA-256은 `392e8d466d56100ada00eb82031fb854297fc9e389b7d303eba3af114e87bce2`다. 로컬 바이트와 비교하지 않았다. index의 `metadata.total_size=335372288`은 전체 repository 크기와 다르므로 bundle 합계로 쓰지 않았다. [고정 weight index metadata](https://huggingface.co/mlx-community/Qwen3-0.6B-4bit/blob/73e3e38d981303bc594367cd910ea6eb48349da8/model.safetensors.index.json)

### 공개 config와 A 검사 코드의 대조

고정 revision의 `config.json`·`tokenizer_config.json`은 인증 없이 HTTP 200으로 읽었다. config는 937바이트이고 아래 값은 `src/core/resources.py`의 소형 dense correction 조건과 일치한다. [고정 config](https://huggingface.co/mlx-community/Qwen3-0.6B-4bit/blob/73e3e38d981303bc594367cd910ea6eb48349da8/config.json)

| 필드 | 관측값 |
| --- | --- |
| `model_type` | `qwen3` |
| `architectures` | `["Qwen3ForCausalLM"]` |
| `hidden_size` / `intermediate_size` | 1024 / 3072 |
| `num_hidden_layers` | 28 |
| `num_attention_heads` / `num_key_value_heads` | 16 / 8 |
| `head_dim` / `vocab_size` | 128 / 151936 |
| `tie_word_embeddings` | true |
| `quantization` / `quantization_config` | 각각 `bits=4`, `group_size=64` |
| quantization `mode` | 양쪽 생략; A 검사는 생략 시 `affine`로 판정 |
| `num_experts`, `num_local_experts`, `model_file` | 모두 없음 |

tokenizer config는 9,706바이트이며 `Qwen2Tokenizer`, chat template 존재, `enable_thinking` 분기 존재, `auto_map` 없음으로 관측됐다. 따라서 A 어댑터의 `enable_thinking=False` 전달과 metadata가 맞는다. tokenizer 자체를 로드하거나 prompt를 생성하지 않았다. [고정 tokenizer config](https://huggingface.co/mlx-community/Qwen3-0.6B-4bit/blob/73e3e38d981303bc594367cd910ea6eb48349da8/tokenizer_config.json)

현 소스에서 AST로 추출한 순수 metadata 함수 `_check_model_metadata`와 `_dimensions`를 공개 config에 적용했다. architecture·700M 상한 metadata 검사 및 tokenizer config metadata 검사는 예외 없이 끝났고 `dimensions_match=true`, 금지된 최상위 필드는 빈 목록이었다. 이는 config metadata 적합성 근거다. correction용 전체 `inspect_model()`은 safetensors header 바이트를 읽으므로 실행하지 않았다. 실제 tensor header/shape, strict MLX-LM load, tokenizer 초기화, 메모리·timeout, 생성 JSON 품질과 qualification은 모두 미검증이다.

`requirements.local.txt`에서 `mlx-lm==0.32.2`와 SHA-256 hash 2개를 확인했다. 기존 pin 변경 0·새 library 추가는 사용자가 전달한 A의 결과이며, 이번 추가 조사는 이전 lock 전수와의 차이를 독립 검증하지 않았다. 설치 venv의 변경도 없다.

### 기존 로컬 ASR 준비 metadata

대상 경로는 MacBook의 `/Users/jaesolshin/.local/share/open-scribe/models/qwen3-asr-0.6b-4bit` 하나로 제한했다. 다른 모델·키·대화는 추가 조사하지 않았다.

- 디렉터리 존재, 일반 파일 30개. 다운로드 캐시 metadata·0바이트 lock 파일을 포함한 전체 stat 합계는 712,781,254바이트(약 0.664 GiB), 디렉터리 symlink 0개다.
- `model.safetensors`는 708,236,945바이트로 존재한다. stat만 확인했고 파일을 열지 않았다.
- `config.json`, `model.safetensors.index.json`, `tokenizer_config.json`, `vocab.json`, `merges.txt`, `preprocessor_config.json`, `chat_template.json`은 모두 크기 0보다 큰 파일로 존재했다.
- config의 `model_type=qwen3_asr`, `architectures=["Qwen3ASRForConditionalGeneration"]`, 양쪽 quantization의 `bits=4`, `group_size=64`, `mode=affine`를 확인했다.
- 현 A 코드의 순수 metadata 함수 `_asr_profile(path, 'asr', 'qwen-0.6', config)`가 `qwen-0.6`을 반환했다. 전체 Helper·ML 모듈·모델 fingerprint·실제 ASR은 실행하지 않았다.
- 기존 HF `config.json.metadata` 영수증의 revision은 `313d850181767edf09f00a9c289becca70e58cd0`였다. config 영수증만의 기록이며 bundle 전체 또는 weight revision 일치를 입증하지 않는다.

판정은 기존 ASR의 준비 경로·파일 존재·native config 적합성까지다. 가중치 무결성·runtime load·재청취 정확도·실측 qualification 통과를 뜻하지 않는다.

### READY 이후 최종 검증 계획 — 아직 미실행

아래는 사용자가 지정한 후속 검증 계획을 보존한 것이다. 현재 실행 권한으로 해석하지 않는다. 모델 가중치 다운로드는 READY 후에도 별도 지시 여부를 결정하는 항목이다.

| 순서 | 검증 경로 | 결과에서 확인할 것 | 현재 상태 |
| --- | --- | --- | --- |
| 1 | 지정 API 2조합, 기존 28초 표본으로 실제 2호출 | 원문 불변, 두 조합의 실제 경로·응답 근거, 공유 원장 반영 | 미실행 |
| 2 | 로컬 모델 미준비 fail-safe 실제 경로; 가능하면 준비 모델 자격 후 영문 합성 재청취+LLM | 미준비 시 API 원문 보존·명시적 unavailable, 준비 시 자격·자원 실측과 ASR/LLM 실제 실행을 구분 | 미실행, 텍스트 LLM 미준비 |
| 3 | 사람이 없는 합성 명찰 영상으로 네임 API 양방향 wire | 후보는 미검증 유지, registry 불변; 실제 CSNL은 video 없음으로 미상 유지 | 미실행 |

새 권한으로 실행하는 모든 유료 호출은 공유 원장 `/tmp/open-scribe-rework-validation/transcription_jobs.db`, scope `validation`, ceiling USD 10을 함께 사용한다. 사용자 전달 현재 합계 약 USD 0.164·unknown 0은 참고값이며 이번 추가 조사에서 원장을 조회하거나 재정산하지 않았다. API 2호출과 네임 검증 호출을 별도 예산으로 나누지 않는다.

추가 조사 결론: 지정 공개 후보는 실제 존재하며 config·파일 metadata 기준으로 A의 작은 correction 모델 후보 조건에 맞는다. 설치·가중치 확보·모델 실측·유료 검증은 수행하지 않았고 상태는 `prepared/probe_only`로 유지했다.

## 이력 3 — PREP_READY 가중치 준비, 2026-11-06 01:09 KST

사용자가 PREP_READY로 허용한 것은 MacBook의 공개 correction 모델 가중치 준비와 무결성 검증이다. 이 단계에서 코드 설치·모델 로드·qualification·설정 활성화·추론은 허용되지 않았다. 그 경계를 유지하고 아래 artifact 준비만 완료했다.

| 항목 | 결과 |
| --- | --- |
| 준비 상태 | `weight_ready` — artifact 무결성에만 해당 |
| HF repo | `mlx-community/Qwen3-0.6B-4bit` |
| 고정 revision | `73e3e38d981303bc594367cd910ea6eb48349da8` |
| 새 모델 디렉터리 | `/Users/jaesolshin/.local/share/open-scribe/models/qwen3-0.6b-correct-4bit` |
| 기존 파일 보존 | 시작 전 디렉터리 부재 확인, 새 디렉터리 생성, 모든 파일 `xb` 배타 생성; 기존 모델·파일 덮어쓰기 없음 |
| 카탈로그 재확인 | 해당 revision API의 repo·SHA·public·ungated·Apache-2.0·11개 파일/크기/공개 digest 일치 확인 |
| 전송 | 인증 없는 Python stdlib HTTP GET, 8 MiB chunk 스트리밍, credential provider 미사용·환경 proxy 비활성 |
| 공개 digest 검증 | LFS SHA-256 2개 + Git blob SHA-1 9개 = 11개 성공 |
| 저장 파일 재검증 | 파일 11개를 디스크에서 8 MiB씩 다시 읽은 SHA-256이 전송 시 계산값과 모두 일치 |
| 최종 파일 수·합계 | 11개, 351,386,061바이트 |
| 모델 디렉터리 내부 추가 파일 | 없음; receipt는 외부에 저장 |
| 실행 종료 | 다운로드·검증 프로세스 exit 0 |

외부 상태 receipt: `/Users/jaesolshin/.local/state/open-scribe/model-preparation/20261105T160939Z-683618d726e4.json`. 권한은 `0600`이며 파일별 예상 크기·공개 digest·실측 SHA-256·저장 파일 검증 여부·고정 revision·준비 상태를 기록했다. signed redirect URL이나 인증 값은 receipt·출력에 기록하지 않았다. HF/API 키·키 파일·전체 환경은 읽지 않았다.

실행 출력과 독립 receipt/stat 조회 근거:

```text
CATALOG_VERIFIED anonymous revision=73e3e38d981303bc594367cd910ea6eb48349da8 files=11 bytes=351386061
WEIGHT_READY files=11 bytes=351386061 published_digest_verified=11 saved_file_sha256_verified=11
NO_MODEL_LOAD NO_QUALIFICATION NO_INFERENCE NO_SETTINGS_CHANGE NO_RUNTIME_INSTALL
exit 0

receipt: status=weight_ready, verified_file_count=11, verified_total_bytes=351386061
all_files_verified=true, lfs_sha256_count=2, git_blob_sha1_count=9
on_disk_file_count=11, on_disk_total_bytes=351386061
model_loaded=false, qualification_run=false, inference_run=false
settings_activated=false, runtime_installed=false, remote_machine_modified=false
```

Mac mini에는 접속·모델 전송·준비를 하지 않았다. 기존 ASR 모델과 개인 설정도 변경하지 않았다. `mlx-lm` 설치나 모델 `inspect_model`·로드를 실행하지 않았으므로 실제 런타임 호환성·품질·자원 qualification은 여전히 미실측이다. 앞 절의 텍스트 모델 미준비 상태는 당시 관측 기록이며, 이번에 바뀐 것은 위 correction artifact의 디스크 준비 상태뿐이다.

최종 검증 계획 2단계의 현재 상태는 다음과 같이 갱신한다: correction artifact 준비 완료, 모델 미준비 fail-safe 실경로·실제 ASR+LLM·자격 측정은 모두 미실행. 최종 코드 설치와 real 검증은 E 최종 PASS·D 전체 동결 뒤 별도 READY까지 수행하지 않는다.

후속 real 검증에서도 기존 global mutex, CPU 2 threads, 최소 가용 메모리 8 GiB, qualification peak 3 GiB, stop ceiling 4 GiB를 그대로 유지한다. macOS cold telemetry 실패를 우회하거나 상한을 늘리지 않는다. 모델 부재·GIL·메모리 조건으로 defer되면 해당 경로는 미실측으로 기록한다. 이 준비 결과는 E PASS·설치 smoke·추론 통과를 대신하지 않는다.

가중치 준비 후 작업을 종료했으며 READY 대기 폴링은 하지 않았다.

## 실행 4 — READY_FULL 설치·실검증, 2026-11-06 01:16 KST 이후

이 단계는 READY_FULL의 명시적 추가 위임에 따라 실행했다. E 최종 독립 PASS·57 focused 및 D 전체 655 tests/147.256s 통과는 사용자 확인 사항이며, D 문서에서도 최종 전체 검사 출력과 동결 지문을 읽었다. F가 655개 검사를 다시 실행했다고 주장하지 않는다. F는 설치된 실제 코드의 별도 CLI·API·모델 경로를 확인했다. 제품 소스 결함을 수정하거나 동결을 해제하지 않았다.

### 동결 지문과 배포 경계

설치 전에 `source-freeze.json`에 110개 파일의 지문을 기록했다. F의 최초 목록은 Makefile 포함·Dockerfile 제외여서 aggregate가 `ee293f720d56322c599469ccd084b4d22f83dcdacf770fc47d8e4ddbe6cc9951`이었다. D 문서의 정확한 범위로 목록을 맞춘 `d-freeze.json`은 110개, aggregate `4ce8b3d0c5bcc8dc2348a49526112a83631baa61c08d71d7caea7ab5ff9e198b`로 D 최종 지문과 일치했다. 이는 목록 차이의 보정이며 소스 수정이 아니다. 최종 재대조에서 해당 110개 파일의 변경은 0개였다.

runtime source bundle은 69개 파일이다. 이 중 installer 자체를 제외하고 실제 설치 대상 68개 파일을 양쪽에서 byte SHA-256으로 대조해 차이 0개였다. 전송은 source allowlist의 실행 코드·requirements·기존 실행 문서·installer만 포함했다. `.git`·index·키·settings·모델·대화·프로필을 전송하지 않았다. 대상의 구형 repo 코드를 배포 원본으로 쓰지 않고 외부 private state에 bundle을 풀어 설치했다.

### 설치 명령과 결과

MacBook에서 실제 실행한 명령:

```sh
bash scripts/install.sh --upgrade --python /opt/homebrew/bin/python3.12 \
  --settings /Users/jaesolshin/.config/open-scribe/settings.json
```

Mac mini는 BatchMode SSH에서 `PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"`을 명시하고, 외부 staging의 `runtime-source/scripts/install.sh --upgrade --python "$HOME/.local/bin/python3.12" --settings "$HOME/.config/open-scribe/settings.json"`를 실행했다. 두 설치 프로세스는 모두 exit 0이며 설치기 자체 config validate·CLI smoke·relocated launcher 확인을 통과했다.

| 검증 항목 | MacBook | Mac mini |
| --- | --- | --- |
| 현재 코드 | `~/.local/lib/open-scribe` | 동일 |
| 현재 명령 | `~/.local/bin/scribe` | 동일 |
| 설치 source byte 비교 | 68개, 불일치 0 | 68개, 불일치 0 |
| 의존성 delta | 기존 122개 버전 변경 0, mlx-lm 0.32.2 하나 추가 → 123개 | 새 distribution 0·기존 버전 변경 0 |
| 로컬 선택 dependency | 기존 그룹 유지, mlx-lm 준비 | mlx·mlx-audio·mlx-lm·torch 모두 없음 |
| models 디렉터리 | 기존 ASR·새 correction 준비 유지 | 없음, 모델 복사 0 |
| 활성 settings/RC/index/HEAD | 전부 기존 지문 일치 | 전부 기존 지문 일치 |
| repo 상태 | 사용자 공유 작업 상태 보존 | clean 보존 |
| 기본 선택 기능 | alignment/diarization/embedding/relisten/speaker_names 모두 false | 동일 |

`--register-shell`, 설정 생성/변환 옵션, key wrapper, `.env` 복사, 비밀 경로 하드코드를 추가하지 않았다. 새로운 stage 필드는 Settings의 기본 merge로만 노출된다. 기존 ASR·요약 모델 선택은 바꾸지 않았다.

### 설치 CLI 경로와 fail-safe

`installed-smoke.py`는 설치본의 `main.py` CLI entry를 실행하고 HTTP transport만 모의 API로 교체했다. 실제 provider 파싱·budget·Application·SQLite·export를 사용했다. 양쪽 각각 아래 5경로를 통과했다. private test settings만 사용했고 실제 외부 API 호출은 0회다.

| 경로 | exit·관측 |
| --- | --- |
| 기본 off | exit 0, ASR 모의 POST 1개, 선택 기능 5개 false |
| relisten 모델 미준비 | exit 2/partial, 실제 fail-safe `unavailable`, API 원문 보존, 로컬 추론 0 |
| standalone cloud diarization | exit 0, ASR 1 + 화자 1 모의 POST, 원문·단어 시간 보존 |
| speaker names | exit 0, ASR 1 + 이름 1 모의 POST, 원문·단어 시간 보존 |
| unsupported provider 설정 | exit 1, POST 0, DB 생성 0, 설정 byte 불변 |

첫 모의 이름 smoke는 검증 스크립트의 과도한 fixture 단가 때문에 예산 guard에서 실패했다. fixture 단가만 수정한 두 번째 private smoke 표본에서 위 결과를 얻었으며 제품 코드는 고치지 않았다. source CLI와 설치 CLI를 혼용해 성공으로 세지 않았다.

### 실제 로컬 qualification: 실행했으나 자격 미획득

공개 설치 CLI `scribe --config <private qualification-settings.json> doctor --qualify ...`를 사용했다. 활성 settings는 바꾸지 않았고, ASR 요청에는 `--relisten --backend qwen-0.6`을 명시했다. primary API ASR의 모델·설정은 그대로다. 선택 stage가 off여도 doctor가 명시적으로 probe settings에서만 준비 모델을 선택하는 경로를 실행했다.

공통 입력은 기존 영문 합성 음성 `~/.local/share/open-scribe/qualification-audio/align-probe.wav`, 실측 7.0526875초다. correction items는 original/candidate 각각 220 English words로 준비했다. 옵션은 max_tokens 512·max_input_tokens 4096·언어 en이며, ASR에는 기본 decoding/chunking과 max_tokens 512가 적용됐다.

전역 helper mutex·helper 1·CPU 2 threads·free 최소 8 GiB·qualification peak 3 GiB·stop 4 GiB·timeout 120초·offline·부모 사망 watchdog을 그대로 사용했다. cap·telemetry grace를 완화하거나 가짜 qualification을 넣지 않았다. 완료 후 helpers 폴더 0개·global mutex 재획득 가능을 확인했다.

| task/모델 | 실행 결과 | 실측·증거 한계 |
| --- | --- | --- |
| ASR `qwen3-asr-0.6b-4bit`, mlx/qwen-0.6 | 1차 exit 1: `local helper telemetry unavailable` | 성공 결과·qualification 없음 |
| 같은 ASR, 허용된 bounded 재실행 1회 | exit 1, 약 2.497초: `local helper stopped: memory pressure or telemetry unavailable` | 외부 capture에는 helper RSS 47,300,608·accelerator 0의 초기 sample 1개만 있음. 실제 lifetime peak나 정확한 pressure/GIL 원인을 확정하지 않음 |
| correction `qwen3-0.6b-correct-4bit`, mlx-lm | 실제 모델 로드·디코더 실행 후 exit 1, 약 10.654초: `local correction probe incomplete: decoder or JSON validation failed` | prompt 576·생성 194·max 512·finish stop·parse_error true·needs_review. 토큰 상한 도달 아님 |

교정의 final helper telemetry에서 host peak 844,283,904바이트, accelerator peak 703,171,108바이트를 관측했다. 이 값은 실제 helper 관측이며, 수락된 qualification record의 peak가 아니다. Parent의 전체 process-tree peak가 별도로 수락됐다고 주장하지 않는다. JSON 검증 실패로 evidence가 생성되지 않았으므로 `qualified_audio_seconds`, `qualified_prompt_tokens`, 성공 evidence ID는 모두 없다. ASR·교정 합쳐 qualification JSON 0개이며 로컬 재청취+LLM 성공 E2E는 defer다.

실행 runtime metadata는 mlx 0.32.4, mlx-audio 0.6.4, mlx-lm 0.32.2, transformers 5.22.1, tokenizers 0.23.3, huggingface-hub 2.4.0, sentencepiece 0.2.2였다. 설치 소스·package metadata 기준 ASR runtime fingerprint는 `49e07010c76aea72936e1a538c5179cddeecc3f681bdedf84e6025f271915140`, correction은 `06386407096aaae1cc56d1288f4a3bafd1ee259f7ac062b8d516c3f5b5e8f103`이다. 실패 출력을 자격 통과나 정확도 근거로 확대하지 않는다.

### 실제 짧은 API·재개·과금

키는 `apikey-env` 스킬의 one-shot zsh source/export 경로로 해당 검증 프로세스에만 전달했다. OPENROUTER_API_KEY만 export했고 값을 출력·argv 전달·프로젝트/private settings 파일 저장하지 않았다. wire 기록에는 인증 헤더를 저장하지 않았다.

공유 DB `/tmp/open-scribe-rework-validation/transcription_jobs.db`, scope validation·ceiling USD 10을 사용했다. private GuardedStore는 각 새 예약을 SQLite transaction에서 기존 미정산 0·quarantine 0 확인 후 생성했고, 설치본 Router가 실제 응답 receipt를 저장·정산했다. source Store는 수정하지 않았다. POST 직전에는 자기 예약만 미정산 1건인지 확인했다. 불명확 과금이 생기면 이후 호출을 멈추는 guard를 유지했다.

| 실제 POST | 모델 | 예약 USD | 정산 USD | reservation ID |
| --- | --- | ---: | ---: | --- |
| 1 | `openai/whisper-large-v3-turbo` | 0.000389 | 0.00009324 | `a7504210d7c94e5ebe0ad8761457d970` |
| 2 | `elevenlabs/scribe-v2` | 0.002139 | 0.0017111111111108 | `c8cceb59d9984a1db0131431e417ed7c` |
| 3 | `openai/gpt-6-luna` speaker names | 0.019824 | 0.0002106 | `9c03282b333349e1bf349b1d9a3b51b7` |

1·2번 입력은 기존 boundary.wav의 28초 한 구간이다. 별도 local model 추론은 자격 부재로 막혔고 API 전사·화자 결과는 보존했다. original combined와 final의 본문·segment ID·텍스트·단어 시간, 입력 파일 SHA-256이 같았다. 화자 모호성으로 단어 13개는 unknown이며 결과는 partial이다. 실제 단어 화자를 정답이라고 판정하거나 CER·사람 정확도·새 default를 선정하지 않았다.

동일 작업 재개 후 실제 POST 증가 0·공유 원장 변화 0이었다. 최초 private harness에 활성 설정의 Notion flag가 따라와 `Notion is not configured` 오류도 기록됐지만 Notion 외부 전송은 없었다. 해당 옵션을 private settings에서만 off로 고친 별도 cache-only 작업은 새 예약 자체를 금지한 Store로 실행했다. ASR·화자 캐시가 재사용됐고 추가 POST·과금 0, 남은 오류는 local unavailable·화자 alignment 모호성뿐이었다. 활성 settings나 원래 job snapshot을 고치지 않았다.

원장 시작은 86건·USD 0.1639549270469512·unknown 0이었다. 종료는 89건·USD 0.165969878158062·unknown 0·quarantine 0이며 이번 비용은 USD 0.002014951111110802다. 모델 카탈로그 GET과 모의 요청을 유료 POST 수에 포함하지 않았다. 전체 60분 호출은 없었다.

### 사람 없는 합성 영상의 이름 API 입출력

명찰은 640×360 텍스트 이미지 `Jordan Lee`만 렌더링해 기존 ffmpeg로 8초 영상화했다. 기존 ffmpeg에 drawtext filter가 없어 첫 생성은 실패했으며, 이미 설치된 Pillow로 글자를 그린 뒤 ffmpeg loop encode로 준비했다. 새로운 패키지·모델은 설치하지 않았다. 합성 영상에는 사람·얼굴·개인 원음 영상이 없다.

installed Application의 speaker_names 통합과 실제 Router.speaker_names를 사용했다. ASR 부분만 명시적 synthetic speaker-labeled transcript fixture로 공급했으며 실제 ASR 추가 호출은 없었다. 개인 영상이나 CSNL 원음 영상을 업로드하지 않았다. 프레임 추출은 기존 CPU 2·width 최대 720 경로를 그대로 사용했고 실제 이름 wire에는 JPEG 프레임 1개, base64 6,792바이트와 json_schema가 전달됐다. 요청/응답은 private `real/wire-3.json`, `real/response-3.json`에 보존했다.

실제 응답에서 synthetic-A → Jordan Lee 후보 1개가 생성됐다. 근거는 합성 전사의 자기소개 segment quote였으며 후보는 `suggested`, `confirmed=false`, `verification=requires_review`다. 합성 영상 명찰과 프레임 전송 경로는 확인했지만, 프레임에서 실제 인물과 화자를 식별했다고 주장하지 않는다. 결과의 근거가 segment였으므로 영상 기반 이름 정확도 실증도 아니다. 실제 CSNL에는 제공된 video가 없으므로 이름 미상 상태를 유지한다.

공유 DB의 people_v3·decisions_v3·embeddings_v3 전체 row hash와 검증 root/기존 사용자 jobs의 named 파일 hash는 전후 동일했다. 영구 registry 등록·confirm·voice enrollment는 실행하지 않았다.

### 영수증과 원복

동일한 run ID `20261105T161653Z-cbf6fe3b`의 외부 state를 양쪽에 남겼다. 주요 파일은 `d-freeze.json`, `bundle-manifest.json`, `installation-verification.json`, `installed-smoke-result.json`, `qualify-*-status.json`, `qualify-*-telemetry.jsonl`, `real-validation-result.json`, `paid-cost-summary.json`, `final-source-verification.json`이다. telemetry·real API 파일은 MacBook에만 있다. receipt·자체 스크립트는 모두 repo 밖이며 제품 소스는 수정하지 않았다.

| 대상 | 이전 runtime backup | 이전 command backup |
| --- | --- | --- |
| MacBook | `~/.local/lib/open-scribe.backup-YE3u0I` | `~/.local/bin/scribe.backup-YE3u0I` |
| Mac mini | `~/.local/lib/open-scribe.backup-eVOpfa` | `~/.local/bin/scribe.backup-eVOpfa` |

원복은 실행하지 않았다. 실행 중인 작업이 없는 상태에서 현재 runtime을 외부 state의 새 경로로 보존하고, 해당 backup을 원래 경로로 돌린 뒤 command backup을 복원하면 된다. 데이터·설정·모델·repo·대화는 대상이 아니다. 아래는 MacBook의 구체적 순서이며 Mac mini에서는 backup suffix만 `eVOpfa`로 바꾼다.

```sh
test ! -e "$HOME/.local/state/open-scribe/release-validation/20261105T161653Z-cbf6fe3b/rollback-current-runtime" && \
  mv "$HOME/.local/lib/open-scribe" "$HOME/.local/state/open-scribe/release-validation/20261105T161653Z-cbf6fe3b/rollback-current-runtime" && \
mv "$HOME/.local/lib/open-scribe.backup-YE3u0I" "$HOME/.local/lib/open-scribe" && \
cp -p "$HOME/.local/bin/scribe.backup-YE3u0I" "$HOME/.local/bin/scribe"
```

현재 판정은 양쪽 runtime 설치·기본 off·모의 5경로·짧은 실제 API 3호출·과금/보존 검증 완료다. 로컬 자격과 실제 ASR+LLM E2E, 모호한 화자 판정은 미완으로 남긴다. 기존 자원 상한·실패 시 defer를 유지했고, 별도 계정·키·서비스 배포·메시지 발송·commit/push는 없었다.

### A 원인진단 인계 — 기존 증거만 확인, 추가 추론 중지

사용자가 correction 원인진단을 A에 위임한 뒤, F는 기존 private state와 설치 소스만 읽었다. 추가 모델 실행·API 호출은 0회다. 구조화된 증거 안내는 repo 밖 `~/.local/state/open-scribe/release-validation/20261105T161653Z-cbf6fe3b/diagnostic-handoff.json`에 기록했다. 아래 경로의 기준 디렉터리는 모두 `/Users/jaesolshin/.local/state/open-scribe/release-validation/20261105T161653Z-cbf6fe3b/`다.

| A가 확인할 파일 | 확정된 관측 |
| --- | --- |
| `qualify-correct-1-status.json`, `qualify-correct-1.err` | exit 1, 약 10.654초. `RuntimeError: local correction probe incomplete: decoder or JSON validation failed` |
| `qualify-correct-1-telemetry.jsonl` | request 1개, memory 10개, result metadata 1개. 마지막 result capture의 원래 helper folder ID는 `35b10fd754e74b49bc7471b8c95ed280` |
| `correct-items.json`, `qualification-settings.json` | 합성 qualifier 입력과 실제 옵션. 키 값 없음. active settings가 아님 |
| `qualify-asr-1.err` | `RuntimeError: local helper telemetry unavailable`; 1차는 외부 telemetry capture 없음 |
| `qualify-asr-2-status.json`, `qualify-asr-2.err` | exit 1, 약 2.497초. `RuntimeError: local helper stopped: memory pressure or telemetry unavailable` |
| `qualify-asr-2-telemetry.jsonl` | request 1개·초기 memory 1개뿐. helper folder ID `a81cce873ba04751912ea14038ecae92`, host 47,300,608바이트·accelerator 0; 실패 순간 pressure/free-memory·final sample 없음 |
| `d-freeze.json`, `bundle-manifest.json` | 검증한 코드 지문. 실행한 구현은 `~/.local/lib/open-scribe/src/core/local.py`와 `resources.py` |
| `paid-cost-summary.json`, `real-validation-result.json` | 실제 API 3호출 정산·unknown 0의 기존 증거; 수정하지 않음 |

보존된 correction 결과 JSON은 아래 metadata capture까지다. 생성된 실패 응답 원문 JSON 자체가 아니다.

```json
{
  "metadata": {
    "finish_reason": "stop",
    "generation_tokens": 194,
    "max_tokens": 512,
    "prompt_tokens": 576,
    "parse_error": true,
    "quality_status": "needs_review",
    "hit_token_limit": false
  },
  "keys": ["corrections", "raw_text", "metadata"]
}
```

F의 외부 monitor가 `result.json`에서 metadata와 key 이름만 복사해 `raw_text` 내용·corrections 본문 보존을 빠뜨렸다. 원래 helper `result.json`은 기존 `_run()` cleanup으로 삭제됐고, 현재 helper folder와 qualification evidence는 모두 0개다. 기존 파일에서 구체적인 실패 생성 JSON을 복원할 수 없다. `local.correct()`가 ValueError/TypeError를 `parse_error=true`로 바꾸며 내부 예외 메시지도 남기지 않으므로 JSON 문법·schema·중복 key·ID 불일치 중 어느 원인인지 확정하지 않는다. 성공으로 고치거나 실패 원문을 추정해 재구성하지 않았다.

ASR도 최상위 예외 두 가지와 위 초기 sample만 확정할 수 있다. cold telemetry·GIL·pressure·가용 메모리 중 정확한 중단 원인은 기존 capture로 구분되지 않는다. 이 증거 한계는 correction 원인진단과 ASR 중단 원인 분석에 영향을 주며, 실제 API 3호출 receipt·정산과 실패/defer 판정을 바꾸지 않는다. A가 코드 계약 불일치를 확인하면 해당 owner 수정·새 동결·재설치 여부를 메인에서 판단할 사안으로 남긴다. F는 추가 추론을 중지한 상태다.

## 실행 5 — FINAL_READY 마지막 설치·bounded probe, 2026-11-06 02:16 KST 이후

### 새 동결과 양쪽 runtime

사용자가 D 671 tests/146.201s·source 110 전후 변경 0 및 E focused 48+independent 22 PASS를 확인한 FINAL_READY에 따라 실행했다. D의 전체 검사 문서와 aggregate를 읽고 F가 설치 전에 동일 범위 110개 파일을 별도 `source-freeze.json`에 기록했다. aggregate는 `b084f1f757fdf3f1a5283313f8183eabda93483adb9c786e1d3c9dbf48ae4247`로 일치했고, 설치·실측 뒤에도 변경 0개였다. 671개 전체 검사를 다시 실행하거나 가격을 조회하지 않았다.

| A 최종 제품 파일 | 실제 설치 표본 SHA-256 |
| --- | --- |
| `src/core/local.py` | `841483129557b20124e0e374b8eee501f3536c2237d4b1e8f98bee3ebbb4fe66` |
| `src/core/resources.py` | `d343fc0af939afc3bd5eee74fd16ab0baa2bc0897ff53bb901e7e2c050a7d14b` |
| `src/core/relisten.py` | `d015f719563bdf3d0708fd2a0198b9815af9ff84456c6720c31e0bfef4fd1a00` |

동일한 software bundle 69개를 사용했고 설치기 자체를 제외한 68개 파일은 양쪽 설치본에서 byte SHA-256 일치했다. MacBook은 기존과 동일한 `bash scripts/install.sh --upgrade --python /opt/homebrew/bin/python3.12 --settings ~/.config/open-scribe/settings.json` 경로, Mac mini는 BatchMode SSH·명시 PATH·`~/.local/bin/python3.12`·private staging installer 경로로 업데이트했다. 양쪽 exit 0, 이번 dependency 추가·버전 변경은 모두 0개였다.

양쪽 active JSON·RC·Git index·HEAD 및 Git 상태가 시작 지문과 같았다. Mac mini repo는 clean이며 모델 디렉터리·mlx/mlx-audio/mlx-lm/torch 없이 core API only다. MacBook 기존 모델 파일의 목록·size·mtime도 전후 일치했다. 설정 생성·덮어쓰기·기본 모델 변경·새 shell 등록·키 wrapper·모델 전송은 없었다.

양쪽 설치된 main.py CLI entry에서 이전과 동일한 5개 모의 HTTP 경로를 실행했다. default off exit 0, relisten 모델 미준비 partial/exit 2, cloud diarization exit 0, speaker names exit 0, unsupported provider exit 1/POST 0/DB 생성 0을 확인했다. 원문·단어 시간과 private test settings byte 불변도 확인했다. 실제 외부 API는 호출하지 않았다.

### 마지막 probe 입력·관측 방법

입력은 앞선 F 실행의 `correct-items.json` 바이트를 그대로 복사한 original/candidate 각 220 English words와 기존 합성 audio 7.0526875초다. 이전 items SHA-256과 새 사본이 같았다. ASR·LLM 준비 디렉터리·max_tokens 512·max_input_tokens 4096·언어 en은 그대로다. 새 private settings의 데이터·캐시 출력 경로만 이번 state로 분리했고 active settings는 쓰지 않았다.

설치된 공개 CLI doctor 경로를 호출했다. 별도 private 관측 harness는 원래 guard/validator의 인자·반환·예외를 유지하면서 parent memory check와 read_telemetry의 실제 입력, helper request/memory, entry/실패/종료 pressure·available을 기록했다. 제품 파일이나 child 모델 코드는 수정하지 않았다. telemetry max_age 3초와 기존 grace·poll·CPU·메모리·timeout·offline·parent-death 조건을 바꾸지 않았다. guard가 거절하면 그대로 종료했고 반복 loop로 모델을 재시도하지 않았다.

### CORRECT: 마지막 1회, stale telemetry defer

`correct-final-status.json`의 결과는 exit 1·elapsed 10.362547초다. entry pressure는 normal, available 14,913,470,464바이트였다. 최종 예외는 `RuntimeError: local helper telemetry unavailable`이다.

실패 순간 `read_telemetry` 관측은 다음과 같다. 모두 같은 monotonic clock 기준이며 값은 `diagnostics/correct-final-trace.jsonl`에 보존했다.

| 항목 | 실제 값 |
| --- | --- |
| helper folder | `4c8e4193685c441886f06576e1d21af1` |
| expected/sample PID | 37296 / 37296 |
| final_required | false |
| sample observed_at | 780609.029561458 |
| parent read observed_at | 780612.931959291 |
| last_sample_age / max_age | 3.902397833 / 3.0초 |
| 마지막 sample host peak / accelerator peak | 102,154,240 / 0바이트 |
| parent guard 관측 host 최대 | 141,901,824바이트; 전체 lifetime peak로 확정하지 않음 |
| 실패 직후 pressure / available | normal / 15,353,790,464바이트 |

이 표본은 sample stale로 guard가 거절한 것까지 확인된다. 가용 메모리 8 GiB 미만이나 pressure 비정상이 원인이었다고 바꾸지 않는다. telemetry 갱신이 늦어진 원인이 GIL·native import·다른 환경 요인 중 무엇인지는 관측만으로 확정하지 않는다. 상한·telemetry grace를 늘리지 않았다.

이번 CORRECT에서는 decoder 결과와 `raw_text`가 parent 관측에 도달하지 않았다. 수락된 자원 evidence, prompt/generated 토큰 수, 정식 JSON fence/alias 형태·semantic review 판정은 생성되지 않았다. raw를 빈 문자열이나 성공 JSON으로 만들어 보충하지 않았다. private `diagnostics/correct-final-no-raw-diagnostic.json`에 `raw_model_text:null`, `raw_status=not_observed`, parse 단계 미도달·예외·sample age·환경을 명시했다. 이는 raw 생성이 없었다는 증명이 아니라 결과가 관측되지 않았다는 보존 한계다. 이번 telemetry 중단을 이전 JSON 실패의 원인으로 소급하지 않는다. CORRECT 추가 재시도는 0회다.

### ASR: 마지막 1회, 해당 범위 자원 qualification 통과

entry pressure normal·available 13,700,988,928바이트를 확인한 뒤 ASR을 한 번 실행했다. 결과는 exit 0, 전체 CLI elapsed 9.718430초이며 실제 helper 측정 elapsed 8.583289초다. 결과와 telemetry를 private 파일에 저장했다.

| 수락된 evidence 필드 | 값 |
| --- | --- |
| qualification ID | `af17f6a1342d4ea99a9ef90d062dd21e` |
| 위치 | `local/qualifications/af17f6a1342d4ea99a9ef90d062dd21e.json` |
| task / profile / device | asr / qwen-0.6 / mlx |
| qualified audio seconds | 7.0526875 |
| length_independent | false |
| host_peak_bytes | 1,109,377,024 |
| accelerator_peak_bytes / peak_bytes | 1,527,556,552 / 1,527,556,552 |
| samples | 9 |
| runtime fingerprint | `31dd106e77d925491543bb08268174f620f742e9b660fa0d6478b8d22d3c2b89` |
| ASR decoding | max_tokens 512, temperature 0, repetition_penalty 1.0 |
| local policy | helper 1 / CPU 2 / available 8 GiB / qual peak 3 GiB / stop 4 GiB / timeout 120초 |

최종 sample은 `observed_at=780712.230495625`, parent read는 `780712.686931083`, age 0.456435458초, final=true였다. sample peak 외에 parent가 본 process-tree RSS도 수락된 host peak에 반영됐다. 종료 pressure normal·available 14,627,553,280바이트이며 helper 폴더 잔존 0개·global mutex 해제도 확인했다. ASR 결과 원문은 출력하지 않았고 `diagnostics/asr-final-result.json`에 저장했다.

이 evidence는 현재 모델·runtime·옵션·정책 및 7.0526875초 이하의 측정 길이 자격이다. 28초·60분 처리나 전사 정답·CER·다른 언어/환경 자격으로 확대하지 않는다. production root로 qualification을 복사하거나 기본 local 옵션을 켜지 않았다.

### helper flow·이력·원장 판정

새 private root의 qualification은 ASR 1개·CORRECT 0개다. CORRECT 자원이 통과한 경우에만 허용된 pending-relisten helper flow는 전제 미충족으로 실행하지 않았다. 따라서 API 원문 불변·review/output 보존의 새 실제 ASR+LLM E2E는 이번 라운드에서 검증 완료가 아니다. 이전 모의 경로와 이전 실제 API 원문 보존 결과는 각각 해당 이력의 근거로 남긴다. 새 decoder의 정식 fence/alias 지원은 D/E 코드 검사 근거이며 이번 실제 decoder 측정 통과로 쓰지 않는다.

이전 실패 state `20261105T161653Z-cbf6fe3b`의 qualification 0, raw 유실·JSON 실패·655 manifest와 그후 A가 수행한 별도 표본의 사실 관계를 덮어쓰지 않았다. F가 A 세션의 산출물을 자기 새 evidence로 합치지도 않았다. 이번 ASR 자격은 새 root에만 생성했다.

공유 원장을 read-only로 전후 조회한 결과 모두 89건·USD 0.165969878158062·unknown 0이었다. 이번 유료 POST 0이며 기존 API 3회 실증·재개 추가 과금 0을 그대로 보존했다. 키 파일 접근·가격 재조회·모델 다운로드·추가 feature·제품 코드 수정·commit/push·외부 메시지 발송은 없었다.

### 최신 영수증과 원복

이번 state 기준 주요 파일은 `source-freeze.json`, `installation-verification.json`, `installed-smoke-result.json`, `correct-final-status.json`, `asr-final-status.json`, `final-release-summary.json`, `history-preservation.json`이다. CORRECT 실패의 구체 상태는 `diagnostics/correct-final-trace.jsonl` 및 `correct-final-no-raw-diagnostic.json`, ASR 성공은 `diagnostics/asr-final-trace.jsonl`·`asr-final-result.json`과 위 qualification JSON으로 확인한다. CORRECT에 실제 raw text 파일이 존재한다고 주장하지 않는다. 모든 파일은 repo 밖 private state에 있다.

| 대상 | 이번 직전 runtime backup | 이번 직전 command backup |
| --- | --- | --- |
| MacBook | `~/.local/lib/open-scribe.backup-M2ARzO` | `~/.local/bin/scribe.backup-M2ARzO` |
| Mac mini | `~/.local/lib/open-scribe.backup-rNxeAf` | `~/.local/bin/scribe.backup-rNxeAf` |

이전 단계의 YE3u0I/eVOpfa 백업도 삭제하지 않았다. 이번 직전 버전으로 원복할 때는 실행 작업이 없는 상태에서 다음 순서를 사용한다. Mac mini에서는 같은 private state 경로와 suffix `rNxeAf`를 사용한다. 아래 명령은 안내이며 실행하지 않았다.

```sh
test ! -e "$HOME/.local/state/open-scribe/release-validation/20261105T171644Z-final-02a96c/rollback-current-runtime" && \
  mv "$HOME/.local/lib/open-scribe" "$HOME/.local/state/open-scribe/release-validation/20261105T171644Z-final-02a96c/rollback-current-runtime" && \
  mv "$HOME/.local/lib/open-scribe.backup-M2ARzO" "$HOME/.local/lib/open-scribe" && \
  cp -p "$HOME/.local/bin/scribe.backup-M2ARzO" "$HOME/.local/bin/scribe"
```

마지막 라운드 판정: 두 host 설치·기본값 보존·설치 CLI 및 ASR의 짧은 자원 자격은 완료, CORRECT 실제 자격·정식 decoder 형태·전체 로컬 E2E는 defer다. 허용된 CORRECT 1회·ASR 1회만 실행하고 추가 loop 없이 종료했다.
