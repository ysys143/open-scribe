# ASR API + 별도 화자분리 API 계약

담당 B의 산출물은 당시 `src/core/cloud_diarization.py`(현재 `src/core/speech/diarization/cloud_diarization.py`), `tests/test_cloud_diarization.py`, 이 문서다. 설정·Application·CLI·공급자·Store·기존 화자 귀속 모듈은 수정하지 않았다. 기능 활성화와 `diarize:remote` 유료 stage 등록은 통합 담당 영역이다. 기본 ASR 모델·remote API 기본값·로컬 기능 off 설정을 이 모듈이 변경하지 않는다.

## 공개 인터페이스

```python
RemoteDiarizer(
    router: Router,
    model: str = 'elevenlabs/scribe-v2',
    provider_options: dict = None,
).preflight() -> dict

RemoteDiarizer(...).run(audio: Path, seconds: float) -> dict
```

`preflight()`는 인증 환경과 공개 모델/endpoint 메타데이터만 확인한다. POST·예산 예약·로컬 모델 실행이 없다. 작업에 고정된 `router.providers.openrouter.api_key_env`가 실제 프로세스 환경에 존재해야 하며, 그 참조값이 인증의 정본이다. 부모 Router에 남은 과거 키와 달라도 고정된 환경변수 값을 모듈 소유 Router에 바인딩해 실제 POST에 사용한다. 매 호출의 preflight에서 다시 바인딩하므로 재사용 전 키가 바뀌어도 새 값을 사용하며 부모 Router는 변경하지 않는다. native 공급자 키만 있는 Router, 고정된 환경변수가 사라진 Router, 다른 환경변수의 키만 있는 Router는 통과하지 않는다. 공개 반환값에는 환경변수 이름과 존재 여부만 있으며 키 값·개인 키 파일 경로가 없다.

응답 계약은 `verbose_json`과 단어 타임스탬프다. 공개 catalog에서 모델을 확인하고 모든 활성 endpoint가 `elevenlabs`이며 `supports_diarization=true`인지 검사한다. STT에서 endpoint 선택 옵션이 적용되지 않는다는 [OpenRouter 공식 문서](https://openrouter.ai/docs/guides/overview/multimodal/stt)에 따라, 옵션이 누락될 수 있는 다른 활성 endpoint가 생겨도 요청 전에 거절한다. 이것은 지원 계약 확인이며 실제 응답의 라벨 완전성이나 정확도를 보증하지 않는다.

`run()`은 입력 파일을 먼저 검사하고 `preflight()` 뒤 전체 음원에 정확히 한 번 전사를 요청한다.

```python
router_for_scribe.transcribe(
    audio, seconds, offset=0, detailed=True,
    provider_options={
        'elevenlabs': {
            'diarize': True,
            'tag_audio_events': False,
            'no_verbatim': False,
        },
    },
)
```

선택한 모델만 다른 Router를 만들며 원래 client·store·ceiling·scope·concurrency·credential_env·providers·text_model·effort를 유지한다. 인증값은 부모의 캐시 대신 고정된 환경변수 참조로 해석한다. 예약 원장과 원격 동시 실행 슬롯은 ASR과 공유한다. 새 client나 독립 예산 원장을 만들지 않으며 호출자의 실행 소유권 문맥도 그대로 사용한다. `provider_options`에는 같은 기본값 위로 ElevenLabs의 추가 옵션을 복사해 병합한다. `diarize=false`, `tag_audio_events=true`, `no_verbatim=true`와 미지원 옵션은 거절한다.

## 반환값과 본문 보존

```json
{
  "turns": [{"speaker": "speaker_0", "start": 0.1, "end": 1.2}],
  "metadata": {
    "model": "elevenlabs/scribe-v2",
    "provider": "openrouter",
    "source": "https://openrouter.ai/docs/guides/overview/multimodal/stt",
    "label_scope": "request",
    "label_scope_id": "one-call-identifier",
    "timeline": {"offset": 0, "seconds": 10},
    "request_count": 1,
    "status": "completed",
    "word_source": "words",
    "excluded_words": [],
    "provider_response": {},
    "billing": {}
  }
}
```

이 예시는 스키마이며 실제 전사·과금 영수증이 아니다. 실제 `provider_response`에는 API가 반환한 전사문·단어 문자열·type·화자 필드·usage를 보존한다. `billing`에는 Router의 예약과 정산 정보가 들어간다. 최상위 `text`는 반환하지 않는다. 별도 API의 전사문이나 단어 문자열로 canonical ASR 본문을 대체하지 않는다.

단어 관측에 있는 화자·시각만 구간화한다. 최상위 `words`가 있으면 중첩 `segments.words`를 중복 사용하지 않는다. 없으면 중첩 단어를 사용하며, segment 화자 라벨로 단어 구간을 만들어내지 않는다. `spacing`·`audio_event`는 원본에 남기고 구간에서 제외한다. 0초 구간·화자 누락·충돌한 `speaker`/`speaker_id`·알 수 없는 type은 경로와 제외 이유를 기록하고 `partial`로 표시한다. Router가 거절하는 시각 누락·역전·음원 밖 시각은 `UnknownOutcome`의 원본 응답과 과금 상태로 보존한다.

같은 화자의 서로 닿거나 겹치는 구간만 합친다. 양의 시간 간격을 메우지 않으므로 침묵을 화자 발화로 확장하지 않는다. 서로 다른 화자의 겹침은 그대로 남는다. `label_scope_id`는 호출마다 달라지며 `speaker_0` 등은 해당 요청 내부 식별자다. 다른 요청이나 실명으로 동일인을 확정하지 않는다.

통합에서는 같은 원음의 offset 0 타임라인에 다음 귀속 경로를 사용한다.

```python
attribute(canonical_asr, [SpeakerTurn(**turn) for turn in result['turns']])
```

본문·segment·단어의 원문 일치 조건이 충족되지 않거나 ASR에 단어 시각이 없으면 화자 귀속은 미확정이다. 별도 API의 단어 시각을 ASR 단어에 순서대로 붙이거나 segment 구간에 비례 배분하지 않는다. 화자 중첩과 순차 경계를 걸치는 단어도 기존 `attribute()`의 미확정 처리를 따른다. `metadata.status=completed`는 구간 추출 상태이며 정확도 검증이나 실명 확인을 뜻하지 않는다.

## 입력 제한과 실패

`run()`은 비어 있지 않은 기존 파일, 양의 유한 길이, 24 MiB 이하, 10시간 이하, `wav/mp3/flac/m4a/ogg/webm/aac` 확장자만 허용한다. 크기·길이·확장자 위반은 공개 GET과 유료 POST 이전에 거절한다. 24 MiB는 기존 Router와 일치하는 보수적 상한이다. 10시간은 [Scribe 표준 모드의 공급자 상한](https://elevenlabs.io/docs/overview/capabilities/speech-to-text)이며, OpenRouter의 60초 처리 timeout 안에 그 길이가 처리된다는 뜻이 아니다. 확장자 검사는 실제 codec이나 제공된 `seconds`가 맞다는 증명이 아니므로 통합에서 이미 확인한 전체 음원과 실제 길이를 전달해야 한다.

예를 들어 29 MB 원본 M4A는 직접 제출하면 사전 거절된다. 통합 담당은 전체 음원을 유지한 bounded ffmpeg 압축본을 준비하거나 이유를 남겨 deferred 처리해야 한다. 모듈은 자동 변환·분할·재호출을 하지 않는다. 분할 요청의 `speaker_0`을 같은 사람으로 합치는 우회도 없다.

HTTP 오류·timeout·잘못된 응답은 Router의 원본 영수증·예약 보존을 따른다. 사용량 비용이 없어 과금이 미확정이면 추출한 구간이 있더라도 `UnknownOutcome(result={turns, metadata}, billing=...)`을 발생시킨다. 통합 유료 stage가 이를 미확정으로 기록하고 재시도를 막아야 한다. 모의 통합 검사에서 예외의 결과가 orphan 영수증에 남고 같은 stage 재호출은 POST를 추가하지 않는 것을 확인했다. 로컬 helper fallback이나 준비되지 않은 모델 다운로드는 없다.

## 비용 비교

2026-11-06 인증 없는 공개 endpoint GET에서, 활성 endpoint 중 보수적인 시간당 요금은 Whisper Turbo 약 $0.04와 Scribe v2 약 $0.22였다. 따라서 동일 길이에 Whisper Turbo 전사와 Scribe 화자분리를 각각 요청하는 조합은 약 $0.26/h, Scribe로 전사·화자분리를 함께 하는 단일 요청은 약 $0.22/h다. 추가 전사 결과를 버려도 해당 전사 요청 비용은 발생한다. 이는 공급자 사용량에 따른 실제 청구액이나 정확도 우위를 보증하지 않는다. Router의 예산 예약 여유분은 이 비교와 별개다. 출처: [Whisper Turbo endpoint 가격](https://openrouter.ai/api/v1/models/openai/whisper-large-v3-turbo/endpoints), [Scribe v2 endpoint 가격](https://openrouter.ai/api/v1/models/elevenlabs/scribe-v2/endpoints).

읽기 전용 견적은 기존 `pricing.quote_model(client, model, audio=True)`을 각 모델에 호출하면 된다. 이 함수는 공개 가격·catalog만 GET하며 유료 추론은 시작하지 않는다. 요금을 코드 상수로 추가하지 않았다. pyannoteAI 키나 가입은 요구하지 않는다.

## 검증 범위

테스트는 격리된 환경변수와 임시 원장을 사용한다. HTTP 경계만 `httpx.MockTransport`로 대체하며 Router의 실제 옵션 생성·원장 예약/정산·원격 슬롯·예외·기존 `attribute()` 귀속 경로를 통과한다. 외부 inference POST·실모델 실행·모델 자격 판정은 수행하지 않았다. 실측 정답/CER와 실제 화자 정답도 없으므로 정확도 합격이나 실명 확정을 주장하지 않는다.

기본 명령은 `.venv/bin/python -B -m unittest tests.test_cloud_diarization -v`다. 원격 모델 선택 오류·공백 오분류·침묵 병합·크기 제한 해제·과금 미확정 통과·고정 환경변수 검사 우회·실제 POST에 과거 키 사용을 임시 복사본에 주입해 검사가 실패하는 것도 확인했다. 첫 공백 변이는 검사에 잡히지 않아 정상 상태와 제외 사유 검증을 보강한 후 재검증했다.

2026-11-06 인증 정본 계약 수정 후 최종 검증 기록:

| 범위 | 명령 또는 기록 | 결과 |
|---|---|---|
| 담당 B 검사 | `.venv/bin/python -B -m unittest tests.test_cloud_diarization -v` | 29개, OK |
| 관련 회귀 검사 | `.venv/bin/python -B -m unittest tests.test_cloud_diarization tests.test_scribe_diarization tests.test_provider tests.test_direct_providers tests.test_speaker_quality -v` | 동결 복사본에서 73개, 1.110초, OK |
| 결함 주입 | 동결 복사본에 위 7종을 각각 주입 | 원본 exit 0, 변이 exit 1의 AssertionError를 7/7 검출 |
| 코드 안정성 | src와 tests 전체를 동결해 실행하고, 동결본·작업공간의 실행 전후 SHA-256 비교 | 변경 없음 |

합성 환경변수 `FROZEN`의 정본값과 부모 Router의 과거 인증값을 다르게 주고, 실제 MockTransport POST의 Authorization 헤더가 정본값을 사용하는지 확인했다. 다른 기본 환경변수로의 우회·부모 Router 변경·재사용 시 오래된 키 사용을 막고, 공개 metadata·stdout/stderr·로그에 합성 키 값이 없는 것도 검사한다. 기존의 불일치 거절 구현에서는 새 정본값으로 요청하는 두 회귀가 ValueError로 실패했으며, 환경변수 참조를 다시 바인딩한 후 통과했다. 실제 키 파일이나 실제 키 값은 조사하지 않았다.

최종 회귀 출력은 `/tmp/scribe-composite-api-auth-v2-tests.log`, 명령·입력 해시·결과는 `/tmp/scribe-composite-api-auth-v2-tests.json`, 변이 결과는 `/tmp/scribe-composite-api-auth-v2-mutation.json`이다. 이전 26개/70개/변이 6종 기록은 인증 정본 계약 수정 전 버전의 기록이다. 이번 73개는 담당 B와 관련된 검사의 결과이며 전체 공유 작업의 최종 합격 판정이 아니다. 유료 호출, 원본 전체 재전사, 개인 설정·설치본 수정, commit/push는 수행하지 않았다.
