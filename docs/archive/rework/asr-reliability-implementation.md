# ASR 복구 구현·실행 기록 — 2026-11-05

코드 수정과 설치를 반영했고, 실제 선정용 비교 32건을 보존했다. 검수된 기존 녹취본은 없다고 사용자가 확인했다. 정답 0/12이므로 CER·모델 선정·정확도 합격은 미완이다. 이 기록은 [복구 계획](asr-reliability-plan.md)의 구현 검증과 음성 정확도 검증을 구분한다.

## 구현한 경로

- `settings.json → Application → Router/Helper`에 ASR decoder·청크 옵션을 연결했다. 기본 core 30초, 최대 45초, 문맥 좌우 2초, 최소 꼬리 5초이며 시간 정렬 입력은 최대 49초다. 기존 설정 파일에 없는 새 항목도 검증된 기본값으로 병합한다.
- Qwen에 native 언어명·temperature·max_tokens·repetition_penalty를 전달한다. Whisper는 native config/weights와 별도 alignment_heads·processor를 검증하고 단어 시간을 요청한다. 종료 이유·상한·실제 전달한 옵션을 보존한다. 원격 STT에 지원을 확인하지 않은 decoder 인자를 전달했다고 주장하지 않는다.
- 원출력, canonical 본문, 시간·화자 연결, 품질 플래그를 보존한다. 문맥 ownership에 쓸 시간이 없거나 비단조이면 본문을 남기고 검토 대상으로 표시한다. 숫자·소수점·부정문을 버려 정렬률을 높이지 않는다.
- 빈 응답에는 VAD와 에너지의 무음 근거를 함께 요구한다. 불명확한 빈 응답·토큰 상한·반복·본문/단어 불일치는 정상 전사로 승격하지 않는다. 음성 없음 판정과 실제 ASR 본문이 충돌하는 경우도 검토 항목이다.
- 실제 화자 구간의 교집합과 순차 화자 전환을 구분한다. canonical 본문에 대응하는 단어만 확정 화자에 연결한다. 미해결 구간을 요약의 확정 근거로 쓰지 않으며, 전 구간이 미해결이면 요약 호출을 보류한다.
- 평가기 보고서도 유효 lease를 가진 실행자만 트랜잭션 안에서 원자적으로 저장한다. 미확정 과금은 예약 상태를 유지하고 새 요청을 막는다. 정답·필수 발언 검수·CER 관문을 우회한 선정/보류 실행을 거절한다.
- 설치 업그레이드는 이전 런타임의 배포판 metadata로 로컬 의존성 설치 여부를 확인하고 hash lock을 보존한다. 모델 다운로드·키 파일 로딩은 설치와 실행에 추가하지 않았다.

## 독립 검토에서 재현하고 수정한 결함

| 결함 | 수정 전 경로 | 수정 후 검사 |
|---|---|---|
| R1 부정문 누락 | 전체 본문과 불일치하는 일부 segment를 전체 결과로 재구성 | 본문 보존, needs_review, 확정 요약 차단 |
| R2 빈 토큰 상한 응답 | 빈 결과의 decoder metadata가 합산에서 누락 | 원래 metadata 보존, rejected, 무음 승격 금지 |
| R3 전역 반복의 요약 유입 | segment ID가 없는 품질 문제를 summary가 무시 | 위치를 확정할 수 없으면 해당 전체 결과의 확정 요약 보류 |
| R4 만료 worker의 보고서 덮어쓰기 | report 저장 후 finish 단계에서만 lease 검사 | 저장 전에 동일 트랜잭션으로 실행 소유권 확인 |
| 실제 CLI의 단일 청크 자막 누락 | `--no-speakers --srt`에서 정렬 조건이 화자 요청에만 연결됨 | 자막의 미확정 시간도 정렬 조건에 포함; 원격 화자 라벨 유무 두 경우 모두 검사 |

비단조 단어 시간으로 부정문 순서가 바뀌는 경우도 원문을 보존하는 회귀 검사로 확인했다. 독립 검토자는 R1–R3 및 비단조 시간 사례 4개를 다시 실행해 통과를 확인했다.

## 검증 근거

| 항목 | 명령·증거 | 결과 |
|---|---|---|
| 전체 회귀 | 격리 HOME에서 `.venv/bin/python -B -m unittest discover -s tests -v`; `/tmp/scribe-asr-verified-release-check.log` | 500개, 120.570초, OK |
| 실행 중 코드 변경 검사 | `/tmp/scribe-asr-verified-release-inputs.json`의 전후 SHA 비교 | stable=true, exit=0 |
| 기존 필수 경로 결함 변이 | 별도 복사본에서 `tests/red_check.py RED_ROOT REQUIREMENT`; `/tmp/scribe-asr-mutations.json` | 10/10 baseline 성공·의도적 결함 실패 탐지 |
| native adapter 실제 호출 | 현재 코드와 설치된 ML 의존성의 정식 Helper; `/tmp/scribe-native-asr-production-check.json` | Qwen 0.6B·Whisper turbo 성공, 정상 종료 및 자동 품질 검사 통과 |
| 원격 시간 정보 탐침 | 7초 합성 음성, `verbose_json` 및 단어 시간 명시 요청; `/tmp/open-scribe-rework-validation/format-probe-results.json` | Nvidia·Scribe 각각 단어 18개 반환 관찰 |
| 설치본 소스 | 테스트 해시 목록의 `src/`·`bot/` 파일과 설치본 바이트 대조 | 불일치 0 |
| 설치 설정 | `~/.local/bin/scribe config validate` | valid=true |

최종 전체 회귀는 한국어 tokenizer 의존성·버전 추적, 단일 청크 SRT 분기, 길이 0 정렬 보존까지 포함한다. 앞선 496개 회귀 이후 한국어 tokenizer 관련 검사 두 개를 추가해 수정 전 모두 실패함을 확인했고, 수정 후 관련 검사 66개가 통과했다. 실제 CLI에서 확인한 SRT 분기에는 회귀 검사 한 개(원격 화자 라벨 유무 두 경우)를 추가해 RED를 확인하고 수정 후 관련 33개 및 최종 전체 500개가 통과했다. `tests/red_check.py`의 화자 변이 문자열도 확장된 품질 조건에 맞춰 수정하고 해당 baseline/변이를 다시 실행했다. 제품 코드는 최종 전체 회귀 당시와 동일하다. native 긍정 대조군은 영문 합성 음성이며 CSNL 한국어 정확도 증명이 아니다. 원격 시간 탐침은 단일 관찰이며 모든 endpoint가 항상 지원한다는 보장으로 승격하지 않았다. JSON으로 수행한 32건에 단어 시간이 있었다고 소급하지 않는다.

## 실제 선정용 비교와 검수 자료

원본 SHA256은 `21c83147f5c93cd35376e882f89ae07c3c699fd035a4218a845608d3d9d4b39b`다. 고정 묶음은 12개·480초이며 선정용 8개와 보류용 4개로 나눴다. Nemotron 기준선·Whisper turbo·Qwen3-ASR 1.7B·Scribe v2의 선정용 8건씩 총 32건이 완료됐다. 분류명은 청취 검수 목표이며 실제 내용 포함 여부는 아직 확정하지 않았다.

개인 원음과 원출력은 저장소에 넣지 않았다. 검수 자료는 `/Users/jaesolshin/Downloads/CSNL-1104-ASR-review-20261105-133148/README.md`, 추론 당시 코드와 manifest 원본은 `/tmp/open-scribe-rework-validation/asr-evaluation/`에 보존했다. 비교 추가 비용은 $0.033582997766396026, 합성 시간 탐침을 포함한 설치 CLI 검사를 포함한 공유 원장 실제 합계는 $0.16130261593584042이며 미정산 요청은 0건이다. 상한은 $10다.

32건은 R4 보고서 저장 보호 수정 전 실행이다. 추론 당시 코드 6개를 원래 핀과 대조해 보존했고, 후속 오프라인 분석은 `pre_lease_report_fix`로 표시한다. 기존 manifest를 새 코드에 맞춰 수정하거나 이 결과를 새 코드의 추론으로 가장하지 않는다. [평가기 문서](../../development/asr-evaluation.md)의 새 실행·검수 이관 규칙을 따른다.

## 완료 기준별 상태

| 계획 기준 | 상태 | 근거·남은 조건 |
|---|---|---|
| 호출·실패·청크·원문 보존 수정 | 구현 및 자동 검사 통과 | 전체 500개와 위 회귀·변이 증거 |
| 선정용 실제 실행 | 32/32 완료 | 8개 × 4모델; 원문·비용 보존 |
| 검수 정답 | 미완, 0/12 | 기존 검수본 없음; 모델 출력을 정답으로 대체하지 않음 |
| CER 10% 및 필수 발언 검수 | 전제 미충족 | 선정 정답 8개 및 원음 청취 검수 필요 |
| 모델 선정·보류 평가 | 전제 미충족 | 선정 관문 이후 한 모델에 보류 4개 평가·검수 |
| 60분 전체 ASR 재처리 | 전제 미충족 | 작은 표본 합격 이후 한 경로로 실행 |
| 로컬 설치 | 업그레이드·설정 검사 통과 | 기존 런타임·명령 백업 보존; 로컬 자원 재측정 기록은 아래에 추가 |

원음 정답/필수 발언 검수 담당은 실제 청취 가능한 검수자이며 현재 미배정이다. 사용자가 기존 검수본이 없음을 확인했으나 검수 생략을 승인한 것은 아니다. 따라서 정확도와 후속 단계는 미완으로 남긴다. 원음 전사·검수자·검수 시각이 확보되면 동일 고정 표본의 품질 관문에서 재개한다. 기본 ASR 모델을 바꾸거나 전체 파일을 반복 호출하지 않았다.

## 설치와 되돌리기

`bash scripts/install.sh --upgrade --python /opt/homebrew/bin/python3.12 --settings ~/.config/open-scribe/settings.json`을 실행했다. 설정 파일은 그대로 유지했고 기존 로컬 ML 의존성 그룹을 보존했다. 마지막 길이 0 정렬 보존 업그레이드의 직전 백업은 `~/.local/lib/open-scribe.backup-GeBlpo`와 `~/.local/bin/scribe.backup-GeBlpo`다. 앞선 자막 분기 백업 `backup-NdCS0e`도 보존했다. 키 경로를 제품 코드·wrapper에 넣지 않았다. `doctor`는 별도 키 주입 없는 프로세스에서 키 미설정을 정직하게 보고한다.

최초 수정 전 런타임은 `~/.local/lib/open-scribe.backup-yBZzQy`, 명령은 `~/.local/bin/scribe.backup-yBZzQy`다. 한국어 의존성까지 반영한 마지막 업그레이드의 직전 백업은 `~/.local/lib/open-scribe.backup-9xxNkV`와 `~/.local/bin/scribe.backup-9xxNkV`다. 되돌릴 때 현재 런타임을 별도 보관한 뒤 이전 디렉터리를 원래 위치로 옮기고 명령 백업을 복원한다. 사용자 설정·데이터·모델은 이 교체 대상에 포함되지 않는다. 실제 설치 로그는 `/tmp/scribe-asr-install-upgrade.log`와 `/tmp/scribe-korean-install-upgrade.log`, `/tmp/scribe-asr-final-install-upgrade.log`, `/tmp/scribe-asr-reviewed-install-upgrade.log`다.

한국어 의존성 추가 전 설치본의 첫 MPS 자격 실행은 시작 후 5초 안에 GPU 측정 파일이 나오지 않아 `GPU telemetry unavailable`로 중단했다. 측정 유예·자원 상한을 바꾸지 않고 한 차례 다시 실행했고, 3601.4381875초 원본의 화자 분리를 262.570초, 최대 1.5211GiB로 완료했다. 실패 실행을 자격 증거로 사용하지 않았으며 재실행의 실제 증거는 `/tmp/scribe-asr-requalified-diarization-retry.json`이다. 이 실행은 전체 ASR 재전사가 아니라 로컬 화자 분리 자원 자격 검사다.

## 공개 STT 카탈로그 30개 점검 범위

2026-11-05 공개 모델 목록과 endpoint 응답 30개를 수집했다. 활성 endpoint가 확인된 모델은 30개다. 한국어 지원과 단어 시간에 대한 긍정 metadata가 없는 항목은 미확인으로 유지했다. 공급자 metadata의 `supports_diarization=false`는 그 응답의 명시 값이며 별도 모델 가중치의 능력까지 판정하지 않는다. 과금 단위를 별도 확인해 제품 호출을 허용한 후보는 아래 `second` 네 모델이다. 이 표는 전체 모델의 한국어 품질을 실제 비교했다는 뜻이 아니다. 원시 증거는 검수 폴더의 `catalog-endpoints.json`, 목록은 [OpenRouter STT catalog](https://openrouter.ai/api/v1/models?output_modalities=transcription)다.

| 모델 | 활성 endpoint | 한국어 명시 | 화자 반환 명시 | 검증한 과금 단위 |
|---|---:|---|---|---|
| moondream/parakeet-ultra | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| nvidia/nemotron-3.5-transcribe | 1 | 미확인 | 없음(공개 metadata) | second |
| mistralai/voxtral-small-transcribe-3-0 | 3 | 미확인 | 없음(공개 metadata) | 미확인 |
| mistralai/voxtral-mini-transcribe-3-0 | 3 | 미확인 | 없음(공개 metadata) | 미확인 |
| assemblyai/universal-3-6-pro | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| elevenlabs/scribe-v2 | 1 | 미확인 | 있음 | second |
| elevenlabs/scribe-v2-medical | 1 | 미확인 | 있음 | 미확인 |
| google/gemini-3.5-transcribe | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| fish-audio/transcribe-1-pro | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| assemblyai/universal-3-5-pro | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| meta/muse-voice-transcribe-1.0 | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| microsoft/mai-transcribe-2 | 1 | 미확인 | 있음 | 미확인 |
| nvidia/nemotron-3.5-asr-streaming-multilingual-0.6b | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| mistralai/voxtral-small-24b-2507-stt | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| mistralai/voxtral-mini-3b-2507 | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| qwen/qwen3-asr-1.7b | 2 | 미확인 | 없음(공개 metadata) | second |
| qwen/qwen3-asr-0.6b | 2 | 미확인 | 없음(공개 metadata) | 미확인 |
| openai/gpt-transcribe | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| fish-audio/transcribe-1 | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| x-ai/grok-stt-1.0 | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| deepgram/nova-3 | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| microsoft/mai-transcribe-1.5 | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| nvidia/parakeet-tdt-0.6b-v3 | 2 | 미확인 | 없음(공개 metadata) | 미확인 |
| mistralai/voxtral-mini-transcribe | 2 | 미확인 | 없음(공개 metadata) | 미확인 |
| google/chirp-3 | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| openai/gpt-4o-mini-transcribe | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| openai/whisper-large-v3 | 3 | 미확인 | 없음(공개 metadata) | 미확인 |
| openai/whisper-large-v3-turbo | 3 | 미확인 | 없음(공개 metadata) | second |
| openai/whisper-1 | 1 | 미확인 | 없음(공개 metadata) | 미확인 |
| openai/gpt-4o-transcribe | 1 | 미확인 | 없음(공개 metadata) | 미확인 |

## 한국어 설치 결함과 실제 로컬 decoder 비교

영문 alignment 자격은 통과했지만 한국어 실제 경로는 처음 실패했다. 설치된 mlx-audio의 `ForceAlignProcessor.tokenize_korean()`이 `soynlp`를 요구하는데 STT extra와 기존 로컬 잠금파일에 없었다. 공식 [PyPI 배포판](https://pypi.org/project/soynlp/0.0.493/)을 확인해 0.0.493을 hash lock에 추가했다. 기존 잠금 버전은 바뀌지 않았고 추가된 배포판은 이 하나다. align runtime fingerprint에 tokenizer 버전을 포함해 누락·변경 시 이전 자격을 재사용하지 않게 했다. 이 수정으로 helper 코드 해시가 바뀌어 이전 로컬 자격은 그대로 보존하되 최종 코드의 새 측정으로 갱신한다.

문제 경계 28초에서 로컬 Qwen 0.6B의 penalty 1.0/1.1/1.15와 Whisper turbo를 정식 Helper로 비교했다. 실제 모델 호출 전 자격 측정과 일반 run을 각각 실행했으며, 합성 fixture가 아니다. 원출력은 `/tmp/scribe-installed-local-asr-comparison.json`에 있다. 이 비교는 tokenizer 의존성 추가 직전 helper 버전으로 수행했고 그 버전의 자격 ID·runtime fingerprint를 보존했다. 최종 설치본의 합성 native 검사도 별도로 다시 실행했다.

| 로컬 경로 | penalty | 실제 종료·자동 검사 | 자격 최대 메모리 |
|---|---:|---|---:|
| Qwen 0.6B | 1.0 | 1024 token 상한·반복, rejected | 1.785GiB |
| Qwen 0.6B | 1.1 | 정상 종료, 자동 검사 accepted | 1.785GiB |
| Qwen 0.6B | 1.15 | 정상 종료, 자동 검사 accepted | 1.785GiB |
| Whisper turbo | 1.0 | 정상 종료, 자동 검사 accepted | 1.301GiB |

정답이 없어 어느 출력이 정확한지 판정하지 않았다. penalty를 올려 폭주가 멎었다는 관찰을 CER 합격이나 기본값 선정으로 바꾸지 않았다. 로컬 ASR은 원격 기본 경로를 대체하지 않으며 실제 사용할 모델·옵션·길이의 유효 자격이 없으면 실행을 유예한다.

## 최종 설치본의 자원 자격

최종 설치 후 `runtime_version()`을 각 증거의 runtime fingerprint와 대조해 화자 분리·정렬·임베딩 모두 일치함을 확인했다. source와 설치본의 `src/`·`bot/` 파일은 바이트 불일치 0이며, 설치된 잠금파일도 소스와 같다. 설정 SHA256은 `1c5340b1aa800fc933a4813a26d7defab73ea4133d38c7fd313dafcf98921697`로 작업 전후 동일하다. 키 정본의 경로·값은 앱이나 wrapper에 넣지 않았다.

| 작업·실제 입력 | 경과 | 측정 최대 메모리 | 증거(`/tmp/`) |
|---|---:|---:|---|
| 화자 분리, CSNL 3601.438초 | 253.198초 | 1.489GiB | scribe-asr-final-diarization.json |
| 한국어 정렬, CSNL 경계 28초 | 19.550초 | 2.233GiB | scribe-asr-final-alignment-korean-retry.json |
| 영문 정렬, 합성 56.4215초 | 8.546초 | 2.390GiB | scribe-asr-final-alignment.json |
| 임베딩, 공개 예제 반복 30초 | 36.394초 | 1.050GiB | scribe-asr-final-embedding.json |

한국어 의존성을 추가한 직후 첫 정렬 시도는 측정값이 갱신되지 않아 `local helper telemetry unavailable`로 중단했다. 감시 유예·상한을 바꾸지 않은 한 차례 재실행으로 위 한국어 자격을 얻었다. 중단된 실행은 자격 증거로 쓰지 않았다. 로컬 모델 최초 실행 때 의존성 초기화 등으로 유예될 가능성은 남아 있고, 제품은 이런 실패를 정렬·화자 성공으로 숨기지 않고 원격 원출력과 partial 상태를 보존한다.

## 실제 설치 CLI 검사와 길이 0 정렬

실제 설치된 `scribe`로 문제 경계 28초를 처리했다. 격리된 단일 settings.json과 기존 공유 $10 원장을 사용했고 Notion·요약·Downloads 게시를 껐다. 최초 원격 요청은 Nemotron 한 번($0.0009324)이었고 이후 `jobs retry`는 저장된 `asr:0`을 재사용했다. 전체 60분 ASR은 호출하지 않았다.

첫 CLI 실행에서 `--no-speakers --srt`가 정렬을 건너뛰는 분기를 실제로 확인해 수정했다. 그 다음 단계에서는 GPU 측정 중단과 native aligner의 길이 0 구간이 차례로 확인됐다. 원시 정렬을 별도 정식 Helper 호출로 조사한 결과 47개 중 8개가 시작=끝이었고 음원 밖으로 나간 구간은 없었다. 입력 텍스트는 미검수 Nemotron 출력이다. 원래 오류 메시지 `alignment outside source window`는 길이 0에도 공통으로 쓰였던 문구이며 실제로 원본 범위 밖이었다는 증거가 아니다.

길이 0을 원문 삭제나 임의 시간 배분으로 처리하지 않는다. 원시 정렬 47개는 stage 결과로 먼저 보존하고, 유효한 시간은 유지하며, 길이 0 단위는 본문을 그대로 둔 채 시간·화자를 unknown으로 남기도록 수정했다. `alignment_zero_duration`과 해당 segment ID·단위 인덱스가 품질 검토 항목에 남는다. 전부 길이 0인 경우도 전체 본문을 보존한다. 음원 밖·역전·비유한 시간은 계속 거절한다. 미확정 구간을 확정 요약에 쓰거나 완전한 SRT로 표시하지 않는다.

혼합/전체 길이 0 두 사례를 회귀 검사 한 개의 subtest로 추가해 수정 전 실패를 재현했다. 수정 후 관련 검사 62개가 통과했다. 이 과정에서 첫 테스트의 SQLite result를 dict로 가정한 fixture 오류 두 건도 확인해 JSON 역직렬화로 고쳤고, 해당 중간 전체 실행은 중단했다. 그 실행을 합격 증거로 쓰지 않고 고정된 소스로 최종 전체 검사를 새로 실행했다.

최종 설치 CLI의 문제 경계 결과는 `partial`이다. `align:0`은 완료돼 원시 정렬 47개를 저장했고, canonical 본문 167자는 그대로 보존됐다. 단어 47개 중 39개는 실제 시간을 보존했고, 8개는 시간 unknown이다. 자동 품질은 `needs_review/alignment_zero_duration`이며 완전한 SRT는 생성하지 않았다. `jobs retry`의 종료 코드는 2다. 이는 실제 한국어 자막 검증 합격이 아니며, 미확정 시간과 원음 정확도 관문은 미완이다. 단위 테스트 성공이나 자원 자격으로 이 실패를 덮지 않는다.

최종 전체 회귀는 500개, 120.570초, OK였고 실행 전후 코드 해시가 일치했다. 명령과 고정 입력은 위 표의 verified-release 로그와 JSON에 있다. 기존 499개 통과 이후 추가한 검사는 길이 0 정렬 보존 한 개(혼합/전체 길이 0 두 subtest)다.

실제 설치 CLI의 정상 대조군으로 7초 영문 합성 음성을 별도 처리했다. Nemotron 원격 전사 → MLX 정렬 → TXT/JSON/SRT/VTT 경로가 `completed`, 종료 코드 0, 오류 0으로 끝났고 SRT와 VTT 파일이 실제 생성됐다. 이 영문 대조군을 한국어 CSNL의 정확도 합격으로 취급하지 않는다. 증거는 `/tmp/scribe-asr-installed-cli-positive.json`과 해당 작업 폴더다. 추가 비용은 $0.0002348316이다. 최종 공유 원장 합계는 $0.16130261593584042, 미정산은 0건이다.
