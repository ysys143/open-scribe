# 선택 파이프라인 통합 계약

> 이 문서에는 기능 계약과 당시 동결 소스의 경로·SHA·검사 기록이 함께 있다. 동결 기록의 파일 경로는 그 시점의 경로다. 현재 패키지 배치는 [현재 구조](../architecture.md)를 따른다.

담당 D의 통합 경계다. 기본 API 전사·요약과 로컬 기능 비활성화를 유지한다.
개인 설정, 키 파일, 설치본과 원본은 변경하지 않는다.

[문서 입구](../README.md) · [사용 안내](../user-guide.md) · [현재 구조](../architecture.md) · [담당 F의 릴리스 기록](../archive/rework/optional-modes-release.md)

| 담당 | 인터페이스 | 통합에서 보장하는 조건 |
|---|---|---|
| A | `run_relisten(transcript, source, folder, helper, stage, options) -> Transcript` | 원본과 분리한 입력 사본, `apply=False` 기본, 실패 시 API 결과 보존 |
| B | `RemoteDiarizer(router, model, provider_options).run(audio, seconds) -> {turns, metadata}` | 전체 원본 기준, 별도 `diarize:remote` 유료 stage, 설정·source 캐시 키 |
| C | `name_speakers(transcript, stage, router, options, video=None, context=None, folder=None) -> Transcript` | 화자 분리 후, 후보 전용 derived 결과, 영구 인물 레지스트리와 분리 |
| D | `router.speaker_names(payload, frames) -> candidate JSON` | structured outputs, 텍스트 20KB·최대 6장·프레임 전체 base64 2MiB, 공용 과금·동시성·native key 우선순위 |

`stage(name, settings, operation)`은 `Application._stage`로 연결한다. 유료 API
호출은 `diarize:remote` 또는 `speaker_names:*` 이름을 사용한다. 결과를 알 수 없는
호출은 자동 재시도하지 않는다. 원본 전사와 canonical 단어의 문자·번호·시간을
별도 화자 API의 전사문으로 덮어쓰지 않는다.

설정은 `stages.relisten`, `stages.speaker_names`, 기존 `stages.diarization`이다.
클라우드 화자 분리는 `provider=openrouter`, `model=elevenlabs/scribe-v2`,
`options.provider_options={"elevenlabs":{"diarize":true}}`로 선택한다.
기존 `provider=pyannote` 로컬 경로는 유지한다.

재청취 stage 모델 alias는 `qwen3-0.6b`이며 ASR은 `options.asr_backend`로
독립 선택한다. 경로는 `asr_model_dir`, `llm_model_dir`로 설정하고, `settings.defaults()`의 내장값은
`max_window_seconds=30`, `max_windows=32`, `max_tokens=512`,
`max_input_tokens=4096`, `apply=false`다. 로컬 자격은 ASR과 correct를
분리하며 correct의 실측 `qualified_prompt_tokens`를 확인한다.

A 모듈의 직접 함수 호출에서 `max_windows`를 생략하면 fallback은 6이다.
Application은 settings에서 병합한 32 또는 명시적 사용자 값을 전달하므로
두 경로를 같은 기본값으로 설명하지 않는다. [사용 안내](../user-guide.md)의
예시는 `max_windows=6`을 명시해 작업량을 제한한다. 현재 기본값 차이는
문서 정리에서 코드를 변경해 해소하지 않았다.

문서 대조 기준은 `settings.defaults()`·`settings.validate()`와 각 adapter의 입력 경계다.

| 항목 | 현재 기본값 또는 제한 |
|---|---|
| 기본 실행 | ASR·summary on, alignment/diarization/embedding/relisten/speaker_names off, translate/correct off |
| ASR 청크 | core 목표 30초·최대 45초, 좌우 문맥 2초, 최소 꼬리 5초, 읽기 최대 49초 |
| 재청취 | 창 최대 30초, 창 수 1~128; settings 내장 32·직접 함수 fallback 6·사용 예시 명시 6 |
| 교정 LLM | 기본 output 512 tokens·input 4096 tokens, 허용 output 최대 1024·input 최대 4096; 실측 prompt 자격 상한도 적용 |
| 이름 텍스트 | 요청당 JSON UTF-8 20,000바이트, 세그먼트 단위 배치; 단일 세그먼트 초과 시 거절 |
| 이름 프레임 | 기본·최대 6장, 전체 base64 최대 2,097,152바이트; 폭 720px 이하, 추출 timeout 기본·최대 10초 |
| 원격 화자 | 원본·실제 업로드 각각 최대 24MiB, adapter 길이 최대 10시간; upstream 처리 timeout 내 성공 보장은 아님 |
| 로컬 자원 기본 정책 | 전역 동시 helper 1, CPU 2 threads, 여유 8GiB, 자격 peak 3GiB, 실행 4GiB, poll 1초, timeout 120~900초·길이 계수 0.5 |
| 원격 자원 기본 정책 | 동시성 2(허용 1~2), 예산 10 USD, scope `validation` |

로컬 재청취는 후보를 `relisten/`에 내보낸다. 기본 `apply=False`이며 API 본문은
보존한다. 명시적 적용 결과는 기존 word alignment를 재사용할 수 없고 검토와
재정렬이 필요하다. 작업량 제한으로 빠진 모든 구간은 deferred/skipped 사유를
보관한다. 실제 모델 자격·정확도와 mock 경로 검증은 별개의 근거다.

Application의 canonical API 전사는 apply 설정과 무관하게 보존한다.
명시적 apply 결과는 `relisten/transcript.json`, 전체 교정 후보는
`relisten-derived.json`, 근거는 `relisten-raw.json`에 남긴다.
canonical metadata에는 `applied=false`, 파생 적용 여부는 `derived_applied`로
구분한다. 요약은 canonical 전사를 기준으로 한다.

공식 자격 진입점은 `doctor --qualify asr --relisten`과
`doctor --qualify correct --text-file ITEMS.json`이다. 둘 다 로컬 `--audio`가
필요하다. correct의 JSON은 `[{id,original,candidate}]` 배열이며 in-memory
측정 설정만 활성화한다. 사용자 설정 파일이나 설치본은 변경하지 않는다.

별도 화자 API는 24MiB를 넘는 원본을 변환 전에 거절한다. 29MiB 원본도
failfast하며 기존 ASR 결과는 보존한다. 허용 크기의 전체 소스를 16kHz mono
32kbps MP3로 넘기고 업로드 파일에도 24MiB 제한을 적용한다.
단일 요청 계약을 지키며 자동 분할하지 않는다. source 해시와
provider/model/options/encoding을 캐시 키에 포함한다. 원격 캐시 turns는
ASR 청크 계획에 넣지 않는다. 같은 소스의 불명확한 화자 과금 결과는 ASR·요약
모델 변경과 무관하게 재호출을 막는다. frozen OpenRouter 환경 변수 키를
다른 native 키나 자격 파일로 대체하지 않는다.

실명은 얼굴로 추정하지 않는다. 명찰·자막 OCR 및 사용자가 제공한 맥락의
출처를 가진 후보만 기록하며, 후보를 확인된 이름이나 영구 인물로 등록하지 않는다.

프레임은 `{id,time,mime_type,data}` 형태이고 data는 base64다. image_url은
Router wire에서만 생성하며 OpenAI에는 그대로 전달하고 Anthropic에는
base64 image source로 변환한다. 응답은
`{candidates:[{speaker,name,evidence:[{source,reference,quote}]}]}`다.
실제 유료 호출은 `speaker_names:0`, `speaker_names:1` 등이며
`derived:*`에 숨기지 않는다. 후보 sidecar는 `speaker_names/suggestions.json`이다.
`metadata.speaker_name_suggestions`에 suggested/contextual 상태를 남기고,
`metadata.speaker_names`에는 명시적으로 선택한 미검증 파생 표시만 쓴다.
확인 저장소·`named/`·manifest는 수정하지 않는다.

API correct는 공통 `provider.correction_change`로 숫자 및 모든 어휘 변경을
검토 후보로 남긴다. A도 같은 순수 함수를 import해 순환 import 없이 사용한다.
교정·번역에서 실제 바뀐 파생 segment는 words, start/end와 chunk 시간을
비우고 `transformation_requires_alignment`로 표시한다. 기존 유료 응답 캐시는
재사용하면서 파생 contract만 올려 구버전의 잘못된 SRT를 재사용하지 않는다.

검증 중간 근거:

- 최초 optional 검사 4개 RED: 설정 미등록, 클라우드 옵션 거절, Anthropic system 배열 오류.
- API 교정 RED 4개 검사에서 8개 하위 실패: 어휘 변조 적용, 이전 시간 재사용, 변경 없는 단어 정렬 삭제.
- `python -m unittest tests.test_optional_pipeline_modes tests.test_transform_guards -q`: 26개 통과. 임시 HOME/XDG 경로를 사용하고 키·토큰 환경 변수를 제거했다.
- 화자 라벨 없는 plain JSON 통합 실행: sidecar `reason=no_speakers`, 후보 0개, 이름 API 호출 0회, 유료 이름 stage 0개, 로컬 helper 0회.
- 교정 안전 함수와 클라우드·이름 유료 분류를 각각 무력화한 변이 3개: 3개 모두 탐지.
- 중간 전체 631개·650개 통과는 실행 중 source 변경이 발견되어 최종 근거에서 제외.

D의 아래 코드 검증에서는 유료 API·실모델 추론·모델 다운로드·실측 자격 생성을 수행하지 않았다.
전체 60분 정확도, CER, 실제 실명 확인을 합격으로 주장하지 않는다.
후속 실제 준비·릴리스 실행은 담당 F의 [별도 기록](../archive/rework/optional-modes-release.md)이 소유하며 이 문서가 완료 여부를 대신 판정하지 않는다.

이전 동결 검증(E 최종 경로 리뷰 수정 전)은 임시 HOME/XDG 경로 및 키·토큰 환경 변수를 제거한
subprocess에서 실행했다. 전후에는 src/bot/tests/scripts와 실행 파일·의존성
manifest의 SHA-256을 비교했다.

```text
.venv/bin/python -m unittest discover -s tests -q
Ran 652 tests in 138.851s
OK
SOURCE_CHANGED_DURING_TEST: []
ISOLATED_HOME_AND_CREDENTIAL_ENV: yes
```

`git diff --check`도 통과했다. 기능 통합 당시 D 변경 파일은 다음 14개였다.

- core: `settings.py`, `application.py`, `cli.py`, `provider.py`, `direct.py`, `store.py`, `postprocess.py`
- adapters: `bot/transcribe_worker.py`, `bot/polling.py`
- tests: `tests/test_optional_pipeline_modes.py`, `tests/test_transform_guards.py`
- docs: `README.md`, `docs/rework/user-guide.md`, `docs/rework/optional-modes-implementation.md`

E 최종 경로 리뷰 issue 2 보완:

- 실제 Router와 `httpx.MockTransport`로 유효한 이름 JSON 및 `usage.cost` 누락을 반환했다. 최초 두 RED 검사는 `UnknownOutcome` 미발생과 후속 요약 POST 발생을 각각 재현했다.
- `Router.speaker_names`는 후보 해석 전 `_billing.state=unknown`을 확인하고 raw result와 billing을 담은 `UnknownOutcome`을 발생시킨다. receipt·미정산 예약·orphan result를 보존하고 후보 파생 완료를 기록하지 않는다.
- Router 수정 뒤 같은 소스의 다른 작업에서 요약 POST가 발생하는 경로도 재현했다. `_stage`가 관련 작업의 미확정 과금을 발견하면 현재 실행의 후속 유료 호출도 차단하도록 수정했다.
- 실제 POST 수는 첫 실행 `ASR 1 + 이름 1`, 같은 작업 재개 후에도 총 2회, 같은 소스의 다른 작업을 실행한 뒤에도 총 2회다. 이름 sidecar·파생 전사·요약은 생성하지 않고 API 원문을 보존한다.
- 임시 HOME/XDG 및 자격 환경 제거 후 `.venv/bin/python -m unittest tests.test_optional_pipeline_modes tests.test_speaker_names tests.test_direct_providers tests.test_provider -q`: `Ran 89 tests in 10.183s`, `OK`.

두 blocking 수정 이후 최종 동결 검증:

- A의 relisten ASR 선택은 `options.asr_backend`를 사용한다. correct의 stage 모델 alias를 ASR alias로 재사용하지 않는다.
- primary ASR `diarize=true`와 standalone cloud diarization을 동시에 켠 90초 고정 입력에서 ASR 요청은 3회, standalone 요청은 1회였다. primary 옵션을 자동으로 끄지 않았다.
- 최종 단어 화자는 `[whole-A, whole-A, whole-B]`, `speaker_status=completed`이며 `cross_request_speaker_identity_unresolved` 플래그는 없었다. primary의 세 요청 provenance와 standalone의 단일 요청 provenance가 분리됐고 재개 시 추가 요청은 0회였다. 이 corner는 수정 없이 통과했다.
- 아래 전체 검사는 A/B/C 완료·동결 확인 후 한 번 실행했다. 임시 HOME/XDG와 PATH만 전달해 키·토큰 환경을 상속하지 않았다.

```text
.venv/bin/python -m unittest discover -s tests -q
Ran 655 tests in 147.256s
OK
SOURCE_FILES: 110
BEFORE_MANIFEST_SHA256: 4ce8b3d0c5bcc8dc2348a49526112a83631baa61c08d71d7caea7ab5ff9e198b
AFTER_MANIFEST_SHA256: 4ce8b3d0c5bcc8dc2348a49526112a83631baa61c08d71d7caea7ab5ff9e198b
SOURCE_CHANGED_DURING_TEST: []
ISOLATED_HOME_AND_CREDENTIAL_ENV: yes
```

manifest는 src/bot/tests의 Python 파일, scripts의 Python·shell 파일,
루트 Python·requirements·scribe 실행 파일·Dockerfile의 파일별 SHA-256을
상대 경로에 대응시킨 맵이다. 맵을 `json.dumps(sort_keys=True,
separators=(',', ':'))`로 직렬화한 뒤 SHA-256을 계산했다. 검증 결과를 기록하는
문서는 자체 해시 순환을 피하기 위해 manifest에서 제외했다.

상태: 두 blocking 수정 이후 동결 소스 전체 655개 통과, 전후 SHA 일치.
설치·배포·유료 실API 검증은 수행하지 않았다.
native `send_input` 도구가 현재 세션에 없고 `xsm list`에는 현재 세션만 보여
계약 조율은 메인에 전달했다. worker 소유 파일은 수정하지 않았다.

## 문서 정리 검증

현재 안내·구조와 역사 기록의 입구는 [README](../archive/rework/README.md)로 통합했다.
초기 spec·implementation-status·verification·independent-review·settings-unification·api-defaults는
상단에 역사 표시와 탐색 링크만 추가했다. 당시 본문·검사 수·실측·설치 증거는
현재 버전의 결과로 바꾸지 않았다. F 소유 릴리스 보고서는 수정하지 않았다.

개인 설정 접근을 막은 임시 HOME/XDG 환경에서 `Settings.load`를 실패하도록
대체하고, 아래 JSON 예시를 추출해 `settings.validate`와 `Settings(data, path=임시경로)`를
실행했다. 기본값도 같은 `defaults()`에서 대조했다. API 호출·모델 검사·개인 설정
읽기는 없었다.

| 문서·JSON 블록 | 설정에 병합한 위치 | 결과 |
|---|---|---|
| user-guide #1: 로컬 ASR | `stages.asr` | PASS |
| user-guide #2: 재청취, 명시적 `max_windows=6` | `stages` | PASS |
| user-guide #3: ASR + 별도 Scribe | `stages` | PASS |
| api-defaults #1: 당시 로컬 off 예시 | settings 루트 | PASS; 역사 예시의 현재 스키마 호환만 확인 |

speaker-names의 frame/candidates 2개, composite-api의 결과 1개,
independent-review의 결과 1개 JSON은 설정이 아닌 wire/결과 예시다.
이 네 개는 JSON 구문만 검사했으며 settings 검증이나 실제 API 성공으로 세지 않는다.
현재 기본값·상한을 대조하고 창 수/길이·토큰·프레임·추출 timeout·동시성의
범위 초과 설정 9개가 모두 `validate`에서 거절됨을 확인했다.
11개 문서에서 내부 파일 링크 87개를 검사해 누락은 0개였다.

문서 정리 전 source manifest는 110개 파일·
`4ce8b3d0c5bcc8dc2348a49526112a83631baa61c08d71d7caea7ab5ff9e198b`로
위 655개 동결 검증 소스와 같았다. 정리 후에도 같은 SHA였고 변경 파일은 0개였다.
제품 코드·테스트를 바꾸지 않은 문서 작업이므로
전체 655개 검사를 반복하지 않았다. 실제 실행·설치·릴리스·품질 판정은 각각의
증거와 담당 F 기록에서 별도로 확인한다.

## correct prompt·실패 진단 보존 패치 이후 동결 검증

이 절은 A의 후속 네 파일 패치 이후 새 동결 소스의 코드 검증이다.
앞의 655개 통과와 그 manifest는 해당 버전의 이력으로 보존한다.
새 검증 전 두 제품 파일의 SHA-256이 메인에서 전달한 A 최종값과 같음을 확인했다.

| 제품 파일 | SHA-256 |
|---|---|
| `src/core/local.py` | `9d916e0482a7356cb2a5966d87951f621d961a92ade18259afea2542da7aedc8` |
| `src/core/resources.py` | `8b606ba8d507374de320566bc4661601479c813ade51c14dd91c0d9189ab7af2` |

이전 655개 동결본과 달라진 파일은 위 두 제품 파일과
`tests/test_relisten.py`, `tests/test_relisten_resources.py`뿐이다.
`src/core/settings.py`는 바뀌지 않았고 기본 모델·API only·선택 기능 off를 유지한다.
D는 제품 코드나 테스트를 추가 수정하지 않았다.

이번 전체 검사는 요청에 따라 한 번 실행했다. 추가 테스트를 포함하며,
임시 HOME/XDG와 PATH만 전달해 API 키·토큰·개인 설정을 상속하지 않았다.
manifest의 파일 범위와 직렬화·SHA 계산 방식은 위 655개 검사와 같다.

```text
.venv/bin/python -m unittest discover -s tests -q
Ran 662 tests in 143.356s
OK
SOURCE_FILES: 110
BEFORE_MANIFEST_SHA256: accbd7a7809237b7c8622e59f6a4d6d244ddbbf1206786d67fbcfcfc7afd4b77
AFTER_MANIFEST_SHA256: accbd7a7809237b7c8622e59f6a4d6d244ddbbf1206786d67fbcfcfc7afd4b77
SOURCE_CHANGED_DURING_TEST: []
ISOLATED_HOME_AND_CREDENTIAL_ENV: yes
FULL_SUITE_RUN_COUNT_THIS_REQUEST: 1
```

이전 실제 correct 측정은 메인 전달 기준 prompt 576·generation 194·상한 512·
finish stop이었으나, raw 유실로 syntax/schema/ID 중 어떤 실패였는지 확정하지
못했고 qualification 0·로컬 E2E 보류로 기록됐다. 그 관측과 F의 기존 실패
이력은 새 코드 검사 결과로 덮어쓰지 않는다. prompt 예시·오류 분류·private
실패 진단 보존 경로의 보강만으로 그 실측 실패의 인과를 확정할 수 없다.

662개 통과는 코드·mock 경계 검증이며 새 실제 qualification·정확도·실명 확인의
근거가 아니다. A에게 별도 허가된 실제 correct probe와 E의 독립 리뷰 결과는
이 전체 검사에 포함하지 않았다. F 소유 릴리스 문서는 수정하지 않았다.

## native format adapter 추가 요청 당시 상태

메인 전달에 따르면 후속 실제 probe의 raw에서 완전한 단일 JSON fence 안의
`{corrections:[{id,text}]}`와 ID 일치·reason 생략 표현을 확인했다. 이는 이전
raw 유실 표본의 syntax/schema/ID 실패 원인을 소급해 확정하는 근거가 아니다.
기존 qualification 0·실패 증거는 보존한다.

A에게 명시 wrapper/alias만 수용하는 정식 adapter 보강이 요청됐다. 없는 reason은
`not_supplied`와 검토 상태·raw provenance로 남기고, 임의 복구·부분 extract·추가
prose·중복 ID·ID 변경은 거절하며 의미 보존 guard는 유지하는 요구다.
이 요구를 이 문서 기록만으로 구현 완료나 검증 통과로 표시하지 않는다.

앞의 662개·`accbd7a7809237b7c8622e59f6a4d6d244ddbbf1206786d67fbcfcfc7afd4b77`
전체 검사는 native format adapter 추가 전 버전의 중간 근거다. A 수정 뒤 E 리뷰와
새 source freeze/full 검증이 필요하다. D는 이번 지시 이후 제품 코드 변경·추가
전체 검사·실제 추론·설치를 수행하지 않았다. 사용자 지시상 최종 제품 설치는
보류하고 F의 추론 중지를 유지한다. F 소유 릴리스 문서는 변경하지 않는다.

## native format adapter 동결 후 전체 검증

후속 A 패치의 세 제품 파일 SHA-256을 메인 전달값과 대조해 모두 일치함을 확인했다.
이전 662개 동결본과 비교해 바뀐 파일은 아래 세 제품 파일과
`tests/test_relisten.py`, `tests/test_relisten_resources.py`의 다섯 개뿐이다.
`settings.py`는 바뀌지 않아 기존 모델·API only·선택 기능 off를 유지한다.
D는 제품 코드·테스트를 수정하지 않았다.

| 제품 파일 | SHA-256 |
|---|---|
| `src/core/local.py` | `841483129557b20124e0e374b8eee501f3536c2237d4b1e8f98bee3ebbb4fe66` |
| `src/core/resources.py` | `d343fc0af939afc3bd5eee74fd16ab0baa2bc0897ff53bb901e7e2c050a7d14b` |
| `src/core/relisten.py` | `d015f719563bdf3d0708fd2a0198b9815af9ff84456c6720c31e0bfef4fd1a00` |

현재 로컬 correct adapter는 완전한 단일 JSON 객체 또는 추가 prose가 없는
단일 `json` fence만 허용한다. 최상위 `corrections`와 명시 alias `segments`를
구분해 정규화하고 raw·`format_observation`을 보존한다. JSON 수선·부분 추출·
중복 키/ID·요청과 다른 ID/순서는 거절한다.

reason이 없으면 `not_supplied`와 `reason_source=absent`를 기록하고
`semantic_review_required=true`로 남긴다. 이는 decoder·구조 검증 실패와
구분한다. 자원 자격 판정이 가능하더라도 의미 검토를 대신하지 않으며,
`apply=true`나 문장부호 변경에도 의미 검토가 필요한 후보는 자동 적용하지 않는다.
숫자·부정·고유명사 등의 어휘 변경을 막는 의미 보존 guard도 유지한다.

추가 테스트를 포함한 전체 검사를 한 번 실행했다. 임시 HOME/XDG와 PATH만
전달했으며 manifest 범위·계산 방식은 앞선 동결 검사와 같다.

```text
.venv/bin/python -m unittest discover -s tests -q
Ran 671 tests in 146.201s
OK
SOURCE_FILES: 110
BEFORE_MANIFEST_SHA256: b084f1f757fdf3f1a5283313f8183eabda93483adb9c786e1d3c9dbf48ae4247
AFTER_MANIFEST_SHA256: b084f1f757fdf3f1a5283313f8183eabda93483adb9c786e1d3c9dbf48ae4247
SOURCE_CHANGED_DURING_TEST: []
ISOLATED_HOME_AND_CREDENTIAL_ENV: yes
FULL_SUITE_RUN_COUNT_THIS_REQUEST: 1
```

671개는 이 소스의 코드·mock 경계 검증이다. 기존 655개·662개와 이전 실제 실패·
qualification 0 증거는 해당 버전·표본의 이력으로 유지한다. 이번 D 검증에서
추가 실제 probe·설치·실모델 자격 생성은 수행하지 않았으며, 과거 실패 원인이나
실제 정확도·실명을 확정하지 않는다. E의 동시 독립 리뷰는 이 결과에 포함하지
않는다. 제품 최종 설치 보류와 F 추론 중지 지시는 유지되며 F 릴리스 문서는
수정하지 않았다.
