# 유사 오픈소스 아키텍처와 open-scribe 반입 검토

조사 기준일: 2026-11-04 KST. 저장소·커밋·라이선스 원문은 주로 2026-11-04 KST에 확보했고 추가 원문·소스 대조·인용 감사·작성은 2026-11-05 KST에도 수행했다. open-scribe 기준 commit은 `3880fcfe007965711cb89a2f4778db09d2918bfd`다[1][2]. 아래 날짜는 별도 표시가 없으면 관측한 commit의 UTC 날짜이며, 개별 파일의 작성일이나 정식 릴리스일을 뜻하지 않는다.

## 요약

- [추론] 우선 반입할 구조는 엔진 추가보다 공통 결과 모델과 완료 판정이다. 현재 반환형은 `Optional[str]`이고, 실제 병렬 API 경로는 실패 청크를 제외한 문자열 목록을 반환한다[1][40]. [추론] WhisperX·Buzz·Scriberr의 구조화 결과를 참고하면 누락과 시간값의 의미를 후처리 전에 보존할 수 있다[23][29][33].

- [추론] 다운로드는 엔진의 실행·가용성 검사와 분리하고, 검증한 임시 파일을 최종 경로에 반영하는 방식이 적합하다. Vibe의 크기·헤더·선택적 해시 검사, Buzz의 취소 가능한 다운로드, Handy의 HTTP 실패 시험이 각각 근거다[30][28][38].

- [추론] 캐시 개선은 Scriberr의 작업 상태 복구와 Subgen의 중복 요청 억제를 참고하되 새로 설계해야 한다. [불명: 미발견] 읽은 코드에서 요약 프롬프트까지 포함한 단계별 캐시나 실패 청크만의 영속 재개가 완성된 모범 사례는 찾지 못했다[35][36][3].
- 실제 비교 대상은 10개, 심층 사례는 두 축 안의 5개다. 초기 후보 14개와 추가 후보 Handy·TranscriptionSuite를 합쳐 16개를 확인했다. Whishper·insanely-fast-whisper는 최근 12개월 commit 조건 미충족으로 제외했고 나머지 4개는 상세 비교표 밖의 예비 후보로 남겼다[18][19].

- [추론] 직접 코드 반입 검토는 MIT·BSD·Apache로 확인된 파일에 한정하고, GPL 계열 후보는 구조 참고로 분리하는 것이 현재 MIT 저장소의 검토 부담을 줄인다[6][7][15][17][18][21][22]. Hyprnote의 현재 목적지는 Anarlog이며 community MIT와 enterprise 상업 라이선스의 경계가 있어 저장소 루트의 표기만으로 파일 반입을 판단할 수 없다[20].

## 조사 질문과 판정 방법

질문: 유사 오픈소스의 어떤 구조를 open-scribe에 반입할 수 있는가?

하위 질문은 네 개다.

1. 실재하는 후보 중 최근 12개월 commit과 겹치는 기능 2개 이상을 확인할 수 있는가?

2. 다운로드·엔진 추상화·설정·배포·UI를 어떤 경계로 나누는가?

3. 결과 모델·분할 병렬·캐시 재개·후처리·출력·테스트를 어떻게 연결하는가?

4. 어느 근거 파일의 구조를 어느 open-scribe 파일에 반입하며 작업량·위험·라이선스는 무엇인가?

심층 축은 A「입력·엔진 자원 경계」와 B「결과·영속 실행 경계」로 제한했다. A 안에서 Speaches·Buzz·Vibe 3개, B 안에서 WhisperX·Scriberr 2개를 분석한다. 다른 후보의 짧은 비교는 이 두 축의 보조 근거이며 별도의 성능·화자 알고리즘 심층 조사는 아니다.

기능 중복은 파일·URL 입력 전사, 복수 엔진, 번역·요약, 자막·텍스트 출력, 전사문 교정 중 적어도 2개로 판정했다. 수동 편집과 자동 교정의 구현 차이는 남겨 둔다. 활동성은 기준일 이전 기본 브랜치에서 GitHub commits API가 반환한 마지막 commit으로 확인했다. PR·이슈 작성일·별 개수·검색 크롤링 날짜로 대체하지 않았다. 이 기준은 최소 활동 확인이며 유지보수 응답성이나 코드 품질 점수는 아니다.

검색은 내장 웹 검색으로 시작했고, 본문은 Jina Reader를 먼저 시도했다. 429가 난 저장소는 내장 웹 조회로 재확인하고, 상세 코드는 허용된 얕은 clone에서 읽었다. 모델·앱·테스트를 실행하지 않았으므로 아래의 테스트 항목은 시험 코드의 존재와 내용에 관한 관찰이다. 출처별 원문 구절·commit·조회일은 `/tmp/open-scribe-research-2026-11/t1/source-notes.md`에 보존했다.

## 후보 선정과 비교

### 선정된 10개: 입력·엔진·설정·배포·UI·테스트

아래의 고정 snapshot과 실제 읽은 파일은 출처 7~16의 원문 묶음이다. 시간 범위는 2025-11-04~2026-11-04다. 모두 관측 commit이 기간 안에 있고, 표의 중복 기능을 두 개 이상 확인했다. `테스트` 열은 실행 성공을 뜻하지 않는다.

| 프로젝트 / 관측 commit | 겹치는 기능·입력 / 엔진 경계 | 설정·배포·UI | 확인한 테스트·반입 관점 / 루트 라이선스 |
|---|---|---|---|
| WhisperX / `5d3678b` 2026-10-22 | 파일 전사·복수 텍스트/자막 출력; ASR·정렬·화자 부여가 별도 단계 | Python 라이브러리·CLI, CLI 인자와 모델 캐시 경로 | 시간 보간·정렬 실패 회귀 시험; 결과 계약·writer 참고 / BSD-2-Clause [7][23][24][25]. |
| Speaches / `993994f` 2026-04-18 | 파일 전사·번역·복수 모델; OpenAI 호환 API와 executor/registry 분리 | Python 서비스·Docker/Compose, 환경 기반 설정·선택적 UI | TTL·사용 중 unload 차단·API 타임스탬프 시험; 모델 수명주기 참고 / MIT [8][26][27]. |
| Buzz / `de7484b` 2026-11-04 | 파일·YouTube·마이크 전사, 번역·자막; ModelType과 transcriber 구현 분리 | Python/PyQt 데스크톱, 설정 저장·모델 관리자·편집/재생 UI | 다운로드·전사·DB·큐·UI 시험; 설정 snapshot·모델 확보 참고 / MIT [9][28][29]. |
| Vibe / `da8c2ca` 2026-10-30 | 파일·웹 URL·마이크 전사, 요약·번역·일괄 처리; 데스크톱과 별도 서버 프로세스 | Tauri/Rust·React, 모델·설정 UI, HTTP API | 큐·저장·출력·설정 시험; 스트림 완료 확인·검증 후 파일 반영 참고 / MIT [10][30][31][32]. |
| Scriberr / `a353078` 2026-09-20 | 파일·YouTube·폴더 전사, 요약·대화; capability·adapter·registry 경계 | Go 서비스·React UI, 관리형 Python 모델 환경, Docker·CLI·API | adapter·큐·DB·API 시험; 입력 규격·작업 상태 참고 / MIT [11][33][34][35]. |
| Subgen / `5f98ed6` 2026-08-06 | 파일/폴더 전사·번역·자막, 미디어 서버 webhook·ASR endpoint | Python 서비스·Docker, 환경변수·호환 별칭, 서비스 연동 중심 | 큐·skip 조건·endpoint 시험; 중복 억제·오디오 시작 offset 참고 / MIT [12][36]. |
| transcribe-anything / `3b7a860` 2026-10-26 | 로컬 파일·URL 전사, 번역·자막·다중 backend 라우팅 | Python CLI/API/server, backend별 격리 환경과 사용자 캐시 경로 | URL/로컬 입력·backend 인자·자막 변환 시험; 의존성 격리 구조 참고 / MIT [13][37]. |
| Meetily / `07c4dfd` 2026-11-02 | 회의 녹음·파일 import 전사·재전사·요약; 엔진 enum과 provider trait이 공존 | Tauri/Rust·Next.js, DB·모델 readiness/다운로드·요약 설정 UI | readiness·요약 관련 시험; 읽은 실시간 worker는 `NUM_WORKERS = 1` / MIT community [14]. |
| Whisper-WebUI / `c3bb3b1` 2025-12-29 | 파일·YouTube·마이크 전사, 번역·자막; factory와 BaseTranscriptionPipeline | Python/Gradio·Docker, YAML 기본값·모델별 경로, 별도 backend task DB | 전사·VAD·번역·task status 시험; Pydantic 세그먼트·공통 파이프라인 참고 / Apache-2.0 [15][39]. |
| Handy / `82dfab9` 2026-11-02 | 오프라인 음성 전사·복수 모델·후처리·텍스트 입력 전달 | Tauri/Rust 데스크톱, 모델 관리자·설정·history UI | 로컬 HTTP 서버로 다운로드 이상 응답 재현; 모델 확보 실패 시험 참고 / MIT [16][38]. |

### 같은 10개: 결과·분할 병렬·캐시 재개·후처리·출력

`[불명: 미발견]`은 해당 칸의 경로를 읽었으나 기능을 입증하는 구현을 찾지 못했다는 뜻이다. 저장소 전체에 기능이 없다는 판정은 아니다. 모델 파일 캐시, 전사 결과 캐시, 작업 재투입, 실패 청크 재개를 구별했다.

| 프로젝트 | 결과 모델·분할/병렬 | 캐시·재개 | 후처리·출력 |
|---|---|---|---|
| WhisperX | segment·word·char·언어 TypedDict; VAD 단위 batch와 단계별 모델 해제 | 모델 cache-only 옵션; 읽은 CLI의 단계 결과는 메모리 목록; 디스크 checkpoint는 [불명: 미발견] | 전사→정렬→선택적 화자 부여→writer; JSON/TXT/SRT/VTT/TSV [23][24][25]. |
| Speaches | 구조화 API 응답·SSE event, executor 내부 batch | Hub 모델 파일 캐시와 ref-count/TTL; 요청 단위 영속 작업 재개는 [불명: 미발견] | 응답 포맷에 따라 JSON/상세 JSON/텍스트/자막 변환; 일부 executor는 `diarized_json` 거부 [26][27]. |
| Buzz | ms 단위 Segment, task status·error·segments; 파일 큐와 엔진 구현을 분리 | queued task에 옵션 deepcopy; 다운로드 재시도·중단; 청크 checkpoint는 [불명: 미발견] | 세그먼트 번역·화자 필드, TXT/SRT/VTT와 summary plugin 경로 [9][28][29]. |
| Vibe | 내부 1/100초 Segment; 모델 한 번 로드 후 파일별 순차 큐; 스트림 완료 표식 검사 | 프로젝트별 JSON·오디오 사본; 다운로드 `.part`; 읽은 큐의 청크 영속 재개는 [불명: 미발견] | 편집·요약·화자명·다중 내보내기; 저장 성공과 export 성공을 분리해서 표시 [10][30][31][32]. |
| Scriberr | 공통 TranscriptResult·capability; worker 수 제한·프로세스 취소 | pending은 시작 시 재투입, processing 잔여는 failed; 실패 지점 이어하기와는 다름 | 전처리 hook·JSON 결과·요약/대화; 일부 VAD/노이즈 전처리 코드는 placeholder [11][33][34][35]. |
| Subgen | stable-ts 결과·파일/요청 큐; 동시 작업 제한과 모델 로드 lock | 실행 중/대기 중 중복 억제; 업로드 오디오+task+language 해시; 디스크 청크 재개는 [불명: 미발견] | 자막 regroup·시작 offset 보정·기존 자막 skip, SRT/LRC [12][36]. |
| transcribe-anything | backend 산출물을 공통 출력 폴더로 수집·변환 | backend 환경·모델 캐시는 별도; 단계별 영속 재개는 [불명: 미발견] | JSON에서 자막/텍스트 변환·선택적 정렬; URL 다운로드 코드는 무가공 반입 제외 후보 [13][37]. |
| Meetily | sequence_id·부분 여부·녹음 상대 시작/끝 필드; 읽은 실시간 경로는 직렬 worker | DB에 회의·전사 저장, 원본 오디오 기반 재전사; 청크 checkpoint는 [불명: 미발견] | 요약 provider·template·편집 UI; README의 PRO 기능은 community 기능으로 계산하지 않음 [14]. |
| Whisper-WebUI | 공통 Segment/Word, 전처리→전사→후처리 인터페이스 | `cache_parameters`는 YAML UI 기본값 저장; 작업 DB의 paused/retrying enum만으로 재개 실행을 입증할 수 없음 | VAD/BGM 처리·번역·선택적 화자 처리, TXT/SRT/WebVTT [15][39]. |
| Handy | 녹음→엔진→후처리→입력 전달·history; 장문 설정 UI가 있어도 처리량 비교는 수행하지 않음 | 검증 가능한 부분 다운로드와 로컬 history; 전사 청크 재개는 [불명: 미검색] | LLM 후처리 뒤 사용자 hook, clipboard/직접 입력; 자막 출력은 [불명: 미검색] [16][38]. |

### 나머지 6개: 기간 제외와 예비 후보

| 후보 | 관측 commit UTC / 라이선스 | 확인한 중복 기능 | 선정 결과 |
|---|---|---|---|
| noScribe | `acccc92` 2026-10-29 / README·API가 GPL-3.0 표시 | 파일 전사·편집/검증 UI | 기간·중복 기능 조건 충족; 예비 후보; 본문 파일별 구조·의존성 라이선스는 [불명: 미검색] [17]. |
| Whishper | `adcd186` 2025-08-15 / AGPL-3.0 | URL/파일 전사·번역·자막 편집/출력 | 최근 12개월 commit 조건 미충족으로 제외; 기능이 매력적이라는 이유로 활동 조건을 완화하지 않음 [18]. |
| insanely-fast-whisper | `0fed9a4` 2024-05-27 / Apache-2.0 | 파일 전사·번역·JSON 출력 | 최근 12개월 commit 조건 미충족으로 제외; 다른 활성 repo가 wrapper로 쓰는 사실과 원 repo 활동은 구별 [19]. |
| Hyprnote → Anarlog | `428903e` 2026-11-01 / community MIT·enterprise 상업 라이선스 | 회의 전사·요약·SQLite/Markdown 출력 | 조건 충족한 예비 후보; 이전 제품명과 현재 코드의 동일 기능 범위는 [불명: 미검색]; 라이선스 경계를 먼저 조사할 필요 [20]. |
| VoiceInk | `5c95ff9` 2026-11-04 / README·LICENSE는 GPLv3, API는 NOASSERTION | 로컬 음성 전사·텍스트 후처리 | 조건 충족한 예비 후보; API의 NOASSERTION을 MIT로 해석하지 않음; Swift 앱의 파일별 반입 가능성은 [불명: 미검색] [21]. |
| TranscriptionSuite | `541bde9` 2026-09-24 / GPL-3.0 | 파일 import 전사·복수 backend·로컬 노트 기능 | 추가 검색으로 발견한 예비 후보; Electron+Python 서버 경계의 코드 추적은 [불명: 미검색] [22]. |

## 심층 축 A: 입력·엔진 자원 경계

### 사례 1 — Speaches: 모델 검색·파일 확보·메모리 점유를 분리

`WhisperModelRegistry`가 원격/로컬 목록과 필요한 파일을 관리하고 `WhisperModelManager`가 장치·worker 설정으로 모델을 로드한다. `SelfDisposingModel`은 RLock, 참조 수, TTL 타이머와 context manager를 사용한다. TTL 양수는 마지막 사용 후 지연 해제, 0은 즉시 해제, 음수는 유지다. 사용 중인 모델의 unload는 오류를 낸다[27][26].

[추론] open-scribe의 `get_transcriber()`를 이식 위치로 삼아 engine capability, model artifact, runtime handle을 구분할 수 있다. `is_available()`가 다운로드·엔진 설치·가중치 로드를 한꺼번에 수행하지 않도록 계약을 정하면 CLI·bot에서 같은 준비 상태를 해석하기 쉽다. 다만 현재 CLI 한 번 실행의 이점과 장기 실행 bot의 이점은 다르므로 TTL 값을 그대로 복사할 근거는 없다[2][1][26][27].

`tests/model_manager_test.py`는 TTL 해제·재사용 시 TTL 초기화·사용 중 삭제의 409 응답 등을 검사한다[8]. 모델 fixture가 필요한 시험이므로 이번에는 실행하지 않았다. [추론] 반입 시 모델 객체를 fake로 대체한 수명주기 시험과 실제 로컬 엔진 smoke test를 분리할 수 있다. 이 보고서는 어느 장치의 처리량이 더 높다고 판단하지 않는다.

### 사례 2 — Buzz: 엔진별 모델 확보와 작업 옵션 snapshot

`ModelType`, `TranscriptionModel`, `ModelDownloader`가 구별되어 있고 API 엔진은 로컬 가중치 경로와 다른 분기를 가진다. Hub 다운로드는 취소할 수 있도록 자식 프로세스에서 수행한다. 직접 HTTP 경로는 Range 재개 시도와 200 응답 시 처음부터 쓰기, 선택적인 SHA-256 검사를 가진다. 모든 backend·URL이 동일한 무결성 검사를 보장한다는 뜻은 아니다[28].

`FileTranscriptionTask.__post_init__()`는 전사 옵션을 deepcopy한다. Segment는 시작/끝을 ms로 정의하고, task는 queued/in_progress/completed/failed/canceled/skipped와 error를 보존한다. [추론] open-scribe에서도 큐에 넣을 때 엔진·언어·모델·후처리 설정 snapshot을 고정하면 실행 중 환경 설정이 바뀌어 작업 의미가 달라지는 문제를 줄일 수 있다[29][2].

[추론] Python 파일이라도 GUI signal·Qt worker·전역 monkey patch까지 함께 들여오는 방식은 결합 범위를 키운다. HTTP 전송·해시 검증·취소 상태의 작은 함수를 추출하고, CLI 표시 부분을 현재 progress 계층에 맞추는 편이 검토하기 쉽다. Buzz의 첫 다운로드 `.downloading` 파일을 완료 후 옮기는 처리와 예외 시 삭제를 읽었으므로, 모든 취소 상황에서 부분 파일이 남는다고 일반화하지 않았다[28].

### 사례 3 — Vibe: 검증 후 파일 반영과 스트림 완료 판정

`download.rs`는 `.part` 경로, 최소 크기, GGML/GGUF 헤더, catalog의 선택적 크기·SHA-256을 검사한 뒤 파일을 최종 경로에 옮긴다. 기존 목적 파일을 교체할 때 backup으로 이동하고 교체 실패 시 복원을 시도한다. catalog 정보가 없는 사용자 URL은 크기·헤더 검사로 검증 강도가 낮아진다고 코드가 명시한다[30].

`transcribe.rs`는 HTTP 스트림에서 Progress/Segment/Result/Error를 구별하고, Result 완료 표식 없이 스트림이 끝나면 성공 결과로 반환하지 않는다. 서버의 exit 상태와 최근 stderr를 포함하는 오류 경로도 있다. 단, 사용자 취소는 별도 분기이므로 모든 중단이 동일한 실패로 처리된다고 쓰지 않는다[31].

`use-transcribe-queue.ts`는 모델을 한 번 로드한 뒤 여러 파일을 순서대로 처리한다. 일괄 처리가 여러 모델 프로세스의 동시 실행과 동의어가 아니다. [추론] open-scribe는 원격 요청 동시성과 로컬 모델 메모리 동시성을 별도 한도로 관리할 수 있다. 현재 `WorkerCalculator`의 메모리 표는 코드에 있는 추정 상수이므로 실측 자원 한도로 승격해서는 안 된다[5].

## 심층 축 B: 결과·영속 실행 경계

### 사례 4 — WhisperX: 단계 결과와 출력기를 연결하는 공통 데이터

`schema.py`는 전사 segment, aligned segment, word, char를 나누고 `avg_logprob`를 선택 필드로 둔다[23]. `transcribe.py`는 ASR 결과 목록을 만든 뒤 모델을 해제하고 정렬과 선택적 화자 부여를 거쳐 writer에 넘긴다[24]. `utils.py`의 writer는 같은 결과 dict에서 텍스트·JSON·SRT·VTT·TSV를 만든다[25]. 알고리즘의 정확도·화자 재식별 성능은 이 조사에서 다루지 않는다.

[추론] open-scribe는 `TranscriptionResult`에 `segments`, 선택적 `words`·`speaker`, `language`, `engine`, `model_revision`, `timing_source`, `status`, `chunk_errors`를 두고 렌더링을 마지막에 수행하는 방향을 검토할 수 있다. `timing_source`·`status`·`chunk_errors`는 WhisperX를 그대로 베낀 필드가 아니라 현재 문자열 반환·실패 누락·청크 시작 시간 경로를 보완하기 위한 제안이다[1][40][23].

WhisperX writer는 초 단위 시간값을 1,000배해 표시하고 Buzz Segment는 ms, Vibe의 데스크톱 수신 경로는 서버 초를 100배한 내부 정수다[25][29][31]. [추론] 내부 표준은 정수 ms 등 한 단위로 고정하고, 청크 시작 시간·세그먼트 추정 시간·단어 정렬 시간을 출처 필드로 구분해야 한다[40][23]. 시간값이 없는 결과에 0이나 가상의 종료 시간을 채우는 설계는 결과의 의미를 바꿀 수 있다.

WhisperX의 읽은 CLI는 중간 결과를 메모리에 모으며 마지막 단계에서 writer를 호출한다. [불명: 미발견] 이 경로에서 ASR·정렬별 영속 checkpoint와 작업 재개는 찾지 못했다. [추론] writer 패턴을 참고하는 일과 파일 길이와 무관한 메모리 사용·중간 재개를 확보하는 일은 별도 작업이다[24][25].

### 사례 5 — Scriberr: capability·입력 규격과 재시작 시 상태 복구

`interfaces.go`는 ModelCapabilities, ParameterSchema, AudioInput, TranscriptResult와 준비·검증·전사 adapter를 정의한다. `AudioInput`에는 포맷·sample rate·channels·duration·size·temporary path가 있고, 결과에는 text·segments·words·언어·모델·처리시간이 있다. [추론] 같은 입력을 엔진마다 재해석하게 두는 대신 입력 정규화와 capability 검증을 factory 바깥의 단계로 둘 수 있다[33][2][4].

`pipeline.go`의 기본 전처리는 mono/16kHz/WAV 변환이다[34]. 읽은 구현은 전처리 실패를 로그로 남긴 뒤 원래 입력으로 계속 진행한다[34]. VAD·noise reduction에는 placeholder도 존재한다[34]. [추론] 구조를 참고하더라도 open-scribe에서는 필수 변환 실패와 선택적 개선 실패를 구분해야 한다. 선언한 hook이나 이름만으로 전처리·후처리가 실제 수행된다고 판정하지 않았다[34].

`TaskQueue.Start()`는 먼저 processing 잔여를 failed로 바꾸고 재시작 오류 메시지를 저장한 뒤, pending 작업을 한 번 재투입한다[35]. recover 함수에서 채널이 가득 차면 pending 상태를 유지하며 경고를 남긴다[35]. worker 상한·취소 context·실제 자식 프로세스 등록도 존재한다. [불명: 미발견] 읽은 경로에서 실패 청크별 디스크 checkpoint를 이용한 이어하기는 찾지 못했다[35].

[추론] open-scribe의 단계 완료 플래그를 버릴 필요는 없지만, 그 아래에 실행 attempt와 청크 상태를 저장해야 부분 성공을 전체 완료로 오인하는 경로를 차단할 수 있다. Subgen의 중복 억제는 queued/processing 집합과 요청 해시로 동시 중복을 막는 참고 자료다. 이 메모리 큐를 그대로 재시작 내구성이 있는 캐시로 부를 수는 없다[3][35][36][40].

## open-scribe 적용 검토

### 실제 기준선과 선행 조건

실제 factory는 `src/cli.py:get_transcriber()`다[2]. 반환 계약은 `src/transcribers/base.py`의 문자열이다[1]. `src/transcribers/__init__.py`를 factory라고 가정하거나 문서의 `BaseTranscriber -> TranscriptionResult` 예시를 현재 구현으로 계산하지 않았다. 아래 제안은 기존 fallback이 CLI에서 운영 중이라는 전제를 사용하지 않는다.

현재 작업 키는 SQLite의 `(video_id, engine)`이다[3]. CLI가 이 키로 전사·요약 완료 플래그와 경로를 재사용하고, 로컬 입력의 식별자는 파일 stem 기반이다[2]. [추론] 동일 파일명·서로 다른 오디오 또는 요약 모델·프롬프트 변경을 구별하려면 미디어 content hash와 단계별 설정 fingerprint를 새로 도입해야 한다[2][3]. 비교 프로젝트에서 이 조합의 완성 구현을 확인한 것은 아니다.

API 병렬 전사의 `valid_texts` 필터는 실패 결과를 버리고, `WorkerPool.merge_results()`도 실패 청크를 경고하면서 성공 텍스트를 합친다. [추론] 결과 모델·완료 판정 변경은 이 실제 병합 경로와 CLI의 DB 완료 갱신을 함께 다뤄야 한다. 새 타입만 선언하고 호출부를 문자열 경로에 그대로 두는 작업으로는 이 결함을 해결할 수 없다[40][5][2].

### 반입 후보 8개

모든 효과·작업량·우선순위는 코드 관찰에서 도출한 [추론]이다. S는 제한된 helper와 호출부 변경, M은 여러 모듈의 계약·저장·시험 변경, L은 DB 이행과 실행 흐름 전반 변경을 뜻하며 기간·성능 실측값이 아니다. P0는 결과의 신뢰성, P1은 재시작·준비 상태, P2는 운영 편의 순으로 부여했다.

| 우선순위·반입 대상 | 고정 commit 근거 파일 | open-scribe 대상 파일 | 효과·작업량 | 반입 형태·라이선스·위험 |
|---|---|---|---|---|
| P0 공통 결과·시간 출처 | WhisperX `whisperx/schema.py`·Buzz `buzz/transcriber/transcriber.py`·Scriberr `interfaces.go`; | `src/transcribers/base.py`, `openai.py`, `whisper_cpp.py`, `youtube.py`, `src/cli.py` | segment/word·오류·시간 출처를 보존; L | 구조 참고 후 Python 계약 구현; BSD-2-Clause/MIT; 문자열 소비자·bot·출력기의 동시 이행, 시간 단위 혼합 위험 [23][29][33]. |
| P0 부분 성공·완료 표식 | Vibe `desktop/src-tauri/src/cmd/transcribe.rs`; | `src/transcribers/openai.py`, `src/utils/worker_pool.py`, `src/cli.py`, `src/database.py` | 실패 청크를 숨기지 않고 partial/failed 판정; M | Rust 코드는 구조 참고(MIT); 정상 종료와 사용자 취소 정책 혼동, 이전 DB 완료 플래그 호환 위험 [31]. |
| P0 구조화 결과 기반 writer | WhisperX `whisperx/utils.py`; | `src/utils/srt_converter.py`, `src/utils/file.py`, `src/cli.py` | TXT/JSON/SRT/VTT가 같은 결과를 소비; M | Python writer 일부 직접 반입 검토(BSD-2-Clause), 기존 고지 보존; 화자 표기·빈 word 시간·자막 cue 정책 회귀 위험 [25]. |
| P1 검증 후 모델 파일 반영 | Vibe `cmd/download.rs`, Buzz `buzz/model_loader.py`, Handy `model/download/tests.rs`; | `src/transcribers/whisper_cpp.py`, `src/config.py`, 신규 `src/utils/model_artifacts.py` | `.part`·크기·해시·취소·교체 복구를 준비 단계로 분리; M | Buzz의 작은 Python helper 직접 반입 검토(MIT); Rust 구현·시험은 구조 참고; 외부 catalog 무결성 정보가 없으면 보증 약화 [30][28][38]. |
| P1 작업 재투입·청크 checkpoint | Scriberr `internal/queue/queue.go`, Subgen `subgen.py`; | `src/utils/job_queue.py`, `src/database.py`, `src/utils/worker_pool.py`, `src/cli.py` | 재시작 attempt·실패 청크 재실행·중복 요청 억제; L | 구조 참고(MIT); 실제 checkpoint는 새 구현 필요; DB 이행·파일 원자성·동시 재투입·큐 포화 위험 [35][36]. |
| P1 capability·옵션 snapshot | Scriberr `interfaces.go`, Buzz `transcriber.py`, Whisper-WebUI `data_classes.py`; | `src/cli.py:get_transcriber()`, `src/config.py`, `src/transcribers/base.py`, `src/utils/job_queue.py` | 엔진별 지원 기능 검사·작업별 설정 고정; M | 구조 참고, 단순 데이터 정의 직접 반입도 검토 가능(MIT/Apache-2.0); Gradio·Qt 의존성 유입과 default 값의 무비판적 복사 위험 [33][29][39]. |
| P1 단계별 캐시 fingerprint | Subgen `generate_audio_hash()`·중복 큐, Buzz task 옵션 snapshot; | `src/database.py`, `src/cli.py`, `src/utils/summary.py`, `translator.py`, `subtitle_corrector.py` | 오디오·엔진 revision·전처리/후처리 설정별 재계산; L | 구조 참고(MIT); 완성 캐시 구현을 복사하는 항목이 아님; 비밀값을 fingerprint 입력/로그에 넣거나 실패 결과를 캐시하는 위험 [36][29]. |
| P2 로컬 모델 runtime 수명주기 | Speaches `base_model_manager.py`와 `executors/whisper.py`; | 신규 `src/transcribers/model_runtime.py`, `src/transcribers/whisper_cpp.py`, `src/utils/job_queue.py` | 장기 실행에서 모델 재사용·동시 사용 상한·idle 해제; M | Python 수명주기 일부 직접 반입 검토(MIT); subprocess 기반 엔진에 context manager를 그대로 붙이는 것과 API 요청 병렬성까지 같은 lock으로 묶는 위험 [26][27]. |

[추론] 권장 의존 순서는 결과 계약·부분 성공 판정, writer와 caller 이행, 작업/청크 저장, fingerprint, 준비 상태·runtime 관리자다. 독립적인 모델 파일 무결성 helper는 병행할 수 있다. 시간 출처가 불명확한 문자열을 JSON에 포장하는 것만으로 단어 타임스탬프가 생기지는 않는다[1][40][23][31].

### 직접 반입과 구조 참고의 경계

open-scribe의 현재 루트 LICENSE는 MIT다[6]. WhisperX는 BSD-2-Clause, 비교표의 MIT 후보들은 저작권·허가 고지를 보존하는 조건을 가진다[7][8][9][10][11][12][13][14][16]. Whisper-WebUI의 Apache-2.0 원문에는 재배포 조건이 있으므로 파일 반입 시 해당 파일의 상위 출처·NOTICE와 수정 고지까지 확인해야 한다[15]. 이는 반입 후보 분류이며 모든 종속 패키지·모델 파일의 재배포 조건을 확인했다는 뜻은 아니다.

[추론] noScribe·VoiceInk·TranscriptionSuite와 제외된 Whishper는 이번 MIT 코드 반입 목록에서 복제 대상과 분리하고 인터페이스 아이디어만 기록한다. Anarlog는 README와 `LICENSE.enterprise`가 community/enterprise의 조건을 구별한다. 파일별 경계를 확인하기 전 전체 repo를 MIT로 간주해 복사할 수 있다는 결론은 내리지 않았다[17][18][20][21][22].

transcribe-anything의 `ytldp_download.py`는 출력 디렉터리 파일을 지운 뒤 URL을 셸 문자열에 삽입하고 `shell=True`, `--no-check-certificate`로 실행한다[37]. [추론] backend별 환경 격리라는 아이디어는 참고하되 이 다운로드 helper는 직접 반입하지 않는 것이 적절하다. 현재 open-scribe의 다운로드 경로와 비교해야 하며, 후보가 MIT라는 사실만으로 구현을 신뢰할 수는 없다[37][4].

### 후속 구현에서 확인할 경로

다음은 수행한 테스트 결과가 아니라 [추론]에 따른 인수 기준 제안이다. 이번 문헌 조사에서는 제품 코드·모델·상위 프로젝트의 시험을 실행하지 않았다.

1. 청크 하나를 의도적으로 실패시키면 `completed`가 아닌 partial/failed와 누락 구간이 저장되고, 재실행 시 성공 청크를 재사용하는지 확인한다[40][5][35].

2. 동일 파일명의 다른 입력·요약 프롬프트 변경·엔진 revision 변경이 해당 단계만 무효화하는지 확인한다[2][3][36].

3. 단어 시간·청크 시작 시간·시간 없음 결과가 서로 다른 provenance로 저장되고 모든 writer에서 의미가 유지되는지 확인한다[40][23][25][29][31].

4. Range를 무시하는 200·잘못된 206·416·중간 EOF·해시 불일치·취소 상황에서 미검증 파일이 최종 모델 경로에 노출되지 않는지 확인한다. Handy의 로컬 가짜 HTTP 서버 시험은 모델 다운로드 없이 이 실패를 만드는 참고 예다[38].

5. 재시작 직전 queued/running 상태, 큐 포화, 취소된 자식 프로세스의 종료가 DB·파일 상태와 일치하는지 확인한다. enum 존재만 확인하는 시험으로 대체하지 않는다[35][31].

## 남은 질문

- [불명: 미발견] 비교한 CLI/큐 경로에서 미디어 content hash부터 후처리 프롬프트 revision까지 연결된 완성 캐시와 실패 청크 영속 재개를 찾지 못했다. 신규 설계의 상태 전이·DB migration·checkpoint 파일 형식은 후속 구현 과제다[24][35][36][3].

- [불명: 미검색] 예비 후보 4개의 모든 adapter·저장·export 구현은 깊게 추적하지 않았다. 16개 전수 선별, 비교 10개, 두 축의 심층 사례 5개라는 계획 수량은 채웠으며 예비 후보의 미검색 항목은 추가 완료 항목으로 계산하지 않았다.

- [불명: 미검색] 실제 M3 Max에서의 메모리·시간·취소 반응과 한국어/영어 처리 품질은 측정하지 않았다. 소스의 속도 광고·README 수치를 장비 성능으로 환산하지 않았다.

- [불명: 미검색] 직접 코드 반입할 개별 파일의 전체 이력·기여자별 권리·종속 라이선스·모델 재배포 약관은 조사하지 않았다. 여기서 직접 반입은 후보의 형태를 뜻하며 법적 검토 완료나 반입 실행을 뜻하지 않는다.
- 실행 경계의 예외를 기록한다. 허용된 얕은 clone에 Buzz `testdata/ggml-tiny.bin` 575,451바이트, WhisperX `whisperx/assets/pytorch_model.bin` 17,719,103바이트, Handy `src-tauri/resources/models/silero-vad-v6.2-F32.gguf` 1,241,056바이트가 동반 전송됐다. 최종 전수 점검은 3건 합계 19,535,610바이트다. 초기 담당자 집계가 GGUF 1건을 놓쳐 메인이 확장자 범위를 넓혀 재점검·정정했다. 필요한 소스·commit·LICENSE를 보존한 뒤 해당 세 clone 캐시를 11-05에 삭제했다. 별도 모델 다운로드 명령·추론은 0건이나 모델 전송 0건으로 보고하지 않는다. 원래 담당자 기록은 `bundled-fixtures.json`·`cache-cleanup.json`, 이를 정정한 메인 기록은 `/tmp/open-scribe-research-2026-11/cache-cleanup-final.json`이다.

검증 기록(2026-11-05): 번호 출처 40항목(외부 33·로컬 7), 후보 16개, 비교 10개, 심층 축 2개·사례 5개, 반입 후보 8개다. `cite_check.js` 구조 오류 0건, 전체 189쌍을 `citation-audit.jsonl`의 0부터 시작하는 pair_index로 대조했다. 발견한 README 경로·시간 단위·시험 범위·인용 연결 문제는 본문을 수정했다. `source-notes.md`, `citation-audit.jsonl`, `audit-summary.json`, `validation.json`은 자기 임시공간에 보존했다.

## 출처

원문은 주로 2026-11-04 KST에 확보했고, 재대조·인용 감사는 2026-11-05 KST에도 수행했다. 22의 루트 README 응답은 11-04에 읽었으며 고정 `docs/README.md`와 17의 추가 LICENSE.txt는 11-05에 확인했다. 7~22는 저장소의 고정 commit을 기준으로 README·라이선스·명시한 코드/시험을 읽은 원문 묶음이다. README 설명과 코드가 다르면 코드 범위로 주장을 좁혔다. commit 날짜는 source-notes의 GitHub commits API 원문과, clone한 10개는 clone HEAD도 대조했다. 검색 결과·크롤링 시점은 활동성 근거로 사용하지 않았다.

[1] ysys143/open-scribe — src/transcribers/base.py (3880fcf, 2026-08-27). https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/transcribers/base.py
[2] ysys143/open-scribe — src/cli.py (3880fcf, 2026-08-27). https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/cli.py
[3] ysys143/open-scribe — src/database.py (3880fcf, 2026-08-27). https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/database.py
[4] ysys143/open-scribe — src/downloader.py (3880fcf, 2026-08-27). https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/downloader.py
[5] ysys143/open-scribe — src/utils/worker_pool.py (3880fcf, 2026-08-27). https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/utils/worker_pool.py
[6] ysys143/open-scribe — LICENSE (3880fcf, 2026-08-27). https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/LICENSE
[7] m-bain/whisperX — README.md (5d3678b, 2026-10-22). https://github.com/m-bain/whisperX/blob/5d3678b8535698a2826a5db9eb3e4105aef85dd9/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/m-bain/whisperX/commit/5d3678b8535698a2826a5db9eb3e4105aef85dd9
[8] speaches-ai/speaches — README.md (993994f, 2026-04-18). https://github.com/speaches-ai/speaches/blob/993994f7984bf3fe9655b267448328cf66fccb42/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/speaches-ai/speaches/commit/993994f7984bf3fe9655b267448328cf66fccb42
[9] chidiwilliams/buzz — README.md (de7484b, 2026-11-04). https://github.com/chidiwilliams/buzz/blob/de7484bea317ebb17dcb27da3a6e4109f9bb33e7/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/chidiwilliams/buzz/commit/de7484bea317ebb17dcb27da3a6e4109f9bb33e7
[10] thewh1teagle/vibe — README.md (da8c2ca, 2026-10-30). https://github.com/thewh1teagle/vibe/blob/da8c2ca53b6c7ff44f7a1314c3be862d466c3427/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/thewh1teagle/vibe/commit/da8c2ca53b6c7ff44f7a1314c3be862d466c3427
[11] rishikanthc/Scriberr — README.md (a353078, 2026-09-20). https://github.com/rishikanthc/Scriberr/blob/a353078fd96b8aca4002681813524b7397c90df1/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/rishikanthc/Scriberr/commit/a353078fd96b8aca4002681813524b7397c90df1
[12] McCloudS/subgen — README.md (5f98ed6, 2026-08-06). https://github.com/McCloudS/subgen/blob/5f98ed611dcb46844e8d671bd5c17e1d092261f5/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/McCloudS/subgen/commit/5f98ed611dcb46844e8d671bd5c17e1d092261f5
[13] zackees/transcribe-anything — README.md (3b7a860, 2026-10-26). https://github.com/zackees/transcribe-anything/blob/3b7a860ac4a7f1e31c4d5d19ef4c678dafa396e3/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/zackees/transcribe-anything/commit/3b7a860ac4a7f1e31c4d5d19ef4c678dafa396e3
[14] Zackriya-Solutions/meetily — README.md (07c4dfd, 2026-11-02). https://github.com/Zackriya-Solutions/meetily/blob/07c4dfd45361bb6776916a0d46f493dda447f471/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/Zackriya-Solutions/meetily/commit/07c4dfd45361bb6776916a0d46f493dda447f471
[15] jhj0517/Whisper-WebUI — README.md (c3bb3b1, 2025-12-29). https://github.com/jhj0517/Whisper-WebUI/blob/c3bb3b18e959826b28b1192486a8d5b361b6a4e0/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/jhj0517/Whisper-WebUI/commit/c3bb3b18e959826b28b1192486a8d5b361b6a4e0
[16] cjpais/Handy — README.md (82dfab9, 2026-11-02). https://github.com/cjpais/Handy/blob/82dfab9fda18c4bc24e1f6e56d36474d38eca0bc/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/cjpais/Handy/commit/82dfab9fda18c4bc24e1f6e56d36474d38eca0bc
[17] kaixxx/noScribe — README.md (acccc92, 2026-10-29). https://github.com/kaixxx/noScribe/blob/acccc9203c674e0bffb42fa4da6d8af5c90cce1e/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/kaixxx/noScribe/commit/acccc9203c674e0bffb42fa4da6d8af5c90cce1e
[18] pluja/whishper — README.md (adcd186, 2025-08-15). https://github.com/pluja/whishper/blob/adcd186a2c72f5826235a36a500a2cbbc4acfdd2/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/pluja/whishper/commit/adcd186a2c72f5826235a36a500a2cbbc4acfdd2
[19] Vaibhavs10/insanely-fast-whisper — README.md (0fed9a4, 2024-05-27). https://github.com/Vaibhavs10/insanely-fast-whisper/blob/0fed9a41fe8a929698ee35aa2030793e649f21bc/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/Vaibhavs10/insanely-fast-whisper/commit/0fed9a41fe8a929698ee35aa2030793e649f21bc
[20] fastrepl/hyprnote — README.md (428903e, 2026-11-01). https://github.com/fastrepl/anarlog/blob/428903e3c73d840f4a5e3501fce0037fd050abfd/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/fastrepl/hyprnote/commit/428903e3c73d840f4a5e3501fce0037fd050abfd
[21] Beingpax/VoiceInk — README.md (5c95ff9, 2026-11-04). https://github.com/Beingpax/VoiceInk/blob/5c95ff971687f71655a26b0c531833ac4414011b/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/Beingpax/VoiceInk/commit/5c95ff971687f71655a26b0c531833ac4414011b
[22] homelab-00/TranscriptionSuite — docs/README.md (541bde9, 2026-09-24). https://github.com/homelab-00/TranscriptionSuite/blob/541bde94cbd38b51ca79d01faddec0ba9764809c/docs/README.md；원문 묶음: 고정 snapshot README·라이선스·본문 지정 코드/시험. commit 확인: https://github.com/homelab-00/TranscriptionSuite/commit/541bde94cbd38b51ca79d01faddec0ba9764809c
[23] m-bain/whisperX — whisperx/schema.py (5d3678b, 2026-10-22). https://github.com/m-bain/whisperX/blob/5d3678b8535698a2826a5db9eb3e4105aef85dd9/whisperx/schema.py
[24] m-bain/whisperX — whisperx/transcribe.py (5d3678b, 2026-10-22). https://github.com/m-bain/whisperX/blob/5d3678b8535698a2826a5db9eb3e4105aef85dd9/whisperx/transcribe.py
[25] m-bain/whisperX — whisperx/utils.py (5d3678b, 2026-10-22). https://github.com/m-bain/whisperX/blob/5d3678b8535698a2826a5db9eb3e4105aef85dd9/whisperx/utils.py
[26] speaches-ai/speaches — src/speaches/executors/shared/base_model_manager.py (993994f, 2026-04-18). https://github.com/speaches-ai/speaches/blob/993994f7984bf3fe9655b267448328cf66fccb42/src/speaches/executors/shared/base_model_manager.py
[27] speaches-ai/speaches — src/speaches/executors/whisper.py (993994f, 2026-04-18). https://github.com/speaches-ai/speaches/blob/993994f7984bf3fe9655b267448328cf66fccb42/src/speaches/executors/whisper.py
[28] chidiwilliams/buzz — buzz/model_loader.py (de7484b, 2026-11-04). https://github.com/chidiwilliams/buzz/blob/de7484bea317ebb17dcb27da3a6e4109f9bb33e7/buzz/model_loader.py
[29] chidiwilliams/buzz — buzz/transcriber/transcriber.py (de7484b, 2026-11-04). https://github.com/chidiwilliams/buzz/blob/de7484bea317ebb17dcb27da3a6e4109f9bb33e7/buzz/transcriber/transcriber.py
[30] thewh1teagle/vibe — desktop/src-tauri/src/cmd/download.rs (da8c2ca, 2026-10-30). https://github.com/thewh1teagle/vibe/blob/da8c2ca53b6c7ff44f7a1314c3be862d466c3427/desktop/src-tauri/src/cmd/download.rs
[31] thewh1teagle/vibe — desktop/src-tauri/src/cmd/transcribe.rs (da8c2ca, 2026-10-30). https://github.com/thewh1teagle/vibe/blob/da8c2ca53b6c7ff44f7a1314c3be862d466c3427/desktop/src-tauri/src/cmd/transcribe.rs
[32] thewh1teagle/vibe — desktop/src/pages/main/hooks/use-transcribe-queue.ts (da8c2ca, 2026-10-30). https://github.com/thewh1teagle/vibe/blob/da8c2ca53b6c7ff44f7a1314c3be862d466c3427/desktop/src/pages/main/hooks/use-transcribe-queue.ts
[33] rishikanthc/Scriberr — internal/transcription/interfaces/interfaces.go (a353078, 2026-09-20). https://github.com/rishikanthc/Scriberr/blob/a353078fd96b8aca4002681813524b7397c90df1/internal/transcription/interfaces/interfaces.go
[34] rishikanthc/Scriberr — internal/transcription/pipeline/pipeline.go (a353078, 2026-09-20). https://github.com/rishikanthc/Scriberr/blob/a353078fd96b8aca4002681813524b7397c90df1/internal/transcription/pipeline/pipeline.go
[35] rishikanthc/Scriberr — internal/queue/queue.go (a353078, 2026-09-20). https://github.com/rishikanthc/Scriberr/blob/a353078fd96b8aca4002681813524b7397c90df1/internal/queue/queue.go
[36] McCloudS/subgen — subgen.py (5f98ed6, 2026-08-06). https://github.com/McCloudS/subgen/blob/5f98ed611dcb46844e8d671bd5c17e1d092261f5/subgen.py
[37] zackees/transcribe-anything — src/transcribe_anything/ytldp_download.py (3b7a860, 2026-10-26). https://github.com/zackees/transcribe-anything/blob/3b7a860ac4a7f1e31c4d5d19ef4c678dafa396e3/src/transcribe_anything/ytldp_download.py
[38] cjpais/Handy — src-tauri/src/managers/model/download/tests.rs (82dfab9, 2026-11-02). https://github.com/cjpais/Handy/blob/82dfab9fda18c4bc24e1f6e56d36474d38eca0bc/src-tauri/src/managers/model/download/tests.rs
[39] jhj0517/Whisper-WebUI — modules/whisper/data_classes.py (c3bb3b1, 2025-12-29). https://github.com/jhj0517/Whisper-WebUI/blob/c3bb3b18e959826b28b1192486a8d5b361b6a4e0/modules/whisper/data_classes.py
[40] ysys143/open-scribe — src/transcribers/openai.py (3880fcf, 2026-08-27). https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/transcribers/openai.py
