# 고정 ASR 평가 하네스

`tools/evaluation/evaluate_asr.py`는 로컬 manifest 생성, OpenRouter 평가, 명시적 모델 선정 동결을 제공한다. 단위 테스트는 합성 WAV와 `httpx.MockTransport`를 사용한다. 별도의 실제 검증에서는 CSNL 클립 12개를 추출하고 선정용 8개에 네 모델을 호출한 32개 결과를 저장소 밖에 보존했다. 정답은 전부 pending이며 정확도·모델 선정은 미완이다. 실제 실행과 설치 상태는 [구현 기록](../archive/rework/asr-reliability-implementation.md)에 구분해 기록한다. 녹음 데이터·실제 정답은 저장소에 넣지 않는다.

## 코디네이터 체크포인트와 API

manifest/report의 `schema_version`은 1이다. 기존 애플리케이션·설치본·설정을 변경하지 않는다. 호출 계약은 다음과 같다.

```python
from tools.evaluation.evaluate_asr import prepare_manifest, evaluate_manifest, freeze_selection

prepare_manifest(source, out, *, expected_source_sha256=None,
                 catalog_path=CATALOG, capabilities_path=None)  # pathlib.Path 반환
evaluate_manifest(path, model_ids=None, *, split='selection', allow_paid=False,
                  ledger_path=LEDGER, ceiling=10, api_key=None, client=None)  # dict 반환
freeze_selection(path, model_id, *, reviewed_by, reason, ledger_path=LEDGER)  # dict 반환
```

`out`은 아직 없는 디렉터리다. `prepare_manifest`는 `out/manifest.json`을 반환하고 `out/clips/*.wav`를 만든다. 저장소 안의 출력 폴더와 manifest는 거절하며 이미 있는 출력 폴더는 덮어쓰지 않는다. 추출 도중 실패하면 부분 폴더를 보존하며 manifest가 없는 출력은 미완이다. `expected_source_sha256`은 전체 SHA256 또는 8자리 이상 접두사다. SHA 불일치와 지나치게 짧은 원본은 출력 폴더 생성 전에 거절한다. 원본은 추출 전후 전체 SHA를 확인한다.

코디네이터는 CSNL 원본 경로를 자신의 셸에서 지정하고, 저장소 밖 출력 디렉터리로 아래 준비 명령을 실행한다. `CSNL_SOURCE`는 원본 경로를 담는 로컬 변수이며 manifest에는 그 경로를 저장하지 않는다. 실제 전체 SHA는 manifest의 `pins.original.sha256`에 기록한다. 여기서 제공받은 원본 식별자는 접두사 `21c83147`이다.

```sh
.venv/bin/python -B tools/evaluation/evaluate_asr.py prepare "$CSNL_SOURCE" \
  /tmp/open-scribe-rework-validation/asr-evaluation \
  --expected-source-sha256 21c83147 \
  --catalog-snapshot /tmp/open-scribe-stt-models.json

.venv/bin/python -B tools/evaluation/evaluate_asr.py evaluate \
  /tmp/open-scribe-rework-validation/asr-evaluation/manifest.json

.venv/bin/python -B tools/evaluation/evaluate_asr.py --help
.venv/bin/python -B tools/evaluation/evaluate_asr.py evaluate --help
```

두 번째 명령은 오프라인 보고만 만든다. `allow_paid=False`가 Python API 기본값이며 CLI도 `--allow-paid` 없이는 Router를 생성하지 않고 키를 읽지 않는다. 실제 유료 검증은 승인된 공유 $10 한도 안에서 외부 셸 환경의 `OPENROUTER_API_KEY`를 사용했다. 하네스는 키 파일·앱 설정을 읽거나 키를 manifest/report에 쓰지 않는다. `api_key`·`client`·`ledger_path` 매개변수는 격리 테스트용 주입 경로도 제공한다. CLI에는 별도 원장·scope·상한 우회 인자가 없다.

```sh
# 유료 실행 예시. 기존 실행의 핀은 아래 이력 절의 제한을 따른다.
.venv/bin/python -B tools/evaluation/evaluate_asr.py evaluate \
  /tmp/open-scribe-rework-validation/asr-evaluation/manifest.json \
  --allow-paid
```

## 정확히 12개, 480초, 선정 8개와 보류 4개

원본은 최소 2482초여야 한다. 중복 없는 고정 구간을 사용하며 짧은 파일을 늘리거나 구간을 임의 대체하지 않는다. 마지막 구간은 원본의 마지막 41초다. 모두 45초 이하다. 문제 경계는 정확히 828–856초이며 840초를 가로지른다.

| ID | 원본 시작–끝(초) | 길이(초) | 분할 | 청취 검수 목표 |
|---|---|---:|---|---|
| opening | 0–42 | 42 | selection | 시작 |
| ordinary | 180–221 | 41 | selection | 일반 대화 |
| backchannel | 360–401 | 41 | selection | 맞장구 |
| quiet | 540–581 | 41 | holdout | 작은 목소리 |
| boundary | 828–856 | 28 | selection | 14분 문제 경계 |
| numbers | 1000–1041 | 41 | selection | 숫자·소수점 |
| negation | 1200–1241 | 41 | selection | 부정문 |
| names | 1440–1481 | 41 | holdout | 고유명사 |
| noise | 1800–1841 | 41 | selection | 소음 |
| crosstalk | 2100–2141 | 41 | selection | 겹침 |
| later | 2400–2441 | 41 | holdout | 후반 대화 |
| tail | 원본 길이−41–원본 길이 | 41 | holdout | 마지막 꼬리 |

위 분류는 원음을 듣기 전의 목표다. 실제 포함 사실을 주장하지 않는다. `content_validation.status`는 `pending`, `observed_tags`는 빈 배열로 시작한다. 원음 청취 후 확인자를 기록해 실제 포함 여부를 별도로 남긴다. 해당 목표가 없다고 구간이나 분할을 바꿔 평가 결과를 유리하게 만들지 않는다. 실제 내용 커버리지 검수는 코디네이터에게 남은 작업이다.

## 고정 정보와 모델

manifest의 `pins`와 그 SHA256은 원본 전체 SHA·크기·길이, 각 구간·클립 SHA, 분할, 변환, 모델 네 개, 모델별 요청 계약, decoder, 코드 버전을 고정한다. 출력은 제품 파일과 같은 16kHz mono PCM16 WAV(`pcm_s16le`)이며 ffmpeg 버전도 기록한다. native 로컬 loader의 메모리 입력 float32 변환은 해당 loader의 책임이며 이 원격 평가기는 로컬 loader를 실행하지 않는다. 추가 문맥은 0초다. 전체 480초는 전송할 클립 길이 합계다. 실제 제품의 문맥 청크 병합·화자 연결 성능 검증과 구별한다.

허용 모델은 아래 네 개이며 기준선은 첫 번째다. 로컬·공급자 직접 호출이나 모델 자동 대체는 없다. ID는 당시 Router의 `src/core/pricing.py` 계약(현재 위치 `src/core/providers/pricing.py`) 및 [OpenRouter 전사 가이드](https://openrouter.ai/blog/tutorials/transcription-on-openrouter/), [Qwen 모델 목록](https://openrouter.ai/qwen/), [Scribe v2 카드](https://openrouter.ai/elevenlabs/scribe-v2/)와 대조했다.

- `nvidia/nemotron-3.5-transcribe`
- `openai/whisper-large-v3-turbo`
- `qwen/qwen3-asr-1.7b`
- `elevenlabs/scribe-v2`

실제 요청은 모두 `language=ko`, `temperature=0`, `offset=0`이다. `detailed`는 `pins.model_contracts.<model>.request_options`에 모델별로 고정한다. 준비 단계는 기존 `Router.transcription_capabilities(model)`로 공개 GET만 실행하며 원본 모델·endpoint metadata를 보존한다. 자격 증명과 원장을 사용하지 않고 추론을 호출하지 않는다. 이미 수집한 native 응답이 있으면 모델 ID를 키로 하는 JSON을 `capabilities_path` 또는 CLI `--capabilities-snapshot`으로 전달해 완전한 오프라인 준비도 가능하다.

활성 endpoint 모두가 word timestamps 지원과 `verbose_json` 형식을 명시한 경우에만 `detailed=True`로 요청한다. 명시적 미지원이나 미확인이면 `detailed=False`와 JSON 텍스트 요청으로 고정하고 timestamp 요청을 보내지 않는다. 빈 `supported_parameters`나 화자 기능으로 시간 정보 지원을 추론하지 않는다. 2026-11-05 공개 GET으로 확인한 네 후보의 metadata에는 이 긍정 계약이 없었으므로 현재 준비 시에는 네 모델 모두 보수적인 JSON 계약이다. metadata의 미확인은 실제 기능 미지원이라는 판정이 아니다. 400 응답 뒤 옵션을 바꿔 재호출하지 않는다.

원본 구간 시작·끝은 manifest에 있고 반환 timestamp는 클립 기준이다. 보고서는 실제 받은 단어·시간 있는 단어·화자 라벨 단어·시간 있는 segment 수와 단어/본문 일치 여부를 관찰값으로 기록한다. 시간 정보가 없는 응답에 시간을 만들지 않는다. `max_tokens`, `repetition_penalty`, `seed`는 기존 Router가 전사 계약으로 검증하지 않은 인자이므로 `not_sent`로 고정한다. 이를 적용됐다고 보고하지 않는다. 공급자가 제공하는 checkpoint revision과 미전송 decoder 기본값은 고정할 수 없어 `provider_revision=null`과 `provider_defaults`에 한계를 기록한다. 완전한 서버 재현성을 보장하지 않는다.

전체 STT 카탈로그는 `catalog_path`의 로컬 공개 snapshot을 읽어 SHA와 전체 metadata 요약을 고정한다. 기본 파일은 `/tmp/open-scribe-stt-models.json`이며 현재 파일은 선언된 30개와 실제 30개가 일치한다. 부분 pagination, 중복 ID, 전사 외 modality, 네 후보 누락은 거절한다. 실제 report에 `candidate_model_ids` 네 개, `catalog.model_count`, 전체 `catalog.models`를 보존한다. 각 모델의 원시 요금·architecture·지원 인자·endpoint 경로를 기록하되 별도 검증이 없는 한국어·시간·화자·과금 단위·활성 endpoint 지원은 `unknown`이다. 현재 활성 후보 metadata는 `model_contracts`에 따로 보존하며 전체 30개를 모두 실제 호출했다는 주장을 하지 않는다. snapshot 수정 시 기존 pins를 재연결하지 않는다.

변환·decoder·모델·구간·분할 변경은 로드 시 거절한다. 클립 파일은 해시를 다시 확인하고 manifest 밖 경로는 거절한다. 평가기, Router, pricing, Store, model 자료형, operation context의 소스 SHA도 확인하므로 이 파일들이 바뀌면 기존 manifest로 새 요청하지 않는다. 코드 업데이트 뒤에는 원본에서 새 평가 묶음을 준비해야 하며, 관련 미확정 요청은 Store의 추가 검사로 차단된다. 검수용 `reviews`는 추론 캐시 키에서 제외하므로 사후 정답 확인으로 유료 호출을 반복하지 않는다.

## 정답 검수와 CER

처음에는 12개 모두 아래 상태다. 정답을 제공받거나 원음을 검수하지 않았으므로 모델 출력에서 채우지 않는다.

```json
{
  "status": "pending",
  "text": null,
  "reviewed_by": null,
  "reviewed_at": null,
  "method": null
}
```

원음 청취 검수 후 `reviews.<clip-id>.reference`에 실제 발언, `status="confirmed"`, 검수자 `reviewed_by`, timezone이 있는 ISO 시각 `reviewed_at`, `method="human_listening"`을 기록한다. `confirmed`인데 이 정보가 누락되면 요청 전에 거절한다. 내용이 비어 있는 실제 무음 정답은 문자열 `""`로 표현할 수 있지만, 빈 정답만 있는 corpus는 분모가 0이므로 CER을 만들지 않는다. `pending`에 임시 텍스트를 넣어도 채점하지 않는다. 모델 다수결·LLM 교정은 정답 근거가 아니다.

`normalize_cer(text)`는 Unicode NFC와 Unicode 공백 제거만 수행한다. 숫자·소수점·문장부호·부정문을 유지한다. `character_errors(reference, hypothesis)`는 Levenshtein 편집 수, 정답 글자 수, CER을 반환한다. CER은 1을 넘을 수 있다. corpus CER은 편집 수 합계를 정답 글자 수 합계로 나눈 값이며 클립별 CER 평균이 아니다.

보고서는 `report-selection.json` 또는 `report-holdout.json`이다. 각 case에 결과·실행시간·품질 플래그·검수 상태·점수를 기록하고, 모델별 완료 수·검수 수·채점 수·글자 수를 집계한다. 전체 분할의 모든 case에 검수 정답과 완료 결과가 있어야 모델의 `cer`를 채운다. 일부만 있으면 `quality="partial"`, `cer=null`이고 참고용 `observed_cer`를 별도로 둔다. 정답이 없으면 `quality="unknown"`, `cer=null`이다. 모델들이 동일한 결과를 내도 `winner`는 항상 `null`이다.

빈 전사는 전송 결과로 보존하고 `empty_response_needs_review`를 표시한다. 자동 무음 판정이나 재호출을 하지 않는다. 숫자·부정문·고유명사 검수는 모델별로 명시적 청취 검수를 입력하기 전까지 `pending`이다. 선정 보고서의 `acceptance`는 `not_established`로 두고 실제 선정 관문은 `freeze_selection`에서 강제한다. 보류 보고서는 아래 조건에 따라 `passed`·`pending`·`failed`를 기록한다. 이 판정만으로 기본 모델을 자동 변경하거나 전체 파일을 재처리하지 않는다. 실제 음향 범주 포함 여부와 전체 파일 재처리 승인은 별도로 확인해야 한다.

## 원장, 재개, 미확정 결과

기본 원장은 `/tmp/open-scribe-rework-validation/transcription_jobs.db`, scope는 `validation`, 누적 상한은 $10이다. 기존의 지출·예약을 함께 계산하며 실행마다 새 예산을 만들지 않는다. 전달받은 기존 원장 수치 `$0.1258865574`, 미확정 0건은 코디네이터의 사전 체크포인트이고, 이 구현에서는 실원장을 열거나 그 수치를 재검증하지 않았다. 실제 실행 시에는 Store의 현재 원장 값이 우선한다.

모든 전사는 기존 `Router.transcribe` 한 경로다. 가격 조회·예약·영수증 보존·실제 비용 정산은 Router가 담당한다. 하네스는 Store의 예약·정산 값을 조회해 보고할 뿐 자체 요율로 비용을 만들거나 `settle`을 호출하지 않는다. 클라이언트는 순차 요청하며 Router의 원장 slot 보호도 유지한다.

job은 `pins_sha256`으로 중복 제출을 막는다. clip/model별 stage 이름과 key가 결정적이며 각 유료 요청의 `operation_context`에 job/stage/key를 넣어 비용 예약과 연결한다. 출력 디렉터리를 옮기거나 모델 부분집합을 달리해도 같은 pins이면 같은 job을 사용한다. 원격 stage에 앞서 job lease를 얻어 같은 묶음의 동시 실행을 차단한다.

보고서는 `Store.connect()`의 쓰기 트랜잭션 안에서 `assert_execution(job, worker)`를 확인한 뒤 원자적으로 저장한다. 따라서 검사와 보고서 교체 사이에 새 worker가 job을 인계할 수 없다. lease가 만료됐거나 다른 worker가 인계했으면 보고서를 쓰지 않고 `LeaseLost`를 발생시킨다. 수정된 실행 보고서는 `report_publication_contract="lease_transaction_v1"`을 기록한다.

완료 stage는 원장의 결과를 재사용한다. `UnknownOutcome`, 중단 후 남은 `running`, `failed` stage, 실제 비용이 없는 예약이 있으면 남은 유료 작업과 다음 실행을 차단한다. 완료된 case는 차단 상태에서도 보고·재채점할 수 있다. 파싱 오류가 나도 Router가 보존한 실제 정산과 원응답은 원장에 남는다. 실패·미확정 상태를 지우거나 다른 폴더·새 실행으로 우회하지 않는다. 코디네이터가 공급자 영수증과 기존 명시적 조정 경로를 통해 확인한 뒤에만 진행한다. 이 하네스에는 자동 재시도·원장 초기화·추정 비용 정산 명령이 없다.

## 선정 동결과 보류 평가

보류 요청 전에는 선정용 정답 8개 전부 확인, 네 모델의 선정용 8건씩 총 32건 완료, 미확정 stage/과금 부재를 요구한다. `freeze_selection`은 원장에 저장한 원출력으로 선정 모델과 Nemotron 기준선의 micro CER을 다시 계산한다. 전체 정답 글자 수 합계가 양수이고, 선정 모델의 CER이 0.1 이하이며 기준선 CER 이하일 때만 동결한다. 클립별 CER의 단순 평균은 사용하지 않는다. 기준선과 동률이어도 검수자와 공백이 아닌 선정 이유는 반드시 입력해야 한다. 자동 우승 모델은 만들지 않는다.

선정 모델의 8개 구간에는 모델별·클립별 필수 발언 검수가 모두 필요하다. 위치는 `reviews.<clip-id>.critical_validation.<model-id>`다. 준비 단계는 아래 구조를 네 후보 모두 `pending`으로 만들며 원음을 듣거나 모델 출력으로 자동 합격시키지 않는다. 기존 파일에서 이 항목이나 해당 모델의 기록이 없으면 `pending`으로 취급한다.

```json
{
  "critical_validation": {
    "openai/whisper-large-v3-turbo": {
      "status": "pending",
      "method": null,
      "reviewed_by": null,
      "reviewed_at": null
    }
  }
}
```

원음과 해당 모델 출력을 대조해 숫자·소수점·부정문·고유명사 등 필수 발언이 보존됐음을 확인한 뒤에만 `status="passed"`를 입력한다. `method="human_listening"`, 비어 있지 않은 `reviewed_by`, timezone이 있는 ISO `reviewed_at`이 필수다. 같은 클립의 다른 모델 검수로 대신할 수 없다. 실패한 검수는 `failed`로 기록하고, 누락·pending·failed·감사 정보 없는 passed가 하나라도 있으면 선정 모델을 동결하지 않는다. 정답 reference와 모델별 검수는 서로 별개의 기록이다.

```sh
.venv/bin/python -B tools/evaluation/evaluate_asr.py freeze \
  /tmp/open-scribe-rework-validation/asr-evaluation/manifest.json \
  --model openai/whisper-large-v3-turbo \
  --reviewed-by "$ASR_REVIEWER" --reason "$ASR_SELECTION_REASON"

# 별도 승인된 유료 실행 예시. 실제 선정된 모델 하나만 지정한다.
.venv/bin/python -B tools/evaluation/evaluate_asr.py evaluate \
  /tmp/open-scribe-rework-validation/asr-evaluation/manifest.json \
  --models openai/whisper-large-v3-turbo --split holdout --allow-paid
```

`freeze`는 원장에 선정 모델·검수자·시각·이유와 선정 정답/전체 critical review/결과 SHA를 저장한다. `selection_gate.contract="micro_cer_critical_v1"`과 선정·기준선 편집 수, 정답 글자 수, micro CER, 개선/동률 여부, 검수 통과 8건도 보존한다. 같은 동결 요청은 재사용하고 모델·이유·검수자를 바꾸는 재동결은 거절한다. 동결 뒤 선정 정답·선정 결과·선정 구간의 어느 모델 critical review라도 수정되면 거절한다.

보류는 선택된 모델 하나의 4건만 허용하고 재실행은 완료 캐시를 사용한다. 동결 뒤 선정용 유료 평가는 막고 오프라인 보고만 허용한다. 보류 보고서의 최상위 `acceptance`와 해당 모델의 `acceptance`는 확정 정답 4개·완료 결과 4개·정답 글자 수 합계 양수·해당 모델의 청취 검수 passed 4개·micro CER ≤0.1·미확정 stage/과금 부재를 모두 만족할 때만 `passed`다. 검수의 명시적 failed나 전체 CER 초과는 `failed`, 그 밖의 전제 미충족은 `pending`이다. 정답이 없는 구간은 점수를 만들지 않으며 품질 unknown을 유지한다. 실제 reference와 critical review는 원음 청취로만 채운다. 사후 검수 입력으로 캐시를 재평가할 때 유료 호출을 반복하지 않는다.

## 로컬 검증

```sh
.venv/bin/python -B -m unittest tests.test_evaluate_asr -v
```

테스트는 12개/480초/8+4/문제 경계, source SHA 사전 검사, 무정답 상태, 실제 짧은 PCM16 WAV 변환, CLI 도움말과 기본 오프라인 실행, 확정 정답 검증, NFC·숫자·부정문 CER, 부분 정답의 집계 제한, 실제 Router·Store 정산 연결, 완료 재사용, 폴더 이동, timeout·비정상 응답·미확정 비용·중단·동시 실행 차단, 공유 예산, pins 변조, 선정 동결과 보류 1회 실행/캐시를 확인한다. 합성 30개 metadata fixture로 전체 요약과 미확인 capability 보존을 검사하고, 모델별 detailed 고정·400 무재시도·실제 응답의 시간 정보 관찰을 검증한다. 실제 CSNL 데이터·유료 API·실원장을 사용하지 않는다.

## R4 수정과 기존 실행의 보존

독립 검토 R4에서 lease 만료 뒤 이전 worker가 보고서를 덮어쓰고, 이후 `finish()`에서야 `LeaseLost`가 발생하는 경로를 재현했다. 181초의 시계 이동과 새 worker의 인계를 넣은 회귀 검사, 인계 없이 만료만 시킨 검사가 모두 수정 전 덮어쓰기를 검출한다. 위 트랜잭션 보호가 그 보고서 저장 경로를 수정한다.

기존 CSNL 32회 실행은 수정 전 코드로 수행됐다. `/tmp/open-scribe-rework-validation/asr-evaluation/inference-code-snapshot`의 추론 코드 6개를 기존 manifest의 해시와 대조했고 모두 일치했다. 이 아카이브·manifest·원래 보고서는 수정하지 않는다. 현재 평가기 소스 해시는 의도적으로 기존 핀과 달라지므로 기존 manifest의 핀을 새 소스에 맞춰 고치지 않는다. 향후 유료 추론은 정답 검수와 품질 관문을 확인한 뒤 새 manifest로 승인된 공유 한도 안에서 실행해야 한다. 한도를 초과하는 변경에는 사용자 승인이 필요하다. 이번 수정은 유료 호출을 다시 실행하지 않는다.

`tools/evaluation/assess_asr_results.py`는 기존 보고서를 읽기 전용으로 계속 분석한다. publication contract가 없는 보고서는 `publication_history.version="pre_lease_report_fix"`로 표시하고 Markdown에도 수정 전 실행임을 적는다. 새 marker가 있는 보고서는 `lease_report_fix_declared`로만 표시하며 선언만으로 이력을 검증했다거나 새 추론을 실행했다고 주장하지 않는다. 원래 추론 핀과 현재 품질 검사 해시는 계속 분리하고, `fresh_inference_performed=false`, 정확도 unknown, CER null을 유지한다.
