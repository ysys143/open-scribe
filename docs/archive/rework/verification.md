# OpenScribe 개편 검증

> 역사 기록 — 2026-11-05 초기 개편 검증이다. 아래 242개 검사, 실행 시간·SHA·실제 호출·표본·남은 관문은 당시 소스에 한정된다. 현재 전체 검사 수나 실제 품질 합격으로 소급하지 않는다. 현재 안내는 [문서 입구](README.md), 655개 동결 코드 검사와 SHA는 [통합 기록](../../development/optional-modes-implementation.md), 실제 준비·설치·짧은 실행·릴리스는 [담당 F 기록](optional-modes-release.md)에서 확인한다. 본문 증거는 변경하지 않았다.

2026-11-05 KST. 최종 동결 소스의 격리 전체 검사 **242개가 28.684초에 통과**했다. 실제 화자 모델/GPU 자격과 Telegram 운영 전환은 미완이다.

## 검증 방법

공통 CLI와 Application·SQLite·ffmpeg·파일 출력·자식 프로세스를 실제 실행한다. 외부 HTTP와 ML 추론 경계는 단위·통합 검사에서 대체한다. 원본·키·운영 DB에 테스트 fixture를 기록하지 않으며 설치 검사는 임시 HOME/prefix를 사용한다. 별도 실제 OpenRouter 호출은 승인된 10달러 원장에서 관리했다.

승인 기준 10개는 [명세](spec.md)와 [실행 계약](verification-contract.yaml)에 대응한다. [변이 검사](../../../tests/red_check.py)는 임시 복사본의 정상 검사가 먼저 통과해야 하며, 그 뒤 의도적 결함을 넣어 같은 검사가 실패해야 통과한다. import 실패·누락 fixture를 검출 성공으로 인정하지 않는다.

최종 suite는 소스·테스트·설치 fixture 84개를 복사하고 빈 HOME/config 및 읽기 전용 기존 venv를 사용했다. 키·실제 오디오·모델·운영 DB는 복사하지 않았다. 실행 전후 원본 작업 트리의 해당 84개 파일 hash가 같았다.

```text
.venv/bin/python -B -m unittest discover -s tests -v
Ran 242 tests in 28.684s
OK
```

처음의 격리 실행은 복사 목록에 `requirements.cloud.txt`를 빠뜨려 241개 중 설치 검사 1개가 오류였다. fixture만 보완해 전체를 다시 실행했다. 코드나 assertion을 완화해 통과시킨 것이 아니다. 이전 실패 로그는 `/tmp/open-scribe-rework-execution/tests-fixture-missing.txt`, 최종 로그·입력 hash는 같은 디렉터리의 `tests-final.txt`·`final-suite.json`이다.

승인 기준별 deliberate mutation 10개는 모두 검출했다. 기존 입력 pin 제거, checkpoint 재사용 제거, 502 확정 실패 오분류, 겹침 강제 화자 부여, 저메모리 허용, OS mutex 해제, 원문 일부 유실, Telegram owner 우회, 비용 예약 한도 우회를 포함한다. 원래 tree에는 변이를 적용하지 않았다.

추가로 121초/두 청크의 두 번째 청크를 한 번 실패시켜 partial 저장을 확인했다. 명시적 재개에서 ASR 호출 offset은 `[0,120,120]`으로 성공 청크를 재사용했다. 재시도 초기화와 다른 worker claim의 경쟁은 실제 실패를 먼저 확인한 뒤 트랜잭션 안의 lease 재확인으로 통과시켰다.

독립 검토 F15는 키 없는 background 접수에서 명시적 모델 선택이 기본값으로 바뀌는 결함이었다. 영향 범위를 조사해 ASR·텍스트 모델·추론 강도 세 설정이 Router 생성에만 연결된 것을 확인했다. 새 회귀 검사를 먼저 실패시킨 뒤 submit에 세 값을 직접 전달했다. CLI 4개 검사와 최종 전체 242개 검사가 통과했다. 앞선 241개 통과를 이 수정의 증거로 쓰지 않는다.

[최종 독립 검토](independent-review.md)는 F11/F12·실행권 경쟁·CLI 연결·F15를 직접 재현해 수정 효과를 확인했고, 코드 범위 PASS로 판정했다. 실제 모델·GPU·운영 관문은 승인하지 않았다. native 전달은 `reviewer-delivery.json`, 구현 담당자의 전달은 `worker-deliveries.json`으로 보존했다. 이 기록을 사전 승인 증거로 확대하지 않는다.

`git diff --check`, Bash/zsh 문법 검사는 종료 코드 0이었다. oracle guard는 HEAD에 추적된 변경 테스트가 없다고 보고했다. 새 테스트는 아직 untracked이므로 이 결과를 assertion 강도 증거로 쓰지 않는다. 별도의 변이·통합 검사와 독립 검토가 그 근거다.

## 검사 시간과 반복 안정성

최초 자원 검사 파일은 16.2초로 10초 예산을 넘었다. 테스트 95개와 assertion을 보존해 자원 관련 파일 5개로 분리했다. 이때 `ProcessTests`의 기존 변이 검사 경로도 유지했다.

전체 suite와 동시에 돌린 반복 프로파일은 두 파일이 10초를 초과했다. 이를 통과로 처리하지 않았다. 다른 전체 suite를 끝낸 뒤 같은 예산으로 분리 실행한 최종 결과는 **14개 파일 각각 5회, 위반 0, flaky 0, waiting 0, 최장 8.896초**다. 성능 측정과 전체 suite가 서로 자원을 경쟁하지 않도록 실행을 분리했다.

이 14개 파일 측정은 F15 직전 소스다. F15 후 변경된 CLI 검사 파일은 2초 예산으로 5회 다시 측정해 위반·flaky·waiting 없이 통과했다. 변경되지 않은 자원 검사 파일의 과거 측정을 수정 후 전체 재측정이라고 표시하지 않는다.

```sh
node "$JSTACK_PLUGIN_ROOT/skills/verify/scripts/test_profile.js" \
  --cmd '.venv/bin/python -B -m unittest -q {file}' \
  --max-seconds 10 --fail-on-waiting --repeat 5 --workers 4 \
  --json /tmp/open-scribe-rework-execution/test-profile-controlled.json 'tests/test_*.py'
```

`test_smells`의 sleep 탐지 7건은 중복 2건을 포함한 자식 payload 5개 위치다. SIGTERM 무시·watchdog·OS 잠금 해제를 재현하기 위해 오래 살아 있는 자식을 만들고, 검사에서 종료·회수를 관측한다. 본문 테스트가 60/120초를 기다리는 구조가 아니다. 탐지를 숨기거나 시간 예산을 높이지 않았다.

## 승인 기준 대조

F15 수정 뒤 실행 계약을 다시 검증해 **정상 10/10, 변이 10/10, 독립 검토 영수증 10/10, 입력 hash 안정**을 확인했다. `workflow.js status`는 `complete=true, problems=[]`를 반환했다. 이는 아래 코드 검사 범위의 완료이며 실모델·운영 출시 완료가 아니다.

| 기준 | 코드 검사 | 실제 모델·운영 관문 |
| --- | --- | --- |
| CORE-01 | PASS — 공통 Application, 실제 CLI→HTTP 대역→SQLite→export, 키 없는 설정 동결 | 실제 Telegram 운영 전환은 별도 |
| DATA-01 | PASS — legacy migration, 원본 보존, 다른 작업 입력 pin | 운영 DB에 테스트 자료를 쓰지 않음 |
| JOB-01 | PASS — 실패 청크 partial·재개·실행권 경쟁·중단 | 미확정 외부 결과는 자동 재호출 금지 |
| REMOTE-01 | PASS — capability/요율 guard·응답·truncation·미확정 비용 | 실제 표본 품질 인증은 아님 |
| SPEAKER-01 | PASS — 겹침·미상·명시 확인·원문 hash·등록/삭제 | 실제 분리/재식별 품질 미완 |
| RESOURCE-01 | PASS — admission·실측 증거·telemetry·timeout·원격 보존 | 실모델 OOM/GPU peak 미검증 |
| RESOURCE-02 | PASS — 전역 mutex·watchdog·후손/부모 종료 | 실모델 GPU 메모리 회수 미검증 |
| OUTPUT-01 | PASS — 원문 보존·동일 ID·시간 출처·파생 출력 | 실제 Notion 게시 미실행 |
| BOT-01 | PASS — 영속 ack·owner·outbox·종료 후 새 작업 차단 | 실제 polling/webhook 전환 미실행 |
| BUDGET-01 | PASS — 예약·정산·raw 보존·과대청구 격리 | 서버 과금 계약의 한계 유지 |

검증 영수증은 `.jstack/tasks/open-scribe-rework-2026-11/receipts/20261104T220916.008Z-8f481158-189d-4339-8110-535beab594e6.json`에 있다. 사용자 요청 전체의 기록은 실모델·운영 관문을 미완으로 남긴다.

## 실제 외부 호출

`/tmp/open-scribe-rework-validation/transcription_jobs.db`를 읽기 전용으로 집계했다. 실제 호출 8회, 정산 합계 **$0.001239447**, 미정산 예약 $0이다. Luna·Haiku 5.5·DeepSeek Flash의 텍스트 응답, Nemotron 전사와 구조화 번역을 확인했다. 키는 canonical 파일을 source하는 하위 프로세스에만 주입했고 값을 기록하지 않았다.

합성 영어 음성의 Nemotron 결과에는 단어 시간이 있었고 화자는 없었다. 인식 오류와 부정 표현 오류도 관측했다. 이 표본을 한국어 품질이나 화자 분리 인증으로 사용하지 않는다. 실제 CLI 작업 `a1834f4748dc43eabe906a94ade10d0e`는 당시 소스에서 `--no-speakers --no-downloads --json`으로 완료했고 전사·요약 파일을 저장했다. 최종 소스의 CLI 연결은 별도의 모의 HTTP 통합 검사로 확인한다.

공개 endpoint 요율, 사전 예약·정산·격리는 앱 수준의 보호다. 공급자가 이미 계약을 위반해 청구한 금액을 앱이 되돌리지는 못한다. 서버 키 spending cap·권한은 변경하지 않았다.

## 기존 데이터 표본

운영 DB는 읽기 전용으로 열고 임시 복사본에만 Store를 적용했다. 최신 표본에서 기존 `transcription_jobs` 74개 ID 전부가 복사본의 legacy import에 남았고, 전체 core 행은 첫 개방·두 번째 개방 모두 75개였다. 원본에는 검사 전부터 v3 테이블과 별도 실패 작업이 있었다. 원본에 없는 새 migration을 수행한 표본처럼 설명하지 않는다.

처음의 단순 총계 동등성 검사는 기존 core 작업까지 합쳐 실패했다. 전체 영향은 검사용 임시 복사본이며 원본은 읽기 전용이었다. 이후 legacy ID 전수 비교와 재개방 전후 전체 행 수 비교로 고쳤다. 최초 migration의 백업 생성은 별도 새 DB fixture에서 검증한다.

## 남은 관문

- 실제 로컬 모델/GPU 자격: 미완. HF 인증은 성공했지만 gated 모델 config 접근은 403/GatedRepo였다. 약관·접근 권한·token scope 중 원인을 확정하지 않았다. 모델 가중치를 내려받거나 계정 동의·권한을 바꾸지 않았다.
- 실제 모델별 한국어 전사·화자 분리·재식별 품질, 긴 오디오에서의 peak와 GPU 회수: 미검증. 모의 ML API와 실제 OS 프로세스 검사는 이를 대신하지 않는다.
- Telegram polling/webhook 전환·실제 Telegram/Notion 게시·운영 설치·배포: 미실행. 임시 설치 및 모의 HTTP 검증 결과만 있다.
- PowerShell 실행: 실행기가 없어 정적 검토만 수행했다. macOS Bash/zsh 결과를 Windows 실행 증거로 쓰지 않는다.

로컬 모델 접근과 준비 후 명시적 `doctor --qualify` 및 실제 품질 검증을 다시 수행하는 주체는 사용자와 구현 담당자다. 운영 전환은 webhook 상태·롤백을 확인하고 별도 승인한 뒤 수행한다. 현재 이 관문들은 완료로 표시하지 않는다.
