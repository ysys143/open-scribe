# OpenScribe 사용 안내

이 안내는 Mac의 단일 core CLI와 같은 서비스를 사용하는 Telegram polling을 설명한다. 실제 외부 API·모델 품질과 GPU 적격성은 별도 검증 대상이다.

[문서 입구](README.md) · [현재 구조](architecture.md) · [선택 기능 계약·동결 소스 검증](development/optional-modes-implementation.md) · [담당 F의 릴리스 기록](archive/rework/optional-modes-release.md)

## 설치와 기존 환경 보존

Python 3.12 이상, uv, ffmpeg·ffprobe를 준비한 뒤 소스 저장소 루트에서 실행한다.

```sh
bash scripts/install.sh --python python3.12
"$HOME/.local/bin/scribe" --help
"$HOME/.local/bin/scribe" doctor
```

기본 경로:

| 용도 | 경로 또는 설정 |
| --- | --- |
| 코드·venv | `OPEN_SCRIBE_HOME`, 기본 `~/.local/lib/open-scribe` |
| 실행 명령 | `OPEN_SCRIBE_BIN_DIR/scribe`, 기본 `~/.local/bin/scribe` |
| 설정 | `--config` 또는 `OPEN_SCRIBE_SETTINGS`, 기본 `${XDG_CONFIG_HOME:-~/.config}/open-scribe/settings.json` |
| 작업·결과 | `--data-dir` 또는 `paths.data`, 기본 XDG data의 `open-scribe` |
| XDG data 기본값 | `${XDG_DATA_HOME:-~/.local/share}/open-scribe` |

저장소의 실행 래퍼는 `scripts/launchers/` 아래의 `scribe.sh`, `scribe.zsh`, `scribe.ps1`이다. 설치본의 전역 명령은 이 Bash 래퍼를 실행한다. 구형 셸 설정이 설치본 최상단 래퍼를 source하는 경우를 위해 설치기는 세 파일의 호환 진입점도 생성한다.

`--prefix DIR`는 코드 위치를 `DIR/lib/open-scribe`, 명령 위치를 `DIR/bin/scribe`로 정한다. 데이터 위치는 바꾸지 않는다. 기존 코드 디렉터리·명령이 있으면 설치기는 중단한다. 실패한 새 설치 디렉터리도 자동 삭제하지 않으므로, 상태를 확인하고 다시 시도할 때 새 prefix를 사용한다. 기존 사용자 설정·원본·데이터베이스·모델을 복사하거나 덮어쓰지 않는다.

설치 단계는 다음과 같다.

1. `src`·`bot`의 Python 소스와 명시적으로 선택한 진입점·wrapper·문서를 복사한다. `.git`, `.env`, 기존 venv, 원본 오디오, DB, 모델과 캐시는 복사 대상에서 제외한다.
2. 지정한 기존 Python으로 uv venv를 생성한다. Python 자동 다운로드는 비활성화한다.
3. `uv pip install --python ... -r requirements/requirements.txt`로 core 의존성을 설치한다. 로컬 모델 backend는 별도로 준비한다.
4. 설치된 실제 명령에서 `--help`와 `doctor`를 실행한다. doctor의 데이터·설정 경로는 임시 디렉터리를 사용한다.

셸 등록은 `--register-shell FILE`을 지정한 경우에만 수행한다. 예:

```sh
bash scripts/install.sh --prefix "$HOME/.local/open-scribe-rework" \
  --python python3.12 --register-shell "$HOME/.zshrc"
```

지정한 셸 파일에 기존 내용을 유지한 채 PATH·코드 경로를 추가한다. 경로의 공백·따옴표·달러 기호는 셸 리터럴로 인용한다. 등록한 셸 파일을 다음 셸에서 읽으면 적용된다. 업데이트는 `bash scripts/install.sh --upgrade --python python3.12` 또는 저장소 루트의 `make update`로 명시적으로 실행한다. 기존 런타임과 명령은 백업한다. `make`는 Python 3.12를 우선 찾고, 없으면 `python3`를 사용하며 `SCRIBE_PYTHON`으로 지정할 수 있다. 다른 디렉터리에서는 `make -C /저장소/경로 update`를 사용한다.

## 의존성 설치 없이 임시 검증

이미 프로젝트 `.venv`에 의존성이 준비되어 있을 때만 사용한다. 이 옵션은 해당 venv를 수정하지 않고 설치 경로에서 참조한다.

```sh
sandbox=$(mktemp -d)
bash scripts/install.sh --prefix "$sandbox" --skip-deps \
  --venv "$PWD/.venv" --python "$PWD/.venv/bin/python"
"$sandbox/bin/scribe" --help
"$sandbox/bin/scribe" --data-dir "$sandbox/check-data" doctor
```

`--skip-deps`에는 `--venv DIR`가 필수다. core 의존성까지 없는 venv는 smoke에서 실패한다. 이 검증은 패키지 다운로드·모델 다운로드·추론 API·polling을 실행하지 않는다. 기본 설치의 의존성 다운로드 성공이나 실제 모델 품질을 증명하지는 않는다.

일반 `scribe doctor`와 `scribe models`는 읽기 전용 preflight다. SQLite나 작업 디렉터리를 초기화하지 않는다. `doctor --qualify`는 아래의 명시적 로컬 측정·자격 저장 명령이며 일반 진단과 구분한다.

## 키와 설정

활성 설정은 `settings.json` 하나다. 파일 선택 순서는 다음과 같다.

1. 명시적 `--config PATH`
2. 실행 환경의 `OPEN_SCRIBE_SETTINGS`
3. `${XDG_CONFIG_HOME:-~/.config}/open-scribe/settings.json`

값은 명시적 CLI 옵션이 파일보다 우선하고, 생략한 값은 파일과 내장 기본값을 따른다. 일반 실행에서 `.env`·`helpers.json`을 보충 설정으로 읽지 않는다. 래퍼는 인자를 그대로 전달하며 개인 키 파일을 읽거나 source하지 않는다. 앱에도 자격 증명 보완용 재실행 경로가 없다. 설치기는 키나 설정을 작성하지 않는다.

```sh
scribe config init
scribe config show
scribe config validate
scribe config init --config "/path/to/settings.json"
scribe config show --config "/path/to/settings.json"
```

`config init`은 전체 기본값을 기록하며 기존 파일은 덮어쓰지 않는다. 교체를 명시할 때만 `config init --force`를 쓴다. 다른 출력 경로는 `--output PATH`로 지정한다. `config show`는 `settings`와 `sources`를 출력한다. `config validate`는 스키마·공급자·옵션·자원 값을 검사한다. show·validate·일반 doctor·models는 DB와 작업 폴더를 초기화하지 않는다. 설정 파일이 없어도 내장 기본값으로 실행하며, 알 수 없는 키나 유효하지 않은 설정은 오류로 보고한다.

| 섹션 | 주요 설정 |
| --- | --- |
| `paths` | `data`, `cache`, `database`, `downloads`; database가 null이면 data 아래 `transcription_jobs.db` |
| `providers.openai`, `providers.anthropic`, `providers.openrouter` | `api_key_env`, `base_url`; 키 값 대신 환경 변수 이름 |
| `stages` | `asr`, `alignment`, `diarization`, `embedding`, `relisten`, `speaker_names`, `summary`, `translate`, `correct` |
| `resources.remote` | `concurrency`, `budget_usd`, `budget_scope` |
| `resources.local` | `concurrency`, `cpu_threads`, `min_available_gib`, `qualified_peak_gib`, `memory_ceiling_gib`, `poll_seconds`, `timeout_min_seconds`, `timeout_max_seconds`, `timeout_factor` |
| `output` | `downloads`, `keep_audio`, `video`, `require_srt`, `timestamp`, `stream`, `verbose`, `retention_days` |
| `integrations.telegram` | `allowed_users`(숫자 ID 문자열 목록), `token_env` |
| `integrations.notion` | `enabled`, `api_key_env`, `database_id` |
| `download` | `cookies_browser`, `proxy`, `remote_components`, `player_clients` |

상대 경로는 설정 파일의 부모 디렉터리를 기준으로 해석한다. `--data-dir DIR`는 해당 실행의 결과·DB를 함께 선택한다. 별도 `paths.database`를 유지할 때는 `--data-dir`를 생략한다.

모든 단계는 `enabled`, `provider`, `model`, `options`를 갖는다. 원격 ASR·요약·번역·교정은 기본 `auto`이며 같은 모델의 native API 키가 있으면 우선 사용하고, 없으면 OpenRouter를 선택한다. 기존 `openrouter` 설정도 같은 키 우선순위를 따른다. summary·translate·correct는 각각 model과 `options.effort`를 선택하며 서로 독립적이다. `--text-model`은 세 단계의 모델을 함께 덮어쓰고, `--summary-model`, `--translate-model`, `--correct-model`은 지정한 단계만 덮어쓴다. 같은 호출에서는 단계별 옵션이 `--text-model`보다 우선한다. `--effort`는 세 텍스트 단계의 effort를 함께 덮어쓴다. `speaker_names`의 모델·effort는 해당 stage 설정으로 선택한다.

로컬 ASR은 provider가 `mlx`이고 model은 `qwen-0.6`, `qwen-1.7`, `whisper-turbo`, `parakeet`, `phonon` 중 하나다. model에서 내부 backend를 정규화하므로 alias를 두 곳에서 지정할 필요가 없다. ASR options에는 `model_dir`, `device`, `language`도 있다. 로컬 정렬·화자 분리·embedding의 provider는 각각 `mlx`, `pyannote`, `speechbrain`이며 준비한 `options.model_dir`와 장치를 사용한다. 별도 원격 화자 분리는 `diarization.provider=openrouter`로 구분한다. 다음은 `stages.asr`에 병합하는 블록이며 기본 로컬 활성화를 뜻하지 않는다.

```json
{
  "enabled": true,
  "provider": "mlx",
  "model": "qwen-0.6",
  "options": {"model_dir": "/path/to/asr-model", "device": "mlx", "language": "ko"}
}
```

키 값은 설정에 넣지 않는다. 원격 공급자는 명시된 api_key_file에서 지정 변수를 읽으며 파일이 지정되지 않았을 때만 실행 환경 키를 읽는다. Keychain 자동 조회는 없다. OpenAI·Anthropic·OpenRouter는 각각 `providers.openai.api_key_env`, `providers.anthropic.api_key_env`, `providers.openrouter.api_key_env`를 사용한다. Telegram은 `integrations.telegram.token_env`, Notion은 `integrations.notion.api_key_env`가 가리키는 이름만 사용한다. 기본 이름은 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, `NOTION_API_KEY`다. `config show`와 doctor는 키 값을 출력하지 않는다. 키가 없어도 `--background`로 접수할 수 있으며 실제 실행에는 필요한 인증이 있어야 한다. Notion 게시를 선택할 때는 설정과 명시적 `--notion`을 확인한다.

### 인증 상태 확인

`scribe auth status [provider]`는 `set`, `missing`, `error`만 출력한다. `doctor`의
`credential_states`는 출처가 `file`인지 확인할 수 있다. 실제 API 유효성·과금은 검사하지 않는다.
Keychain login/logout은 과거 항목 관리용 호환 명령이며 현재 실행 인증에는 사용하지 않는다.
기존 항목은 별도 삭제 요청 없이 제거하지 않는다.

### 기존 설정의 명시적 변환

레거시 파일을 변환할 때만 직접 경로를 지정한다. 두 입력 중 하나만 지정해도 된다.

```sh
scribe config migrate --legacy-env "/path/to/old.env" \
  --helpers "/path/to/helpers.json" --output "/path/to/settings.candidate.json"
scribe config validate --config "/path/to/settings.candidate.json"
scribe config show --config "/path/to/settings.candidate.json"
```

변환은 허용된 비밀 아닌 설정만 가져오고 셸 코드를 실행하거나 환경 변수로 로드하지 않는다. 키 값과 이전 자격은 가져오지 않으므로 자격 측정은 다시 수행한다. 원본을 수정하지 않으며 출력 파일이 이미 있으면 `.candidate` 파일을 별도로 작성한다. 보고서에는 가져온 설정 이름, 제외한 이름, 출력 경로가 표시된다. 검토 후 사용할 파일을 `--config` 또는 `OPEN_SCRIBE_SETTINGS`로 선택한다.

## 전사와 출력

### Scribe v2의 API 화자 분리

`stages.asr.model`을 `elevenlabs/scribe-v2`로 선택하고 `stages.asr.options.provider_options`에 `{"elevenlabs":{"diarize":true,"tag_audio_events":false,"no_verbatim":false}}`를 지정하면 OpenRouter에 단어 시간과 화자 라벨을 함께 요청한다. 이 경우에도 별도 `alignment`·`diarization`·`embedding`은 비활성화 상태로 사용할 수 있다. primary ASR 자체 화자 옵션에는 `--speakers`가 필요하지 않다. 그 플래그는 설정에서 선택한 별도 diarization 단계를 켠다.

화자 수를 모르면 `num_speakers`를 생략한다. 개수와 `diarization_threshold`는 동시에 지정할 수 없으며 endpoint가 화자 분리를 지원하지 않으면 업로드 전에 거절한다. API가 라벨을 반환하지 않으면 검토 대상으로 남긴다.

화자 라벨의 범위는 API 요청 하나다. 현재 클라이언트가 긴 파일을 나눠 요청하면 각 요청의 `speaker_0`을 같은 사람으로 합치지 않고 요청별 namespace로 보존한다. 이 경우 전체 화자 연결은 partial이며, 전역 화자 일관성을 확인했다고 표시하지 않는다. 이번 단일 요청 시험은 28초 구간이며 전체 60분 전사·화자 일관성을 검증한 결과가 아니다. [시험 기록](archive/rework/scribe-diarization-trial.md)

기본 전사·요약은 원격 API만 사용한다. 지원하는 OpenAI·Claude 모델은 해당 native 키가 실행 환경에 있으면 직접 호출하고, 없으면 OpenRouter를 사용한다. 기본 `provider=auto`와 기존 `provider=openrouter` 모두 이 우선순위를 따른다. 직접 요청 실패를 자동 OpenRouter 재요청으로 바꾸지 않는다. `alignment`, `diarization`, `embedding`, `relisten`, `speaker_names`는 기본 `enabled=false`다. 비활성화한 로컬 단계는 모델 파일 검사도 하지 않는다. API 응답에 시간·화자가 있으면 보존하고, 미반환 정보는 미확정으로 남긴다. 자막 시간이 필요하지만 API가 반환하지 않으면 자동 로컬 보완 없이 partial로 보고한다. `--speakers`는 설정에서 선택한 화자 분리 공급자를 활성화한다. `pyannote`를 선택했을 때만 정렬·임베딩도 명시 활성화한다. `--speakers-provider openrouter --speakers`는 로컬 단계를 자동으로 켜지 않는다. 기존 작업의 재개는 접수 당시 고정 설정을 따른다.

## 선택 파이프라인

아래 예시는 기존 `settings.json`의 `stages` 안에 병합하는 블록이다. 개인 설정 파일이나 기본 모델을 자동으로 바꾸지 않는다. CLI, SDK, Telegram에서 접수한 작업 모두 같은 stage 설정을 스냅샷으로 저장하며 재개 때도 그 값을 사용한다. CLI의 `--relisten`, `--speaker-names`는 해당 실행의 enabled 값만 바꾼다.

API 전사 후 소형 로컬 ASR 재청취와 LLM 교정 후보를 만들려면 다음을 선택한다. 경로는 이미 준비한 디렉터리이며 설정 파일 기준 상대 경로도 허용한다. 예시의 `max_windows=6`은 명시적 작업량 제한이다. 현재 `settings.defaults()`의 내장값은 32이고, 설정을 거치지 않고 `run_relisten`에 옵션을 생략하는 직접 함수 호출의 fallback은 6이다. CLI·SDK·Telegram의 Application 경로는 settings에서 병합한 값을 전달한다. 문서 정리를 위해 이 코드 차이나 개인 설정을 변경하지 않았다.

```json
{
  "relisten": {
    "enabled": true,
    "provider": "mlx",
    "model": "qwen3-0.6b",
    "options": {
      "asr_backend": "qwen-0.6",
      "asr_model_dir": "models/relisten-asr",
      "llm_model_dir": "models/relisten-llm",
      "language": "ko",
      "apply": false,
      "max_window_seconds": 30,
      "max_windows": 6,
      "max_tokens": 512,
      "max_input_tokens": 4096
    }
  }
}
```

원래 API 본문·단어·화자·시간은 `transcript.json`과 ASR 캐시에 유지한다. `relisten-raw.json`에는 재청취 근거, `relisten-derived.json`에는 교정 후보, `relisten/transcript.json`에는 선택한 apply 결과를 보관한다. `apply=false`가 기본이다. `apply=true`라도 숫자·부정·인명 등 어휘 변경은 자동 적용하지 않고 검토 후보로 남긴다. 적용한 파생 본문은 기존 시간과 단어 정렬을 재사용하지 않으며 검토·재정렬 필요로 표시한다. `max_windows` 때문에 처리하지 않은 구간도 이유와 시간을 기록하며 원문에서 삭제하지 않는다. 현재 요약은 canonical API 전사를 기준으로 한다.

로컬 correct 응답 adapter는 완전한 JSON 객체 또는 추가 문장이 없는 단일 `json` 코드 fence만 처리한다. 최상위 `corrections`와 명시 alias `segments`만 허용하고, 항목의 ID·순서는 요청과 같아야 한다. JSON 수선·부분 추출·추가 prose·중복 키/ID·ID 변경은 거절한다. 원문 raw와 wrapper/alias 정규화 출처는 보존한다. 모델이 reason을 생략하면 `reason=not_supplied`, `reason_source=absent`, `semantic_review_required=true`로 기록하며, `apply=true`나 안전한 문장부호 변경이라도 자동 적용하지 않는다. decoder·응답 구조 검증과 의미 검토를 분리하며, 자원 자격 기록이 만들어져도 의미 검토를 대신하지 않는다. 이 코드 지원은 별도 실제 모델 probe의 성공 주장이 아니다.

로컬 단계는 기존 전역 helper 하나를 사용한다. CPU 2개, 시작 여유 메모리 8GiB, 실측 자격 3GiB, 실행 상한 4GiB, timeout·부모 사망 감시·offline·prepared-only 정책을 유지한다. 별도 ASR 자격과 correct의 실측 prompt token 자격이 필요하다. 모델·선택 라이브러리·자격이 없거나 timeout이 나면 API 원문과 캐시를 보존하고 partial로 보고한다. 자동 다운로드나 실제 모델 정확도 합격은 수행하지 않는다.

자격을 명시적으로 측정하는 공식 진입점은 다음과 같다. 이 명령은 실제 로컬 추론을 실행하므로 모델과 자원 준비가 끝난 경우에만 사용한다. 여기서는 명령을 실행해 자격을 만들지 않았다.

```sh
scribe doctor --qualify asr --relisten --audio "/path/to/probe.wav"
scribe doctor --qualify correct --audio "/path/to/probe.wav" --text-file "/path/to/correction-items.json"
```

correct의 text-file은 `[{"id":"s1","original":"안녕하세요","candidate":"안녕하세요."}]` 형식이다. `--model-dir`는 해당 측정 모델 경로만 덮어쓴다. 자격 측정은 설정 파일을 활성화하거나 바꾸지 않는다. correct의 측정 prompt token 상한을 넘는 입력은 실행을 보류하며 ASR 자격으로 대체하지 않는다.

API 전사와 별도 화자 API를 조합하려면 다음을 선택한다.

```json
{
  "asr": {"provider": "openrouter", "model": "openai/whisper-large-v3-turbo"},
  "diarization": {
    "enabled": true,
    "provider": "openrouter",
    "model": "elevenlabs/scribe-v2",
    "options": {
      "provider_options": {"elevenlabs": {"diarize": true, "tag_audio_events": false, "no_verbatim": false}}
    }
  }
}
```

ASR 모델은 사용자가 선택한 그대로다. 위 조합 예시가 기본 모델을 교체하지는 않는다. 별도 Scribe는 전체 소스 기준 한 번 요청하며 시간·화자 구간만 canonical ASR 단어에 겹침 기준으로 연결한다. Scribe 본문으로 ASR 본문·단어·번호·시간을 교체하지 않는다. ASR 단어 정렬이 없으면 원문을 보존하고 `needs_review`로 남기며 자동 로컬 보완은 하지 않는다. 원격 화자 캐시는 ASR 청크 경계 계획에 사용하지 않으므로 재개 시 청크가 이동하지 않는다.

별도 화자 단계는 원본이 24MiB를 넘으면 요청 전에 거절한다. 29MiB 원본도 이 제한에 걸리며 압축이나 분할로 제한을 우회하지 않는다. 범위 안의 소스는 16kHz mono 32kbps MP3로 변환하고 실제 업로드 파일에도 24MiB 제한을 적용한다. 요청 간 화자를 같은 인물로 합치지 않는다. OpenRouter의 처리 timeout은 장시간 입력의 성공을 보장하지 않는다. 선택한 `providers.openrouter.api_key_env`의 환경 변수 키가 필요하며 다른 native 키로 대신하지 않는다. 과금은 기존 원장·예산·동시성 제한을 공유한다. 결과를 알 수 없는 요청은 같은 작업 재개와 같은 소스의 다른 작업에서도 재호출을 차단한다.

사용자가 제공한 비교 단가는 Whisper 0.04달러/시간 + 별도 Scribe 0.22달러/시간 = 0.26달러/시간이며 Scribe 통합은 0.22달러/시간이다. 이 비교를 고정 청구 가격으로 사용하지 않고 실행 시 공급자 quote와 원장에 비용을 기록한다. 실제 유료 비교나 60분 재전사는 이번 구현 검증에 포함하지 않았다.

화자 분리 후 영상의 명찰·자막·자기소개·사용자가 제공한 맥락에서 이름 후보를 찾으려면 `speaker_names.enabled=true`를 선택한다. `options.context`는 문자열 또는 `title`, `description`, `participants`를 담은 객체다. `options.video`는 기존 영상의 경로이며 로컬 영상 입력 자체도 사용할 수 있다. 기존에 요청한 영상 다운로드 결과가 있을 때도 활용한다. 이 단계를 켰다는 이유만으로 영상을 추가 다운로드하지 않는다.

텍스트 요청은 세그먼트를 유지한 채 20KB 이하 배치로 나누고, 프레임은 최대 6장·총 base64 2MiB로 제한한다. 얼굴로 실명을 추정하지 않는다. 결과는 `speaker_names/suggestions.json`과 독립 파생 전사에 `suggested` 또는 `contextual` 후보로 저장한다. `apply_suggestions=false`가 기본이며 명시 활성화한 파생 표시에도 미검증 표시를 붙인다. 후보는 사람 확인·영구 인물·음성 임베딩 등록을 대신하지 않고 기존 확인 이름을 덮어쓰지 않는다. 확인된 이름의 `named/` 및 manifest는 이 경로가 수정하지 않는다.

원격 `correct`도 숫자·부정·고유명사 같은 어휘 변경은 원문에 적용하지 않고 `transformation_review`에 남긴다. 실제 변경한 교정·번역의 파생 파일은 원래 단어와 구간 시간을 무효화하고 재정렬 필요로 표시해 SRT를 생성하지 않는다. 원본 전사 출력은 유지한다.

```sh
scribe "/path/to/audio.wav"
scribe transcribe "https://www.youtube.com/watch?v=VIDEO_ID" --profile remote
scribe transcribe "https://www.youtube.com/playlist?list=PLAYLIST_ID" --background
scribe transcribe "/path/to/audio.wav" --translate --srt --language ko --json
```

짧은 입력 형식은 `transcribe`와 같다. 원격 전사와 요약·번역·교정은 모델별 API 키 우선순위를 따른다. 기본으로 요약을 요청하며 로컬 화자 분리는 비활성화다. `--no-summary`, `--no-speakers`, `--translate`, `--correct`로 선택한다. `--stream`은 단계 진행 표시이며 실시간 음성 전사를 뜻하지 않는다. `--timestamp`는 호환 옵션으로 접수되며, 자막 시간의 유효성은 실제 결과의 timing provenance로 판단한다.

### CLI 진행 표시와 출력 제어

stderr가 TTY이고 진행 표시가 활성화되어 있으면 기본 모드는 각 진행 이벤트를 새 줄에 누적한다. quiet 모드는 최대 3줄을 CR·커서 이동으로 갱신하며 재생목록도 같은 영역을 사용한다. quiet에서는 터미널 너비에 맞춰 표시를 자르고 최종 결과·오류 출력 전에는 진행 영역을 지운다. `--stream`·`--no-stream` 또는 `output.stream`으로 진행 표시를 선택한다.

`-q`, `-quiet`, `--quiet`는 같은 옵션이며 CR 방식의 간결한 진행 표시를 사용하고 verbose·일반 안내를 억제한다. 최종 작업 상태·결과 경로와 오류는 유지한다. `--verbose`를 함께 지정해도 quiet가 verbose 안내를 억제한다. 파이프나 파일로 stderr를 보내는 non-TTY 환경에서는 진행 표시를 누적하거나 그 표시용 ANSI 제어문자를 출력하지 않는다.

전사 명령의 `--json`은 진행 표시를 끄고 stdout의 기계 처리용 JSON을 유지한다. 오류는 stderr로 출력한다. verbose 정보도 stderr에 출력되므로 이를 억제하려면 quiet를 함께 사용한다.

```sh
scribe transcribe "/path/to/audio.wav" -q
scribe transcribe "/path/to/audio.wav" -quiet
scribe transcribe "/path/to/audio.wav" --quiet --json
```

코딩 에이전트의 도구 호출에는 명시적 `transcribe` 형식으로 JSON과 quiet를 함께 지정한다. `URL`은 실제 입력 URL로 바꾼다.

```sh
scribe transcribe 'URL' --json -q
```

수분 걸리는 실행도 호출 도구가 실행 세션을 유지하고 폴링할 수 있으면 동기 명령으로 결과를 기다릴 수 있다. 다음 종료 코드는 `--background` 없이 처리 결과를 기다리는 전사 명령 기준이다.

| 종료 코드 | 의미 |
| --- | --- |
| `0` | 결과 상태가 `completed`. 재생목록은 모든 결과가 `completed` |
| `2` | `partial` 등 `completed`가 아닌 결과가 반환됨. 재생목록은 하나라도 미완료 결과가 있음 |
| `1` | 처리 중 예외. 오류는 stderr에 출력하며 실패 JSON은 보장하지 않음 |
| `130` | Ctrl-C로 중단. 중단 안내는 stderr에 출력 |

`--json`의 stdout은 정상적으로 반환된 완료·부분 완료 등 처리 결과의 JSON이다. 예외까지 항상 JSON으로 반환하는 계약은 아니므로 종료 코드와 stderr를 함께 확인한다. 인자 파싱 오류는 argparse의 종료 코드 `2`일 수 있으며 부분 결과 JSON과 구분한다.

출력 옵션은 작업 실행 방식을 바꾸지 않는다. 기존 `--background`는 접수 후 반환하며 worker를 자동 시작하지 않는다. 처리는 같은 data·DB 설정으로 `scribe jobs work`를 명시적으로 실행한다.

원격 STT는 `--asr-model PROVIDER/MODEL`로 공통 `provider/model` ID를 선택할 수 있다. `openai/gpt-transcribe`는 OpenAI 직접 API 계약을 지원한다. `PROVIDER/MODEL`은 사용할 실제 STT ID로 바꾼다. 기본값은 `stages.asr.model`로 지정하며 명시적 `--asr-model`이 우선한다.

```sh
scribe transcribe "/path/to/audio.wav" --profile remote \
  --asr-model PROVIDER/MODEL --language ko
```

OpenRouter 경로는 오디오 업로드·유료 POST 전에 공개 endpoint metadata의 모델 ID 일치, 활성 endpoint, `audio->transcription` modality와 지원하는 초 단위 요율을 확인해 비용을 예약한다. native 경로는 확인된 동일 모델 계약과 native 요율·usage를 사용하며 OpenRouter 공개 metadata 조회로 대체하지 않는다. 요율·과금 단위를 지원하지 않으면 유료 요청을 시작하지 않는다. 모델 ID를 지정한 것만으로 언어·전사 품질·시간 정보 지원을 검증한 것은 아니다.

음성 청크는 16 kHz·mono·PCM16 WAV를 사용한다. 현재 `stages.asr.options.chunking` 기본값은 core 목표 30초, 최대 core 45초, 문맥 좌우 2초, 최소 꼬리 5초다. 문맥을 포함한 읽기 구간은 최대 49초이며 원본 양끝에서는 잘린다. 청크에는 추가 손실 압축을 적용하지 않고 실측 duration을 사용한다. 사용자 원본은 보존한다. 과거 문서의 120초 고정 청크는 그 당시 실행 기록이다.

정렬 언어는 `--language ko` 또는 `--language en`으로 지정한다. 명시하지 않았으면 전사 결과의 언어를 사용한다. 정렬이 필요한데 언어가 unknown이거나 지원 여부를 확인할 수 없으면 해당 단계를 미완으로 보고하고 원격 전사 결과를 보존한다. 정렬 측정에서도 지원 언어 지정이 필요하다.

결과는 data 디렉터리의 `jobs/JOB/`에 저장한다. 구조화된 `transcript.json`, 본문 TXT, 본문에 대응하는 시간·품질 조건이 충족될 때 SRT/VTT, 요청한 후처리의 `summary.md`·`translate.md`·`correct.md`를 확인한다. 번역·교정은 원래 segment ID 집합을 유지한 구조화 응답을 검증하고 `translate/`·`correct/`에 JSON/TXT를 생성한다. 본문을 변경한 파생 segment의 기존 시간은 무효화하므로 재정렬 전 SRT/VTT를 성공으로 내보내지 않는다. 생성된 캐시는 작업 폴더 안에 있으며 사용자 원본은 지우지 않는다. `--no-downloads`로 Downloads 사본 생성을 끈다. `--notion`은 명시적으로 외부 게시를 요청하므로 사용자가 게시를 선택할 때만 지정한다.

결과 상태가 `partial`이면 일부 청크·화자·후처리 단계가 실패했음을 뜻한다. 이미 얻은 원격 전사·요약은 보존한다. 시간이 없는 자막을 임의로 만들어 성공으로 표시하지 않는다. 처리 결과를 기다리는 전사 명령은 `completed`이면 0, 그 외 반환된 결과이면 2, 처리 중 예외이면 1, 사용자 중단이면 130을 반환한다.

### 호환 옵션과 이전 engine

| 입력 | 현재 동작 |
| --- | --- |
| `--profile remote` 또는 `--engine remote` | native 키 우선 원격 profile |
| `--profile local` 또는 `--engine local` | 검증된 로컬 ASR helper |
| `--engine whisper-cpp`, `whisper-local` | 로컬 profile의 MLX Whisper Turbo helper 선택; stderr에 런타임 전환 경고 |
| `--engine youtube`, `youtube-transcript-api` | YouTube 자막 profile; 요청한 화자·요약 단계는 별도 |
| 이전 직접 공급자 engine 및 `high`·`medium` | 명시적으로 거부; `--profile remote` API 경로 선택 안내 |
| `--no-srt` | 시간 있는 SRT의 필수 생성 요구를 해제; 시간이 있으면 공통 exporter가 SRT를 제공할 수 있음 |
| `--no-video` | 동영상 저장 요청을 끔; 기본값 |
| `-p N`, `--parallel N` | 양수 입력, 재생목록 실제 동시 실행은 최대 2개 |
| `-f`, `--force` | 새로운 UUID 작업을 접수하고 기존 작업·결과는 보존 |
| `scribe --update-key` | 이전 직접 공급자 키 입력·저장 흐름 종료 안내 후 코드 1 반환; 키 파일 수정 없음 |

`--update-key`는 키를 변경하지 않고 `providers.openrouter.api_key_file` 설정을 안내하며 종료 코드 1을 반환한다.

호환성 주의: `whisper-cpp`와 `whisper-local`의 현재 실행 경로는 **MLX Whisper Turbo**다. 기존 native whisper.cpp 실행 파일이나 CPP 모델 경로를 사용하지 않으며 CLI가 이 전환을 stderr에 경고한다. 명시적 표기는 `--profile local --local-model whisper-turbo`다. MLX 의존성·로컬 모델 준비·실측 자격이 필요하므로 기존 CPP 설치만으로 준비가 끝났다고 판단하지 않는다.

재생목록의 여러 작업은 ThreadPool에서 `min(2, N)`개까지 동시에 실행한다. `-p 1`은 한 작업씩 처리하고 2보다 큰 값도 실제 상한은 2다. 로컬 helper의 전역 단일 실행 제한은 유지한다. `--force`는 같은 입력에도 새 작업을 만들며, 기존 작업을 재개할 때는 `jobs retry JOB`을 사용한다.

입력 경로는 wrapper가 그대로 전달한다. `~`나 셸 변수를 확장하려면 호출하는 셸에서 `"$HOME/path/audio.wav"`처럼 확장한다. 문자열에 들어 있는 `$(...)`를 wrapper가 재평가하지 않는다.

## 작업 기록과 재시작

```sh
scribe jobs list
scribe jobs show JOB
scribe jobs work
scribe jobs retry JOB
scribe jobs retry JOB --stage summary
```

접수 시 입력·옵션을 SQLite에 고정하고, owner와 중복 키로 구분한다. `--background`는 접수 후 반환하며 worker를 자동 시작하지 않는다. 실제 처리를 진행하려면 `jobs work`를 명시적으로 실행해야 한다.

```sh
scribe transcribe "/path/to/audio.wav" --background
scribe jobs work
```

두 명령은 같은 data·DB 설정으로 실행한다. `jobs work`는 queued·만료 running 작업을 처리하고 완료된 청크·단계 결과를 재사용한다. 실제로 실행 중인 lease를 가진 작업은 다른 worker가 동시에 실행할 수 없다.

유료 호출 전에 OpenRouter는 공개 endpoint metadata의 모델·활성 상태·요율을, native 경로는 확인된 모델 계약·요율을 사용한다. 입력 토큰 상한 또는 오디오 초 단위의 최대 예상 비용을 공유 예산에 예약한다. 과금 계약을 확인할 수 없으면 유료 요청을 시작하지 않는다. 응답이 불명확하거나 이전 호출의 성공·과금이 확인되지 않은 단계는 자동 재호출하지 않는다. `--stage`를 지정해도 이 보호를 우회하지 않는다. 해당 호출과 과금 결과를 확인한 뒤 재시도 여부를 결정한다. 작업 status와 단계별 기록은 `jobs show JOB`에서 확인한다.

### 불명확한 호출의 비용 확인과 복구

먼저 `jobs show JOB`에서 비용 목록의 예약 ID(`id`)와 연결된 유료 단계(`stage`)를 확인한다. 공급자 측 실제 과금과 결과 존재 여부를 확인한 뒤 해당 예약을 정산한다. 실행 중인 lease가 있는 작업은 정산 대상이 될 수 없다. 아래 `JOB`, `RESERVATION`, `VERIFIED_USD`는 확인한 작업 ID·예약 ID·실제 달러 금액으로 바꾼다.

비용만 확인했고 결과 없음까지 확인하지 않았다면 비용만 정산한다. 이 명령은 단계 상태를 초기화하거나 유료 요청을 재실행하지 않는다.

```sh
scribe jobs show JOB
scribe jobs reconcile JOB --reservation RESERVATION --actual-cost VERIFIED_USD --confirm-cost
```

공급자에서 사용 가능한 결과가 없다는 사실까지 확인한 경우에는 별도의 확인 옵션을 사용한다. 기록에 이미 완료되거나 사용 가능한 결과가 있으면 단계 초기화를 거부한다.

```sh
scribe jobs reconcile JOB --reservation RESERVATION --actual-cost VERIFIED_USD --confirm-no-result
```

두 확인 옵션은 서로 배타적이며 하나를 명시해야 한다. 예약은 해당 작업·단계 기록과 일치해야 한다. 결과 없음 확인으로 정산한 뒤에도 자동으로 재실행하지 않는다. 이후 새 유료 호출을 선택할 때 `scribe jobs retry JOB`을 명시한다. 확인하지 못한 금액을 임의로 0으로 정산하거나 원장을 직접 지워 보호를 우회하지 않는다.

`scribe jobs prune`은 보존 기간이 지난 생성 오디오 캐시를 정리하는 별도 명령이다. 원본·결과·화자 벡터를 삭제하는 명령으로 사용하지 않는다. 데이터 삭제 작업이므로 실제 실행 전 대상 정책을 확인한다.

## 화자 확인과 로컬 모델

```sh
scribe speakers candidates JOB
scribe speakers confirm JOB:SPEAKER --person "이름"
scribe speakers enroll JOB:SPEAKER --person "이름"
scribe transcribe "/path/to/audio.wav" --profile local --local-model whisper-turbo --no-summary --language ko
```

`candidates`는 현재 작업의 화자와 해당 owner의 확인 인물·호환되는 음성 후보를 보여준다. 후보는 자동 확정이 아니다. `confirm`은 이름 연결을 명시 확인하며, 음성 벡터를 자동 등록하지 않는다. `enroll`은 같은 작업·화자의 확인이 선행되어야 하며 검증된 embedding helper로 벡터를 등록한다. 원본 클립은 기본 영구 보관 대상이 아니다. 벡터는 명시적으로 삭제할 때까지 유지한다.

인물 삭제를 선택한 경우에만 다음 명령을 실행한다. `--person`에는 본인 owner의 인물 이름 또는 ID를 지정한다. `--confirm`이 없으면 삭제를 거부한다.

```sh
scribe speakers forget --person "이름" --confirm
```

이 명령은 해당 인물의 이름·화자 확인 연결·모든 버전의 음성 벡터와 provenance를 삭제한다. 원본 오디오·작업 기록·전사 산출물은 보존한다. Telegram owner의 인물은 CLI의 `local` owner와 격리된다.

### 선택 로컬 runtime 준비

소스 설치에는 `requirements/requirements.local.in`과 생성된 `requirements/requirements.local.txt` 잠금파일도 동봉한다. 새 설치는 core의 `requirements/requirements.txt`가 기본이며 `--with-local-deps`로 로컬 그룹을 선택한다. 일반 `--upgrade`는 이전 런타임의 로컬 배포판 metadata를 확인해 로컬 그룹을 보존한다. 잠금 대상은 CPython 3.12·macOS 14 이상·Apple Silicon이며, 로컬 설치를 요청한 다른 플랫폼·Python 버전은 교체 전에 거절한다. 한국어 Qwen 시간 정렬에 필요한 `soynlp`도 로컬 잠금파일에 포함한다.

아래 명령은 사용자가 로컬 추론을 선택했을 때 실제 설치 환경에 명시적으로 적용한다. `scribe_install_dir`는 소스 설치 경로이며 별도 prefix를 사용했다면 해당 `lib/open-scribe` 경로로 바꾼다.

```sh
scribe_install_dir="${OPEN_SCRIBE_HOME:-$HOME/.local/lib/open-scribe}"
uv pip install --python "$scribe_install_dir/.venv/bin/python" \
  --require-hashes --only-binary :all: --no-python-downloads \
  -r "$scribe_install_dir/requirements/requirements.local.txt"
```

이 명령은 Python 패키지 환경을 변경한다. `--skip-deps --venv`로 만든 검증 설치는 venv를 공유하므로 독립된 설치 환경을 준비한 뒤 적용한다. TorchCodec에는 FFmpeg 공유 라이브러리도 필요하다. 잠금파일 생성·동봉은 실제 설치 성공, 모델 준비, GPU 품질을 검증한 결과가 아니다. 모델은 별도로 준비하고 아래의 실측 자격 절차를 수행한다. 모델 다운로드나 자격 부여는 자동 실행하지 않는다.

### 명시적 helper 적격성 측정

로컬 ASR 선택자는 `whisper-turbo`, `qwen-0.6`, `qwen-1.7`, `parakeet`, `phonon`이다. 선택자만으로 모델이 설치되거나 자원 적격성이 인정되지 않는다. 사전에 모델·backend 의존성을 로컬에 준비한 뒤, 실제 사용할 오디오로 다음 측정을 명시적으로 실행한다. 예시 경로는 준비한 파일 경로로 바꾼다.

```sh
scribe doctor --qualify asr --backend qwen-1.7 --device mlx \
  --model-dir "/path/to/asr-model" --audio "/path/to/sample.wav"

scribe doctor --qualify align --device mlx --language ko \
  --model-dir "/path/to/alignment-model" --audio "/path/to/sample.wav" \
  --text-file "/path/to/known-transcript.txt"

scribe doctor --qualify diarize --device cpu \
  --model-dir "/path/to/diarization-model" --audio "/path/to/sample.wav"

scribe doctor --qualify embed --device cpu \
  --model-dir "/path/to/embedding-model" --audio "/path/to/sample.wav"
```

`--model-dir` 또는 해당 stage의 `options.model_dir`와 로컬 `--audio`가 필요하며 align에는 해당 오디오의 정답 본문 `--text-file`과 지원 언어 `--language`(예: `ko`, `en`)도 필요하다. 정렬 적격성 측정은 언어가 없거나 지원되지 않으면 측정을 거부한다. `--device` 선택지는 `cpu`, `mps`, `mlx`이며 실제 backend가 지원하는 장치를 선택한다. 생략 시 해당 stage의 장치를 사용하며 기본값은 asr·align이 `mlx`, diarize·embed가 `cpu`다. `--backend`는 해당 측정의 ASR 선택자를 덮어쓰는 호환 옵션이며 기본값은 설정에서 선택한 ASR 모델이다.

명령은 실제 helper를 제한된 시간 동안 실행해 자원을 측정한다. 성공하면 data 디렉터리의 `qualifications/`에 측정 근거를 보관하고 자격 레코드를 출력한다. `settings.json`과 `helpers.json`은 쓰지 않는다. 전사에 사용할 모델·장치는 settings.json의 해당 stage에서 선택한다. 실패를 성공 자격으로 저장하거나 모델을 자동 다운로드하지 않는다. `--data-dir`를 지정했다면 이후 전사에서도 같은 경로를 사용한다.

측정 통과는 해당 모델·runtime·장치 조합의 자원 적격성을 뜻한다. 언어·전사 정확도·화자 품질 검증은 별도로 수행한다. 일반 `doctor`의 설정 파일 존재 표시만으로 적격성을 판단하지 않는다.

`resources.local`에서 로컬 자원 정책을 설정한다. 기본값은 전역 단일 helper, CPU 두 threads, 실행 전 여유 8 GiB 이상·정상 pressure·측정 peak 3 GiB 이하이며 실행 중 메모리 한도는 4 GiB다. 설정한 한도 초과·시스템 pressure·측정 누락·timeout은 helper를 중단시킨다. runtime·모델·장치가 달라지면 적격성을 다시 확인한다. helper 실패를 자동 재시도하거나 모델을 다운로드하지 않는다.

## Telegram

운영자가 설정과 webhook 상태를 확인한 뒤 명시적으로 `scribe bot`을 실행한다. 이 안내의 설치·smoke는 bot을 시작하지 않는다. `integrations.telegram.allowed_users`의 허용 사용자 ID 설정과 `token_env`가 참조하는 실행 환경 토큰이 필요하며 개인 대화만 접수한다. owner는 `telegram:USER_ID`이고 CLI의 `local` owner와 격리된다.

| 사용자 명령 | 동작 |
| --- | --- |
| URL 또는 오디오 파일 | 기본 API 전사·요약; 화자 처리는 명시 설정을 따름 |
| `/list`, `/status [JOB]` | 본인 작업과 전달 상태 |
| `/summary URL`, `/translate URL`, `/srt URL` | 해당 후처리·자막 요구 포함 |
| `/engine remote`, `local`, `captions` | 다음 작업 profile; SQLite에 유지 |
| `/speakers JOB` | 인물 후보 확인 |
| `/confirm JOB:SPEAKER 이름` | 인물 연결 명시 확인 |

update를 SQLite에 보관하고 작업 제출이 영구 저장된 뒤 offset을 전진시킨다. 재시작 시 queued·만료 running 작업과 대기 전달을 복구한다. 결과는 텍스트 미리보기와 문서로 보낸다. 입출력 파일 한도는 8 MiB이며, 초과 파일·부분 완료·시간 없는 SRT는 별도로 안내한다. 전송 후 응답 유실·프로세스 중단으로 성공 여부가 불명확해지면 outbox를 `unknown`으로 두고 자동 재전송하지 않는다. `/status JOB`에서 확인한다.

`Ctrl+C`로 polling을 중단하면 이미 실행 중인 작업은 남은 단계를 마치고 결과와 전달 outbox를 저장한다. 종료 신호 이후에는 다음 대기 작업을 시작하지 않는다. 미시작 작업은 SQLite의 queued/submitted 상태로 유지하며 다음 실행에서 복구한다. 종료 중 완료된 결과의 미전달 문서도 outbox에 남아 다음 polling 실행에서 전달할 수 있다.

기존 webhook이 활성화되어 있으면 polling은 시작을 거부한다. webhook 삭제·변경·운영 시작은 별도 승인 범위다. `scripts/deploy.sh`는 자격 증명 접근과 gcloud·curl 호출 전에 종료 코드 64로 중단한다. Cloud Run 자동 배포는 제공하지 않는다. 기존 운영 컨테이너와 webhook은 이 소스 변경으로 수정하지 않는다.

## 로컬 컨테이너 진단

Dockerfile은 공통 CLI `python /app/main.py`를 진입점으로 사용하며 기본 인자는 `--help`다. `main.py`, `src`·`bot`의 명시적 Python 소스, requirements를 이미지에 복사한다. 사용자 키·원본·DB·모델·캐시는 빌드 컨텍스트의 허용 대상이 아니다. 의존성 정본은 컨테이너에서도 `requirements/requirements.txt`다.

```sh
docker build -t open-scribe-cli .
docker run --rm --network none --read-only open-scribe-cli
docker run --rm --network none --read-only open-scribe-cli doctor
docker run --rm --network none --read-only open-scribe-cli models
```

이미지 빌드는 OS와 Python 의존성을 내려받아 설치한다. 모델 다운로드·추론·bot 시작은 빌드 단계에 포함하지 않는다. 위 실행 예시는 네트워크와 파일 쓰기를 막은 읽기 전용 preflight이며 모델 API를 호출하거나 SQLite를 초기화하지 않는다. 실행 중인 기존 컨테이너를 교체하거나 webhook을 변경하는 명령도 포함하지 않는다. Mac helper의 실제 GPU·메모리 적격성은 이 컨테이너 진단으로 대체하지 않는다.

## 검증 범위

```sh
source .venv/bin/activate
python -m unittest discover -s tests -p test_install.py
python -m unittest discover -s tests
```

설치 검사는 임시 HOME·prefix, 준비된 venv, 실제 core CLI를 사용한다. 키 처리는 합성 fixture만 사용한다. PowerShell 실행기는 별도 runtime이 있을 때만 실행 검증할 수 있으며, macOS 이외 플랫폼의 helper 적격성을 이 검사로 보증하지 않는다. 실제 전사 품질·장시간 GPU 메모리·외부 서비스와의 운영 전환은 별도 검증 대상이다.

655개 통과는 [동결 소스의 코드·mock 경계 검증](development/optional-modes-implementation.md)이다. 실제 설치본과 짧은 실경로 검사는 담당 F의 [릴리스 기록](archive/rework/optional-modes-release.md)에서 별도로 관리한다. 어느 결과도 정답/CER·실제 화자 정답·실명 대조 없이 품질 합격을 뜻하지 않는다. 문서의 JSON 예시 검증은 설정 스키마 검사이며 파일·모델 존재나 실행 자격을 부여하지 않는다.

후속 correct prompt·실패 진단 보존 패치 이후 전체 662개 검사와 새 SHA는 같은 통합 기록의 별도 이력이다. 이전 실제 실패의 원인은 raw 유실로 미확정이며, 새 코드 검사로 실제 자격이나 로컬 E2E 완료를 주장하지 않는다.

native format adapter 추가 후 새 동결 소스에서는 전체 671개가 통과했다. 단일 fence·명시 alias·reason 생략과 의미 검토 경로를 포함한 코드 검사이며, 과거 실패의 인과 확정이나 실제 qualification·정확도·실명 합격의 근거는 아니다.

## 필요할 때만 실행하는 로컬 UI

`scribe dashboard`, `scribe review open JOB`, `scribe speakers gallery`는 기본 브라우저에 로컬 UI를 연다. 에이전트 없이 직접 실행할 수 있다. 마지막 질문 후 종료 확인에서 ‘예’를 선택하면 저장 후 탭과 서버를 종료한다. 정상적인 탭 직접 닫기는 heartbeat 유예 후 서버를 종료한다. 평소에는 상주 서비스가 없다.

에이전트가 질문을 준비할 때는 `--questions FILE --events-json`을 사용한다. 저장 성공 이벤트의 실제 메모리 경로를 확인한다. 준비된 질문이 없으면 기본 검토 질문을 제공한다. [명령·저장 형식·제약](development/local-review-ui.md)을 참고한다.


## 명시적인 인증 파일

`settings.json`에서 공급자별로 환경변수 파일과 변수 이름을 지정한다. 키 값은 설정에 넣지 않는다.

```json
{"providers":{"openrouter":{"api_key_file":"/absolute/path/keys.env","api_key_env":"OPENROUTER_API_KEY"}}}
```

파일은 현재 사용자 소유이고 권한은 600이어야 한다. `NAME=value` 또는 따옴표로 감싼 한 줄
리터럴만 지원한다. 셸 명령과 변수 확장은 실행하지 않는다. 지정된 파일에서만 해당 키를 읽고,
다른 프로세스에 export하거나 Keychain으로 대체 조회하지 않는다. 파일을 지정하지 않으면
해당 프로세스 환경변수만 사용한다. `scribe auth status`와 `scribe doctor`는 유료 호출 없이
설정 상태를 확인한다. 기존 Keychain 항목은 자동 사용하지 않으며 삭제하지도 않는다.

기본 CLI 모드는 ASR 청크가 반환될 때마다 전사 본문을 즉시 출력한다. 출력은 후속 교정·정렬 전의 전사 초안이며 문맥용 중첩 구간이 포함될 수 있다. quiet 모드는 본문을 숨기고 CR 진행 표시만 유지한다. `--json`·`--no-stream`에서는 전사 초안을 출력하지 않는다. 이는 ASR 응답의 토큰 스트리밍이 아닌 청크별 출력이다.
