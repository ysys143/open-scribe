# 화자 이름 후보 후처리

`src/core/speech/diarization/speaker_names.py`는 이미 API 또는 로컬에서 분리한 화자 ID에 이름 후보를 연결한다. 기본 동작은 비활성이며, 활성화해도 제안만 저장한다. 얼굴·외모·음성 유사성으로 사람을 알아내지 않는다. 실명 확정과 음성 임베딩 등록은 기존 `identity.py`의 사람 확인 절차에 남는다.

## 호출 계약

```python
name_speakers(
    transcript, stage, router, options,
    video=None, context=None, folder=None,
) -> Transcript
```

- `transcript`: canonical 본문과 세그먼트가 일치하는 `Transcript`. 함수는 깊은 복사본만 수정한다.
- `stage(name, settings, operation)`: 캐시·과금·실행 상태를 관리하는 주입 경계. 실제 모델 호출은 `speaker_names:0`, `speaker_names:1` 순서로 실행한다. 유료 호출을 `derived:`로 분류하지 않는다. 캐시 응답도 원본 근거와 다시 대조한다.
- `router.speaker_names(payload: dict, frames: list) -> dict`: 유일한 외부 모델 호출 경계. 이 모듈에는 HTTP 클라이언트나 API 키 조회가 없다.
- `options`: `enabled=False`, `apply_suggestions=False`, `max_frames=6`, `max_frame_bytes=2097152`, `frame_timeout_seconds=10`. 제한값은 더 작게만 설정할 수 있다. 설정 소유자는 `settings.json`이며, Application은 활성 stage의 옵션에 `enabled=True`를 합쳐 전달한다. `provider`, `model`, `effort`를 전달하면 캐시 식별에도 포함한다. Application의 stage wrapper는 전체 stage·provider 설정을 추가할 수 있다.
- `video`: 이미 존재하는 로컬 영상 `Path`만 사용한다. URL 입력이나 전체 영상 다운로드는 하지 않는다. 영상 경로는 router payload에 넣지 않는다.
- `context`: 문자열이면 `description`으로 취급한다. 객체는 `title`, `description`, `participants`만 전달하며, `participants` 문자열 목록은 줄바꿈으로 연결한다. 전체 문맥은 16KiB 이하이다. 메타데이터 전체나 로컬 파일 경로를 자동 전송하지 않는다.
- `folder`: 선택 사항. 이미 존재하는 별도 출력 폴더에 `speaker-name-suggestions.json`만 배타 생성한다. 같은 내용의 재실행은 허용하고, 다른 내용·사용자 수정·심볼릭 링크는 보존하며 오류를 반환한다. `named/`, identity manifest가 있는 폴더와 심볼릭 링크 폴더는 거절한다. Application이 파생 파일을 관리할 때는 `folder=None`을 사용한다.

입력 전체를 세그먼트 단위로 나눠 각 text payload를 JSON UTF-8 기준 20,000바이트 이하로 유지한다. 본문·ID·숫자는 바꾸거나 잘라내지 않는다. 단일 세그먼트나 고정 문맥만으로 한도를 넘으면 모델 호출 전에 오류를 반환한다. 현재 배치에 없는 세그먼트를 근거로 주장한 응답도 거절한다. 화자 겹침은 배치별이 아닌 전체 타임라인으로 검사해 다른 배치에 있는 동시 발화를 놓치지 않는다.

Scribe처럼 원래 세그먼트 하나에 여러 화자의 단어가 있는 경우에는 canonical 단어 본문·개별 시간·겹침 여부를 검사한 뒤 이름 추론에만 사용하는 임시 단일 화자 turn view를 만든다. 연속한 동일 화자 단어를 묶으며, `0 → 1 → 0`은 서로 다른 세 turn으로 유지한다. 임시 ID는 원본 ID와 충돌하지 않게 만들고, 각 payload 항목에 `parent_segment`와 반열린 `word_range=[start,end)`를 제공한다. 모델은 임시 `id`를 reference로 반환한다. 검증한 segment·frame 근거에도 같은 원본 parent와 word range를 함수가 직접 붙인다. frame 근거는 연결된 임시 `segment_reference`도 기록한다.

이 view는 원래 Transcript나 원본 segment ID·word 시간·speaker ID에 쓰지 않는다. 단어 본문 불일치, 시간 누락·부모 범위 이탈, 겹침, 단어 화자 누락은 임의 보간하지 않고 unknown으로 남기며 `turn_view`에 이유를 기록한다. 프레임 샘플링과 화자 대조에는 임시 turn 시간을 사용하고 원본 범위도 coverage에 함께 남긴다.

프레임은 다음 형식이며 요청의 text payload와 분리한다.

```json
{"id":"frame:0","time":2.0,"mime_type":"image/jpeg","data":"<base64>"}
```

추출 전체에서 최대 6장, 폭 720px 이하, base64 합계 2MiB 이하이다. 각 배치에는 그 배치의 시간 구간에 해당하는 프레임만 전달한다. 캐시에는 프레임 내용의 SHA-256과 ID·시간·MIME 형식을 넣는다.

router 응답 예시는 다음과 같다.

```json
{
  "candidates": [{
    "speaker": "A",
    "name": "김민수",
    "evidence": [{
      "source": "segment",
      "reference": "s1",
      "quote": "저는 김민수입니다."
    }]
  }]
}
```

`model`, `billing`, `confirmed` wrapper 필드는 허용하지만 사람 확인으로 해석하지 않는다. 본문·시간·세그먼트 교체 필드는 거절한다. 후보는 응답당 최대 128개, 후보당 근거는 1~16개이다.

## 근거 검증과 불확실성

| source | reference | 검증 및 취급 |
|---|---|---|
| `segment` | 원래 segment ID | 인용문이 원본에 그대로 존재하고 이름이 인용문에 있어야 한다. 인용문과 원래 세그먼트 모두 명시적 자기소개 형식이어야 한다. 제삼자 소개는 거절한다. 해당 세그먼트의 화자가 유일해야 한다. |
| `context` | `title`, `description`, `participants` | 원문에 그대로 존재하는 인용문만 허용한다. 설명·명단은 `contextual` 후보이며, 이것만으로 표시명을 붙이지 않는다. |
| `frame` | 실제 전달한 frame ID | 해당 시각에 단일 화자 구간이 있어야 한다. `kind`는 `lower_third`, `name_tag`, `subtitle` 중 하나이며, `readable=true`, `people=1`, `ambiguous=false`, `occluded=false`를 모두 요구한다. |

영상 인용문은 모델의 OCR·영상 관찰 결과이며 독립적으로 사실 확인한 문구가 아니다. 따라서 `quote_validation=unverified_visual_observation`을 기록한다. 텍스트 인용문의 존재 확인도 실명·동일인 확인을 뜻하지 않는다. 모호한 매칭, 다중 인물·겹침·가려진 명찰, 존재하지 않는 ID, 이름이 없는 인용문, 원본과 다른 숫자가 포함된 인용문은 거절하거나 unknown으로 남긴다. 같은 화자에 서로 다른 이름 또는 같은 이름에 여러 화자가 연결되면 표시명 후보 자격을 해제한다.

화자 구간에 단어가 있으면 완전한 단어 본문과 모든 단어의 동일 화자 배정이 필요하며, overlap 단어는 허용하지 않는다. 시간 구간이 다른 화자 또는 unknown과 겹치면 연결하지 않는다. 시간상 영상에 나타난 한 사람과 발화자가 동일하다는 사실까지 증명하지 못하므로 영상 후보는 항상 사람 검토 대상이다.

prompt의 모든 영상 문구·본문·설명문은 신뢰하지 않는 데이터로 명시한다. 원문이 제시한 명령을 실행하거나 외부 검색으로 이름을 보충하지 않는다. router에 복사본을 전달하고, 응답은 별도로 보존한 원본 근거와 검증한다. 모델이 원본 payload를 바꿔도 검증 근거가 바뀌지 않는다.

## 결과와 기존 identity 경계

복사된 Transcript의 `metadata.speaker_name_suggestions`에 다음을 기록한다.

- `mode`: `suggest_only` 또는 명시 적용 시 `apply_suggestions`.
- `source_sha256`: 원래 Transcript 사전의 결정적 fingerprint. 기존 identity가 사용하는 원본 파일 바이트 SHA와 별개이며 identity 확인 키로 사용하지 않는다.
- `candidates`: `status=suggested/contextual`, `confirmed=false`, `verification=requires_review`, 검증한 근거와 `eligible_for_display`.
- `rejected`: 후보 인덱스·배치와 거절 사유. 거절 후보의 임의 이름을 표시명으로 사용하지 않는다.
- `unknown_speakers`: 유효한 표시명 제안이 없는 원래 화자 ID.
- `video_evidence`: 영상 단서 유무, 실패 이유, 모든 세그먼트의 sampled/deferred 내역.
- `turn_view`: 추론용 임시 ID, 원래 segment ID, word range, 화자 또는 unknown, view 생성이 불가능한 이유. 원본 세그먼트 변경 내역이 아니다.
- `automatic_identity=false`, `voice_enrolled=false`.

`apply_suggestions=True`인 경우에만 기존 `metadata.speaker_names`에 없는 키에 `이름 [미검증]`을 추가한다. 원래 본문, segment ID, speaker ID, 단어, 숫자, 타임라인은 그대로 유지한다. 기존 확인 이름을 덮어쓰지 않는다.

`people_v3`, `decisions_v3`, `embeddings_v3`, `identity_confirmation_metadata`에는 접근하지 않는다. `named/`와 그 manifest도 수정하지 않는다. 사람 확인의 원본 파일 SHA 바인딩과 확인 취소는 기존 identity 소유 코드가 관리한다.

## 로컬 영상 자원 제한

`.m4a` 등 음성 파일이거나 영상이 없으면 `video_unavailable`을 명시하고 자기소개·제공된 문맥만 처리한다. 프레임 예산을 다 쓰거나 시간·화자가 모호한 구간을 생략하면 `frame_limit`, `frame_byte_budget`, `ambiguous_or_missing_timing` 등 이유를 세그먼트별로 남긴다. 침묵 판정이나 본문 삭제로 처리하지 않는다.

ffmpeg는 로컬 파일에서 필요한 시각으로 seek한 뒤 한 프레임씩 stdout으로 내보낸다. 부모는 pipe를 제한 크기로 읽고 JPEG 크기를 검사한다. decoder와 filter의 thread 한도는 각각 2이며, 허용 프로토콜은 `file,pipe`이다. 전역 로컬 helper와 같은 OS mutex를 사용해 모델 helper와 겹쳐 실행하지 않는다.

추출 전 여유 메모리 8GiB와 정상 pressure를 확인하고, 별도 프레임 worker가 부모 PID·생성 시각·생존, timeout, RSS 4GiB 상한, 여유 8GiB·pressure를 감시한다. 부모가 죽어도 worker는 ffmpeg를 종료한다. 요청 측은 timeout·초과 출력·오류에서 전체 프로세스 그룹을 종료한다. worker 환경은 기존 credential 제거·offline 환경을 재사용한다. 모델을 로드하거나 다운로드하지 않으며, 모델의 3GiB 자격 판정이나 prepared-only 정책을 바꾸지 않는다.

## 검증 기록과 한계

초기 passthrough 구현에 `.venv/bin/python -B -m unittest tests.test_speaker_names -v`를 실행해 후보 누락과 적용 표시 누락을 `FAIL` 2건으로 재현했다. 추가로 제삼자 소개를 자기소개로 받아들이는 결함을 테스트로 재현한 뒤 원래 세그먼트까지 검사하도록 수정했다.

실제 Scribe 응답 형태를 본뜬 합성 한 세그먼트·혼합 word speaker `0/1` 입력에서도 turn 분리 누락을 먼저 `FAIL`로 재현했다. 두 화자의 자기소개, 자기소개와 `안녕하세요.`로 구성한 입력의 두 시각별 frame 근거, 원본 불변과 parent/word range 연결, 타임스탬프 누락·겹침·본문 불일치 unknown 경로를 검사했다. 개인 영상이나 실제 전사 본문은 사용하지 않았다.

최신 담당 C 및 통합 경로 검사:

```text
.venv/bin/python -B -m unittest tests.test_speaker_names tests.test_optional_pipeline_modes -q
Ran 59 tests
OK
```

배치 밖의 동시 화자를 누락하는 결함도 먼저 `FAIL`로 재현한 뒤 전체 타임라인 검증으로 수정했다. 임시 복사본에서 인용문 존재 검사 제거, 제삼자 소개 허용, 기존 확인 이름 강제 덮어쓰기, 배치별 겹침만 검사, 혼합 화자 turn view 제거의 다섯 변이를 각각 주입했다. 다섯 경우 모두 정상본 exit 0, 변이본 exit 1과 `AssertionError`로 검출됐다. 공유 작업공간의 원본에는 변이를 적용하지 않았다.

ffmpeg pipe·자원 guard·부모 사망·API 경계는 stub/mock으로 검사했다. 유료 API 호출, 실제 영상 업로드, 실모델 추론, CER 평가, 실제 이름 정답 대조는 실행하지 않았다. 이 검증은 계약과 보존·격리 경로의 검사이며 정확도나 실명 확정의 성공 증거가 아니다.
