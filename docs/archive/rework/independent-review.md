# 최종 집중 독립 검토

> 역사 기록 — 아래 `최종`·PASS는 2026-11-05의 F11/F12/F15 등 당시 집중 범위를 뜻한다. 본문 지적·재현·검사 수·파일 SHA는 보존했으며 새 선택 모드의 최신 독립 검토로 전용하지 않는다. 현재 안내는 [문서 입구](README.md), 최신 동결 코드 검사 근거는 [통합 기록](../../development/optional-modes-implementation.md), 실제 릴리스 진행은 [담당 F 기록](optional-modes-release.md)을 따른다.

2026-11-05. **집중 검토 코드 범위 PASS. F11·F12·retry lease race·CLI 연결에 이어 F15의 ASR·텍스트 모델·effort 동결도 독립 확인했다. 현재 집중 범위의 blocking finding은 없다.** 실제 모델·GPU·HF 접근·운영 전환 관문은 코드 판정과 별도로 open이다.

## 최종 범위와 실행 제한

최종 통합 지시에 따라 F11·F12·retry lease race·CLI 연결·generic ASR ID/요율 metadata guard·RED runner 및 v2 계약에 집중했다. 추가 broad 리뷰나 전체 suite·반복 profile은 중단했다. 최종 F15 수정 후에는 요청된 최소 keyless background 재현만 실행하고 CLI·테스트 해시와 이 문서를 갱신했다.

`jstack:review`의 읽기 전용 검토를 유지했다. 제품 코드·테스트·계약·기존 Git 변경·`.agents`·삭제된 설치 스킬은 수정하지 않았다. 이 검토자가 저장소에 수정한 파일은 이 문서 하나다. 변이 검사는 요청된 runner를 **임시 복사본에서만** 실행했고 원본 바이트 복원을 확인했다.

실제 모델/API·공개 요율 GET·HF 인증·Telegram/Notion 발송·운영 배포·패키지 설치는 하지 않았다. 원본 HF token 값은 조회하지 않았다. HTTP/모델 경계는 대역이고, 실제 SQLite·ffmpeg·프로세스/스레드 경로를 사용했다. 비밀 파일 없는 소스 스냅샷과 최소 환경/임시 HOME에서 실행했다.

## F15 해결 확인

이전 F15는 키가 없는 background 제출에서 Router가 생성되지 않아 `asr/text_model/effort` 선택값이 모두 기본값으로 바뀌던 문제였다. `src/core/cli.py:208–213`에서 세 값을 Router 유무와 독립적으로 submit에 전달하는 수정이 반영됐다.

**독립 재현:** 실제 CLI 파서·Application·SQLite를 사용하고 config 경계만 임시 경로로 대체했다. 자격 증명이 없는 최소 환경에서 기본값과 다른 ASR ID·텍스트 모델·effort를 지정해 background 제출했다. 세 저장값이 요청값과 같은지, queued 상태인지, stage·cost 행이 없는지 assert했다.

```json
{"exit":0,"status":"queued","three_parameters_preserved":true,"stages":0,"costs":0}
```

검사 전후 CLI·테스트 파일 해시가 같았다. 실제 API·모델 조회/실행은 없었다. F15는 해결로 전환하며 새 blocking finding은 없다.

### 최소 확인 명령

실제 설정 파일을 읽지 않도록 config 모듈을 임시 경로로 대체한다. 제품 코드는 수정하지 않는다.

```sh
env -i PATH=/usr/bin:/bin:/opt/homebrew/bin PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout
from io import StringIO
import json, sys, types, wave
from src.core.cli import main
from src.core.provider import TEXT_MODELS, TEXT
from src.core.store import Store

with TemporaryDirectory() as d:
    config=types.ModuleType('src.config')
    config.Config=type('Config',(),{
        'BASE_PATH':Path(d)/'default',
        'DB_PATH':Path(d)/'default'/'db',
        'COPY_TO_DOWNLOADS':False})
    sys.modules['src.config']=config
    source=Path(d)/'source.wav'
    with wave.open(str(source),'wb') as w:
        w.setparams((1,2,16000,0,'NONE','not compressed'))
        w.writeframes(b'\0\0'*1600)
    state=Path(d)/'state'
    expected={'asr':'fixture/custom-stt',
              'text_model':sorted(TEXT_MODELS-{TEXT})[0],'effort':'high'}
    with redirect_stdout(StringIO()) as out:
        code=main([str(source),'--data-dir',str(state),
                   '--background','--no-downloads',
                   '--asr-model',expected['asr'],
                   '--text-model',expected['text_model'],'--effort',expected['effort']])
    job=Store(state/'transcription_jobs.db').job(out.getvalue().strip(),'local')
    assert code==0 and job['status']=='queued'
    assert {k:job['request'][k] for k in expected}==expected
    assert job['stages']==[] and job['costs']==[]
    print('F15 PASS: all three parameters preserved')
PY
```

## 집중 재검증 결과

| 대상 | 독립 실행 결과 |
|---|---|
| F11: submit이 먼저인 순서 | 첫 작업의 생성 WAV를 다른 owner의 queued 입력으로 등록하고 8일 경과를 재현했다. prune 후 bytes가 같고 queued job이 보존됐다. |
| F11: prune이 먼저인 순서 | digest 이후 durable 등록 직전에 실제 prune가 후보를 삭제하도록 순서를 제어했다. Store.submit이 missing input을 거부하고 DB job 수가 증가하지 않았다. 두 순서 모두 확인했다. |
| F12 | 실제 polling stop Event가 설정됐음을 확인한 뒤 첫 작업을 풀었다. 호출 1회, 상태는 `completed/queued`였고 두 번째 update는 submitted로 남았다. |
| F12 재개 | 명시적으로 work_once를 다시 실행한 뒤에만 두 번째 작업이 실행·완료됐다. 서로 다른 입력 bytes를 써 공유 캐시가 호출 누락을 감추지 않도록 했다. |
| retry lease race | 최초 읽기 직후 다른 worker가 claim하게 했다. reset transaction 안의 재검사가 거부했고 기존 결과가 남았으며 run은 호출되지 않았다. |
| CLI 연결 | 키가 있는 실제 CLI→Router→metadata GET 대역→POST 대역→SQLite→JSON export를 실행했다. 지정 ID가 요청과 저장소에 보존되고 종료 코드 0이었다. |
| generic ASR guard | 안전하지 않은 ID는 요청 0회로 거부됐다. 유효 형식이지만 audio가 아닌 metadata는 GET만 실행되고 POST 0회였다. |
| F15 | 키 없는 background 제출에서도 ASR·text_model·effort 세 선택값이 모두 보존되고 queued로 저장됨을 독립 확인했다. stage/cost 행은 0개였다. |

이전 문서의 “F11·F12가 남았다”는 판정은 폐기한다. 위 결과는 실제 실행 경로의 확인이며 상수·분기 존재만 확인한 것이 아니다. scope 밖의 누적 follow-up을 별도 broad 재검토 사이클로 다시 실행하지 않았다.

## RED runner 및 v2 계약

- `tests/red_check.py`를 원문으로 읽었다. 자기 작업 트리를 mutation root로 받지 않고, target symlink/경로 탈출/변이 위치 중복을 거부하며, baseline 성공 후에만 변이한다. 복원은 finally에서 수행한다.
- 서로 다른 임시 복사본에서 계약의 **10개 ID 모두** 실행했다. 각 baseline exit 0, mutation exit 1, `detected=true`였다. 매번 복사본의 원본 파일 해시가 복원됐음을 확인했다.
- 탐지 조건은 단순 nonzero가 아니라 `FAIL:`와 `AssertionError`를 요구한다. baseline 오류·timeout은 exit 2로 미결정 처리한다. REMOTE 변이도 `ProviderError`를 `UnknownOutcome`으로 착각해 통과시키지 않고 의미 검사에서 실패했다.
- `docs/rework/verification-contract.yaml`은 JSON으로도 파싱되는 YAML이며 요구 ID **10개**가 spec과 일치한다. 각 관련 목록 **79개**가 존재함을 확인했다. 변경 없는 legacy dependency closure를 RED 복사용으로 포함한 것이며, 사용되지 않는 legacy 내부를 새로 감사했다고 주장하지 않는다.
- 문서 계약과 `.jstack/tasks/open-scribe-rework-2026-11/contract.yaml`은 바이트가 같았다. 둘의 최종 SHA-256은 `4ae69da82cca744e39a97f41def2afca0432c22179b8f916262b4adf7d231626`다.
- 계약의 GREEN 명령 **10/10**이 종료 코드 0이었다. 이는 F15 수정 전 실행 결과다. 이번 F15 전용 재현으로 보완했으며, 수정 후 전체 GREEN/RED를 다시 실행했다고 주장하지 않는다.
- v2 초기화/preflight/brief 통과는 메인 보고다. 계약은 구현 후 만들어졌으며 **위임 전 관문이 실행됐다는 증거로 소급하지 않는다.**
- RESOURCE 묶음 명령의 wall time은 이 실행에서 33.798초/15.515초였다. 단일 파일 10초 반복 profile과 다른 합산 명령이고 경합 중 관측이므로 이를 per-file 성패로 전용하지 않았다. owner 통제 profile 최대 8.075초는 메인/owner 보고다. 추가 반복 profile은 요청대로 실행하지 않았다.

## 코드 verdict — 원래 10개 기준

아래 PASS는 이 집중 검토 및 기계 검사 경로의 코드 판정이다. 실제 모델·GPU·외부 운영 자격을 포함하지 않는다.

| 기준 | 코드 verdict | 실제 모델·운영 |
|---|---|---|
| CORE-01 | PASS — 정상 CLI/공용 Application 연결과 키 없는 background의 세 모델 설정 보존 확인. | 실제 Telegram 운영 전환은 미검증. |
| DATA-01 | PASS — F11의 등록/삭제 양쪽 순서, pin 보존과 관련 검사 통과. | 운영 DB 전체 불변을 주장하지 않음. |
| JOB-01 | PASS — F12 중단/명시 재개와 retry lease race 통과. | 실제 강제 종료·모든 외부 결과 복구의 전수 자격은 미검증. |
| REMOTE-01 | PASS — metadata guard·불확실 응답·RED 의미 검사 통과. | 실호출 성공은 메인 관측 보고, 독립 재호출 안 함. |
| SPEAKER-01 | PASS — 기존 코드 검사와 관련 GREEN/RED 통과. | 실제 화자 품질·로컬 모델 자격 open. |
| RESOURCE-01 | PASS — 관련 GREEN/RED 및 대역/프로세스 검사 범위. | 실제 모델 pressure/OOM/GPU peak 자격 open. |
| RESOURCE-02 | PASS — mutex·watchdog·종료 관련 검사/변이 탐지 범위. | 실제 모델 GPU 메모리 회수 실측 자격 open. |
| OUTPUT-01 | PASS — 구조 변환·원문 보존·최종 SRT 판정 관련 검사 범위. | 실제 모델 의미 정확도와 Notion 운영 게시 미검증. |
| BOT-01 | PASS — F12 해결 및 저장/owner/outbox 관련 GREEN/RED 범위. | 실제 polling/webhook 전환·전송은 실행하지 않음. |
| BUDGET-01 | 조건부 PASS — 로컬 예약·정산·receipt·격리 검사 범위. | 서버 과금 계약에 의존하며 하드 서버 지출 상한 자격은 없음. |

### 모델·운영 관문은 계속 open

HF 인증 200과 Community1 HEAD 403/GatedRepo, Luna 및 CLI 실호출 성공은 **메인 coordinator의 실행 관측 보고, 독립 재호출 안 함**으로 구분한다. token 값은 읽지 않았다. 인증 성공은 gated 모델 준비·실행·품질/GPU 자격을 의미하지 않는다.

공개 요율과 max_price/require_parameters의 효력은 서버 billing 계약에 의존한다. 서버가 견적을 위반해 이미 청구한 금액은 앱이 회수할 수 없다. actual/raw result 보존과 scope 사후 격리만 확인 범위다. 하드 spending cap을 위한 자격 증명·권한 변경은 하지 않았다.

legacy 읽기 전용 복사 검증의 “기존 74개 ID, 총 75개, 반복 동일”은 메인 보고다. 외부 원본 상태가 증가한 점을 반영하며, “운영 DB가 전역적으로 바뀌지 않았다”로 확대하지 않는다.

## 테스트 증거와 최종 소스 바인딩

- **F15 수정 전 메인 보고:** 전체 **241개 / 28.035초 / OK**, 당시 source unchanged.
- **F15 수정 후:** 검토자의 최소 독립 재현 PASS. CLI 4개 통과는 메인 보고다. 전체 242개 예정이라는 안내를 받았으나, 이번 검토에서 242개를 실행하거나 통과했다고 기록하지 않는다.
- **검토자 직접 실행:** 집중 재현 종료 코드 0, 계약 GREEN **10/10**, RED 탐지 **10/10**.
- 검토자의 전체 실행은 최종 설치 manifest 반영 전 스냅샷에서 **241개 중 240개 통과·1개 실패**였다. 실패는 `requirements.local.in` 미복사였다. 이는 코디네이터의 별도 복사본에서 발생한 `requirements.cloud.txt` 누락과 다른 관측이다.
- 최종 installer에서 `requirements.local.in/txt` 복사 항목이 추가됐음을 코드 비교로 확인했다. 그 최종 변경 이후 검토자가 전체 suite를 재실행했다고 주장하지 않는다. owner의 설치 23개 통과도 owner 보고로 구분한다.
- F15 갱신은 CLI 한 줄과 해당 테스트 추가에 한정했다. 두 파일의 새 해시를 아래 표에 반영했으며 나머지 해시는 유지했다. 추가 broad 리뷰·suite·profile·제품 코드 수정은 하지 않았다.

### 집중 검사 및 변이 재현 명령

```sh
.venv/bin/python -B -m unittest \
  tests.test_application.ApplicationTests.test_prune_pins_generated_audio_accepted_as_another_jobs_input \
  tests.test_polling.PollingTests.test_run_interrupt_finishes_current_job_without_starting_next \
  tests.test_regressions.ReviewRegressions.test_retry_cannot_clear_stage_if_job_claimed_after_initial_read \
  tests.test_cli.CommandTests.test_remote_command_runs_through_provider_storage_and_export -v

# RED_ROOT는 원본과 다른 완전한 임시 소스/테스트 복사본이어야 한다.
.venv/bin/python -B tests/red_check.py "$RED_ROOT" CORE-01
# 같은 방식으로 DATA/JOB/REMOTE/SPEAKER/RESOURCE-01/RESOURCE-02/OUTPUT/BOT/BUDGET의 10개 ID를 검사한다.
```

## 최종 파일 SHA-256

분리된 테스트 파일·RED runner·최종 설치 manifest와 두 계약 사본을 포함한다. 과거 스냅샷의 해시는 이 표에 혼합하지 않았다.

| 파일 | SHA-256 |
|---|---|
| `docs/rework/spec.md` | `c54d39f1414924e20637885c215165c5773be6f20cc4b2048f5c70bc0fecaff5` |
| `docs/rework/verification-contract.yaml` | `4ae69da82cca744e39a97f41def2afca0432c22179b8f916262b4adf7d231626` |
| `.jstack/tasks/open-scribe-rework-2026-11/contract.yaml` | `4ae69da82cca744e39a97f41def2afca0432c22179b8f916262b4adf7d231626` |
| `src/core/__init__.py` | `c61856b059ca6313b7ef378de0cf13fcc76b184230911b62f41843d77fc7409a` |
| `src/core/alignment.py` | `eebd5f19d611556a897a779107a578df5a06f2a573b0141719a617d6f8c3b75a` |
| `src/core/application.py` | `2bde5734129d760cb1474a94d6bcd6dda19508717b1ef271592466946755df96` |
| `src/core/cli.py` | `fe646d7eebe350a63a948e0ff4bdf368f7745a33679ac353d46d29e95dc5d3c4` |
| `src/core/context.py` | `94672cec06c3c21c514b1b5437ee15c691a3b05ee92bec9df639b7399de244c8` |
| `src/core/credentials.py` | `dc55b3f5b2f4b22667042dcc32f648ab9809fa11f2934688283beb184812ab7c` |
| `src/core/identity.py` | `481f61d71bdac46770cf5c367ee3df05b20b640c6b4da5872f76137ca0416505` |
| `src/core/local.py` | `d45427419b01255d8aa912b829aa943c40d23b59bc003d324af54ce592d45912` |
| `src/core/models.py` | `5e0c82d13448d603bd1a0d94cecd480714b34565f338d6dfab520107603bafe2` |
| `src/core/output.py` | `a5fa8992864e7361dd6f65523d57f43e65dae2f6df02f78fdc2cc660f67c7121` |
| `src/core/postprocess.py` | `f4f151f5ce50d20ba34ea22dc2e477c529ebce7436b9783bb89fb6b1e22cb07c` |
| `src/core/pricing.py` | `735c985e7b117ba3ffb790384ae828636152d846ae5f5aceef4594640c3f5a97` |
| `src/core/provider.py` | `a1e3e79009780063347140baefc9110149a09de91195f8ba8128904bc5b0a73a` |
| `src/core/resources.py` | `aac2e823a367cb50b224441fdaefe14c60e43015868adc1bdcbe17f7aeebf753` |
| `src/core/speakers.py` | `055064bb284c339cae654aa780be6885f8af8def5e2e62125cde359348aeda92` |
| `src/core/store.py` | `a8186fb4d109c36f865b11b9b5e1b4172887dc4deb33b2ce9a34bb15bc6215cd` |
| `bot/polling.py` | `b0377c44ec30e693aea4675a6bded6d6f18f5edda5f60e7b23c0cfc323893e30` |
| `bot/main.py` | `4e026bd2711e5ee9249ec5fdcc875ee65fa18487a6331da5257acfcc52af8b25` |
| `bot/telegram_bot.py` | `e8cac7f4409bc1dec5eb4fe351ce6c0d32819bccfd01d85c28f474f7ee7897e3` |
| `bot/transcribe_worker.py` | `673dc0b5fc11d9bfed89caf631fa178fe19635dcdd000ea06be41fe4075540ff` |
| `src/cli.py` | `21bc46748fcf3211c4eadbc6f87ed65157cf7e1cc75abccc4d3f6e398979ded4` |
| `src/config.py` | `56627a4df8d6b4ec3cf805670b995ecb0a1e67b3f540d3fabdc095f5adfc237b` |
| `main.py` | `1f5d89bbacfce044d807f54c1713d2b95ebe2fe0565eea28174c43d99c93e894` |
| `scribe.sh` | `bfeb2d47f4b5b9b3714dcc76eea0678179f9f43a291bafae6d3633ff281e6311` |
| `scribe.zsh` | `897ec4b8bd4f7f0abdac6ce42cf391039b572a101532104711d5778f8430be53` |
| `scribe.ps1` | `b5e432006ee7a5c7bb69d2371ca339cbce1506c41ce7890a65b08bca697e0834` |
| `scripts/install.sh` | `b40c24511acc760523bb4e39d1c1902cfc5b43a57f90b846904ef2a07d36ef4b` |
| `requirements.txt` | `553d8f54419a115fdccec70e365688f721ab635bfed49e4a7280d08cb4fbcf04` |
| `requirements.cloud.txt` | `4405e36c21306ca91e53f977c85b867ac7e8eb949d8d4b0fa899b96035864e14` |
| `requirements.local.in` | `ce05067a170da7b611004253363edb5d2353323596cac2bbc907ad08a0e85465` |
| `requirements.local.txt` | `89082a11549b0080a296bc22150089a5387a31ca953da43f5bdf29c24b482986` |
| `tests/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tests/red_check.py` | `67ae77931e92eb52298344a63fb36b433b376706183072aa2260fe3e4fae9cf9` |
| `tests/support.py` | `d738882ad82e76d4617f4f1019d03c89c8743190c0c34dc6a23de320a46267f1` |
| `tests/test_application.py` | `c941760272608b5f160d38e6f4a57895e18f02fdfc892a899d25b8baf3f8fb62` |
| `tests/test_cli.py` | `c6b75c877a0753f231f2001b77c0aefe8575d40d423b2502c1398c2c2cbb5be8` |
| `tests/test_identity.py` | `634b3353ab5f83defffe42fa7c40500961f209154b574aca8e87e18a01282de7` |
| `tests/test_install.py` | `7f7f70adae8c8f7ec5f371b1222af9fff811466daa7c7f7c941b9ed10e8d9370` |
| `tests/test_polling.py` | `016e99eaa8bfccb9e94e6043da4911737439fb2b7e31f7abd3c5e9fa5591a091` |
| `tests/test_pricing.py` | `0fff6e400375d9de0a9acd4ba5dc25fec99c5c7669d119abdb13726234b2c050` |
| `tests/test_provider.py` | `6c2fe6a157adf17ae213056a45e6707dffe4d5eb8e4f17d4abbfba96b6da09c4` |
| `tests/test_regressions.py` | `d32e3961d01bb60e027a7e52ee8e7f9c2e05dd1b47599caf4f1b9c93fa8f14dc` |
| `tests/test_resource_entry.py` | `0cae6d1411eac509addf52bc664489bc8ac79c1d37e456d333089adb02c1688c` |
| `tests/test_resource_lifecycle.py` | `ef28e24676a1972ed91d159cd88cd5fa9620919924a092af5e17be1e53ef2496` |
| `tests/test_resource_models.py` | `7f3a66a678bfac1ea8d95433732e37fc891df20ad32eee0380214eddcd9a3cbb` |
| `tests/test_resource_policy.py` | `50837fcd6d2b8bf37e12f39b306c44455f1fcb14a818e1bf03fe465e215cce96` |
| `tests/test_resources.py` | `847ee2cb701ea21171558af7dfe9321f17b9e00da0f705f79945707fff8609d3` |
| `tests/test_rework.py` | `278da4dd472925fde4e275ce542f1ed5405fb3bb0c07572bf19803a45d0bdf1d` |

문서 자체의 최종 해시는 최종 응답에 제시한다.

```sh
shasum -a 256 docs/rework/independent-review.md
```
