# Open-Scribe 0.3.0

Homebrew 0.2.4의 CLI·출력·파일 처리에 최신 모델 연결을 적용한 소스 버전입니다.

```sh
openscribe ls       # 최근 10건
scr ls 20           # 최근 20건
scr "https://youtu.be/VIDEO_ID"
scr "/path/to/audio.wav" --no-summary
scr "URL" --engine elevenlabs/scribe-v2 --timestamp --srt
```

기존과 같이 영상 제목을 표시하고 전사 본문을 출력하며 제목 기반 TXT·요약 파일을 만듭니다.
`--downloads`는 설정된 Downloads 경로에 제목 파일명을 그대로 복사합니다.
`--no-stream`은 전사 본문 출력을 끕니다. 요약은 기본 활성화이며 `--no-summary`로 끕니다.

- ASR 기본: `elevenlabs/scribe-v2`, OpenRouter 음성 API
- 텍스트 기본: `openai/gpt-6-luna`, 같은 모델의 native 키가 있으면 직접 연결
- 다른 ASR 모델과 기존 엔진: `scribe --help`
- 모델 설정: `${OPEN_SCRIBE_SETTINGS:-~/.config/open-scribe/settings.json}`의 stages 모델·options
- 일반 옵션·경로·연동: 모두 `settings.json`에서 설정하며 `.env`를 자동 로드하지 않음
- 공급자 키 파일: settings.json의 `providers.<provider>.api_key_file`과 `api_key_env`로 명시

키 파일은 현재 사용자 소유·권한 600이어야 하며 지정한 키만 읽습니다. 키를 전역 export하거나
Keychain에서 자동 조회하지 않습니다. 파일을 지정하면 환경변수로 대체하지 않습니다.
요청 실패를 다른 모델·자막으로 대체하거나 자동 재시도하지 않습니다.

## 설치

```sh
brew tap ysys143/open-scribe
brew install open-scribe
```

소스 설치:

```sh
bash scripts/install.sh --python python3.11
# 준비된 Python 환경을 재사용할 때
bash scripts/install.sh --venv /path/to/venv
```

설치기는 설정·키·DB를 수정하지 않습니다. 기존 대상 교체에는 `--upgrade`가 필요합니다.
기본 설치 대상은 `~/.local/lib/open-scribe`, 명령은 `~/.local/bin/scribe`, `scr`, `openscribe`입니다.
`OPEN_SCRIBE_HOME`, `OPEN_SCRIBE_BIN_DIR`로 다른 경로를 선택할 수 있습니다.

## 내부 구조

```text
src/core/config/         기존 설정과 경로
src/core/providers/      업데이트 모델과 인증·API 연결
src/core/speech/         오디오 처리와 전사 엔진
src/core/postprocess/    요약·번역·교정·자막
src/core/presentation/   CLI·진행 출력·파일 출력
src/core/runtime/        기존 DB·큐·워커
src/integrations/        YouTube 다운로드·Notion
```

`src/cli.py`, `src/config.py`는 기존 호출자의 호환 진입점입니다.
조사 리포트는 [docs/research](docs/research/2026-11/deliverables/00-synthesis.md),
이전 설계·구현 문서는 [docs/archive](docs/README.md)에 보존했습니다.

## 요약 모델의 화자 이름 적용

화자 분리 모델이 실제 화자 레이블을 반환하고 요약이 활성화된 경우, 같은 요약 요청에서
문맥상 화자 이름과 근거를 함께 받습니다. 명시적인 자기소개가 자신의 발화에 있고 인용문에
이름이 실제 포함된 후보만 적용합니다. 그 외에는 원래 레이블을 유지합니다. 이는 텍스트 기반
추정이며 사용자 확인을 뜻하지 않습니다. 화자 분리를 쓰지 않거나 `--no-summary`이면 실행하지 않습니다.

청크별 화자 번호는 별개로 취급합니다. 이름은 레이블 위치만 치환하고 발화 본문은 바꾸지 않습니다.
최종 전사·요약·번역·Notion·Downloads 사본에는 적용된 이름을 사용합니다.
원본은 `<제목>_raw_<hash>.txt`, ASR 레이블 근거는 `<제목>_diarization.json`,
이름 추정 근거와 미확정 후보는 `<제목>_speaker_names.json`에 보존합니다.
API 응답에 실제 화자 정보가 없으면 일반 요약만 수행합니다. 모델 호출을 추가하지 않습니다.

## 설정 파일 하나로 관리

```sh
openscribe config show
scr config validate
```

기본 경로는 `~/.config/open-scribe/settings.json`입니다. `OPEN_SCRIBE_SETTINGS`로 다른 JSON을
선택할 수 있습니다. 일반 설정의 우선순위는 **CLI 옵션 → JSON → 내장 기본값**입니다.
기존 `.env`나 `OPEN_SCRIBE_STREAM` 등 일반 환경변수는 읽지 않습니다. 설정은 프로세스 시작 시
선택한 파일을 기준으로 고정되며 편집 내용은 다음 CLI 실행 또는 서비스 재시작 때 반영됩니다.

```json
{
  "version": 1,
  "copy_to_path": "/absolute/path/to/copies",
  "paths": {"data": "~/.local/share/open-scribe"},
  "output": {"stream": true, "downloads": true, "timestamp": true, "keep_audio": true},
  "stages": {"summary": {"enabled": true}, "translate": {"enabled": false}},
  "providers": {"openrouter": {"api_key_env": "OPENROUTER_API_KEY", "api_key_file": "/absolute/path/to/keys.env"}}
}
```

`copy_to_path` 아래에 제목 파일명으로 복사합니다. `null`이면 복사를 끄며 내장 Downloads 경로는
없습니다. `--no-downloads`로 이번 실행만 복사를 끌 수 있습니다. 상대 경로는 JSON 파일이 있는
디렉터리를 기준으로 해석합니다. `paths`의 개별 경로를 생략하면 data 아래에서 파생합니다.
요약·번역 on/off는 `stages.<stage>.enabled`, 언어는 `options.language`에서 설정합니다.

키 값은 JSON에 넣지 않습니다. `providers`와 `integrations`의 `api_key_file`에 기존 키 파일을,
`api_key_env`에 읽을 변수명을 지정합니다. 지정한 변수의 리터럴 값만 읽으며 다른 변수는
프로세스에 주입하지 않습니다. 파일을 지정한 경우 환경변수로 대체하지 않습니다. 파일을
지정하지 않았을 때만 해당 프로세스의 명시적 인증 환경변수를 사용합니다. Keychain은 조회하지 않습니다.
Notion의 enabled·database_id, 다운로드 설정, 워커 수, Whisper 경로, bot 옵션도 JSON에 있습니다.
`--update-key`는 키 파일 관리 안내만 출력하며 파일을 쓰거나 키를 복사하지 않습니다.

업그레이드 시 설정 이전 내용은 [CHANGELOG.md](CHANGELOG.md)를 확인하세요.
