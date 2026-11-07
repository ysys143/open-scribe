# 로컬 검토 UI

## 실행 계약

UI는 CLI 실행 중에만 localhost의 임의 포트에서 동작한다. 기본 브라우저의 새 탭을 열며, 별도 데몬·Node 서버·모델 호출을 시작하지 않는다. 작업 탭의 heartbeat가 사라지면 5초 유예 후 종료한다. 마지막 답변 후 닫기 확인에서 ‘예’를 선택하면 저장된 상태를 확인한 뒤 탭과 서버를 종료한다. 종료 거부 브라우저는 실패로 표시한다. 새로운 방문 기록을 추가하지 않는다.

```sh
scribe dashboard
scribe review catalog --json
scribe review open JOB --questions questions.json --events-json
scribe review state JOB --json
scribe review apply JOB --input answer.json --json
scribe review export JOB --json
scribe speakers gallery
scribe speakers list
scribe speakers show PERSON
```

설치본이 아직 이 명령을 지원하지 않으면 저장소에서 `bash scripts/launchers/scribe.sh` 뒤에 같은 인자를 전달한다. 일반 설치본 교체는 별도 작업이다.

## 질문과 저장

`questions.json`은 질문 배열이다. 원본 세그먼트 ID는 `review state`와 UI의 전사 정보를 기준으로 한다. 혼합 word speaker는 원문 문자 범위를 보존하는 단일 화자 단위로 나뉘며, ID에 원래 세그먼트와 word range의 연결을 유지한다.

```json
[{"id":"speaker-1","kind":"speaker","prompt":"이 목소리는 누구인가요?","segments":["s1"],"choices":["김민수","판단하기 어려움"]}]
```

`kind`는 `speaker`, `comparison`, `mapping`, `overlap`이다. 모든 질문에는 `판단하기 어려움`을 포함한다. 질문 파일이 없으면 등록된 화자와 원래 화자 namespace를 사용한 기본 질문을 준비한다. 이름을 자동 확정하지 않는다.

에이전트는 선택적으로 질문의 `spec`에 json-render의 `root`·`elements` 명세를 제공한다. 사용 가능한 컴포넌트는 `Stack`, `Text`, `SegmentPlayer`, `ClipComparison`, `SpeakerAssignment`, `OverlapReview`이다. `Text`는 `text` 속성, 나머지 작업 컴포넌트는 `question`에 해당 질문 ID를 받는다. `Stack`은 `children`으로 조합한다. 재생·선택 컴포넌트 누락, 미등록 컴포넌트, 다른 질문 참조, 도달 불가능한 항목은 거절한다. UI 저장·종료·경로 안내는 고정 영역이다.

정본은 작업 폴더의 `agent-review/review.json`이다. 원본 파일 SHA-256과 revision에 연결해 원자적으로 저장한다. `answer`는 확정 답변, `draft`는 입력 중 상태다. `mappings`는 세그먼트 ID별 표시 이름이며, `people`는 명시적으로 선택한 영구 인물 ID다. `corrections`는 원문을 대체하지 않는 사용자 보충이다. 다른 질문 범위의 변경은 거절한다.

```json
{"operation":"answer","revision":1,"source_sha256":"STATE에서_읽은_해시","question":"speaker-1","value":{"choice":"김민수","mappings":{"s1":"김민수"}}}
```

상태·버전 충돌은 다시 읽은 뒤 검토한다. 원본이 바뀌면 UI의 재검토 동작 또는 명시적 `rebase`로 이전 기록을 보관하고 새 검토를 시작한다. 저장 실패는 완료로 알리지 않는다. UI와 CLI 이벤트는 실제 저장 경로를 포함한다. 에이전트는 성공 이벤트를 읽고 사용자에게 `[PATH]에 있는 검토 메모리를 갱신했습니다`라고 알린다.

## 화자와 음성

이름 확인과 재사용 화자 등록은 같은 화면에서 선택한다. 같은 이름만으로 기존 인물에 합치지 않는다. 재생용 대표 음성은 `speaker-samples/`에 별도로 보관하고, source·전사 해시·구간·인물 ID를 기록한다. 사용자 확인된 인물 ID 연결이 있어야 클립을 저장한다. 모델용 임베딩은 생성하지 않는다. 등록 재시도는 같은 intent와 샘플 ID를 사용한다.

시각과 단독 발화 근거가 있는 5–10초 구간을 최대 두 개 보관한다. 충분한 클립이 없으면 이름만 등록한다. 서로 겹친 화자·혼합 단어 화자·본문 대응 불명 구간은 대표 클립으로 사용하지 않는다. 원본 이동 시 같은 바이트 해시의 파일을 다시 연결할 수 있다. 다른 음성으로 대체하거나 자동 다운로드하지 않는다.

녹취 출력은 원래 발화를 보존하며 사용자 보충을 구분한다. 원본·사용자 편집 출력은 덮어쓰지 않는다. 최종 요약은 이 검토 상태와 전사를 읽은 에이전트가 작성한다. 인터뷰 제출 완료와 원음 전체 검수 완료는 별개다.

## 빌드와 검증

`ui/`에서 `npm ci`, `npm run check`, `npm test`, `npm run build`를 실행한다. 빌드는 runtime 안에 정적 번들·해시 manifest·라이선스를 생성한다. 설치기는 번들의 해시를 검증해 복사한다. 사용자 실행에는 npm이 필요하지 않다.

합성 원음과 임시 저장소 검증은 `tools/ui/demo.py`, 실제 기본 브라우저 지연 계측은 `tools/ui/measure.py SESSION_JSON --runs 20`을 사용한다. 기본 브라우저가 이미 실행된 상태와 꺼진 상태의 시간은 구분한다. 타 브라우저의 자동 닫힘을 확인하지 않았으면 호환성을 선언하지 않는다.

## 텍스트 추론과 사용자 확인의 구분

에이전트의 텍스트 특정은 `operation=inference`로 따로 기록한다. `value`의 키는 세그먼트 ID이고, 값은 `name`과 `evidence` 목록이다. evidence의 `segment`·`quote`는 실제 원문의 ID·인용과 일치해야 한다. basis는 `text_context`로 저장되며 사용자 답변으로 바꾸지 않는다. 기본 질문 생성은 이미 특정한 단위를 제외한다. 실제 사용자 답변은 추론을 대체할 수 있지만, 서로 충돌하는 사용자 확인이나 삭제된 인물 ID는 재검토가 필요하다.

예시:

```json
{"operation":"inference","revision":0,"source_sha256":"STATE에서_읽은_해시","value":{"s1":{"name":"김민수","evidence":[{"segment":"s1","quote":"저는 김민수입니다."}]}}}
```

`review catalog --json`의 `ui_schema`·`ui_prompt`는 빌드에 사용한 실제 컴포넌트 카탈로그에서 생성된다. 개발 도구는 Node.js 24 이상을 사용한다.

사용자가 이름 연결을 정정하거나 전사를 바꾸면 기존 대표 클립을 확인된 근거로 재사용하지 않는다. `speakers forget --confirm`은 재생용 DB 연결과 수정되지 않은 관리 클립도 정리한다. 사용자가 수정한 클립과 기존 검토 출력은 보존·보고하며, 삭제된 인물 ID를 포함한 새 출력은 재검토 전까지 보류한다. 원래 ASR 전사와 사용자 답변의 역사 기록은 원본 자료로 남긴다.

여러 이름 대응을 한 번에 선택받을 때는 질문의 `choice_mappings`에 선택지별 적용 범위를 명시한다. 예를 들어 `{"대응 1":{"s1":{"name":"김민수","person":"실제 인물 ID"},"s2":"박영희"}}` 형식이다. 인물 ID가 없으면 해당 녹취의 표시 이름만 반영한다. 이름만 보고 기존 인물에 합치지 않는다. `판단하기 어려움`에는 확정 이름을 연결할 수 없다.

원래 시간이 없거나 잘못된 구간은 플레이어에서 현재 위치를 시작·끝으로 지정할 수 있다. 이 값은 답변의 `time_ranges`에 사용자 지정 범위로 저장되며 ASR의 시간과 원문을 수정하지 않는다. 수동 범위로 판단한 발화는 기존 자동 정렬을 재사용해 대표 클립으로 등록하지 않는다. 이때 인물 이름은 저장하고 음성 예시는 보류한다.

긴 화자 그룹은 처음에 대표 원음 최대 두 개만 보여 주고, 필요할 때 나머지 근거를 펼쳐 듣는다. 질문의 선택적 `representatives`에는 적용 범위 안의 ID를 최대 두 개 지정한다. 재생은 대표 구간 최대 10초부터 시작하고 원래 전사 범위를 변경하지 않는다. 같은 사람으로 이름을 일괄 지정한 구간은 명시적인 인물 그룹으로 등록하며, 구간별 이름을 수정하면 별도 인물로 구분한다. 서로 다른 사람의 이름이 같다는 이유로 기존 인물을 합치지 않는다. `직접 지정`은 기본 선택지 외의 사용자 수정 결과를 기록하는 내장 답변이다. 기존 화자의 대표 음성은 이름 선택 옆에서 비교해 들을 수 있다.

생성 UI는 이 앱의 `ui_rules`를 따른다. literal props와 Stack 트리만 사용하고 조건부 숨김·이벤트·반복·상태 표현식을 넣지 않는다. 최대 128요소·깊이 32이며, 재생과 선택 요소가 모두 실제로 표시돼야 한다. 서버는 질문 파일을 저장하고 탭을 열기 전에 이를 검증한다. 전체 json-render 기능을 그대로 노출하는 계약은 아니다.

기존 `speakers confirm`의 확인은 현재 원본 해시에 연결된 기록일 때만 재사용한다. 이 사실은 `confirmed_names`에 기존 사용자 확인으로 표시하고 추론과 구분한다. 출처가 없는 과거 이름을 자동으로 확정하지 않는다. 이름이 알려져 있어도 겹침 내용 검토는 별도 항목으로 남는다.
