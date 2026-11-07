# open-scribe 2026년 11월 조사 브리프

기준일: 2026-11-04 (Asia/Seoul). 목적: 한국어·영어 기술 강연 및 대담의 전사, 화자 식별, 요약을 개선할 근거를 수집한다. 네 주제를 병렬로 문헌 조사한다. 설치·모델 다운로드·유료 API 호출·제품 코드 변경·커밋·push는 수행하지 않는다.

11-05 보완: 사용자 링크의 HF ASR 트렌딩 첫 페이지 30카드를 전수 선별하고 OpenRouter Nemotron 3.5 Transcribe 호스팅을 추가 검토한다. 사용자가 30B급 로컬 실행을 제외했으므로 **30B급은 로컬 추천에서 제외**하며 Nemotron 30B는 호스팅 후보로만 채택 검토한다. active parameter 수가 작다는 이유로 전체 30B급 MoE를 소형으로 분류하지 않는다. 공개 구현·양자화·MLX 지원 기록은 채택 추천과 구별해 남긴다.

## 고정 질문과 역할

- T1: 유사 오픈소스의 어떤 구조를 open-scribe에 반입할 수 있는가?
- T2: 화자를 나누고 목소리를 저장하여 이후 녹음에서 재식별하려면 어떤 구조가 필요한가?
- T3: 2026-11-04에 확인 가능한 호스팅 모델 가운데 요약·교정·번역·전사에 적합한 선택은 무엇인가?
- T4: 한국어·영어 전사용 공개 ASR의 양자화 및 Apple Silicon/MLX 실행 경로는 무엇인가?
- 메인: 코드 기준선 확인, 결과의 근거·개수·충돌 검증, 우선순위 종합.

## 코드 기준선

저장소: /Users/jaesolshin/Documents/GitHub/open-scribe. HEAD 3880fcf (2026-08-27). 코드를 문서보다 우선한다. docs/architecture.md에는 실제 코드와 다른 예시가 있다.

- src/config.py: 기본 엔진 gpt-4o-mini-transcribe. gpt-4o-transcribe, whisper-api, whisper-cpp, youtube-transcript-api 지원. high는 gpt-4o-transcribe 별칭.
- src/transcribers/base.py: transcribe() -> Optional[str]. 세그먼트·단어·화자용 공통 구조가 없다. chunk 실패 시 문자열을 생략하여 부분 결과를 반환할 수 있다.
- src/transcribers/openai.py: whisper-1 verbose_json 세그먼트는 문자열로 포맷. GPT-4o 계열 타임스탬프는 chunk 시작 시간이다. 단어 시간과 구별해야 한다.
- src/cli.py: 엔진 생성·다운로드·전사·후처리를 조정한다. src/database.py SQLite transcription_jobs는 (video_id, engine) UNIQUE이며 단계별 완료 플래그와 파일 경로를 저장한다.
- src/utils/summary.py, translator.py, subtitle_corrector.py: Config 기본 요약·번역·교정 모델 gpt-5-mini. summary는 OpenAI Chat Completions 고정, gpt-5 접두어 분기만 있고 추론 강도는 지정하지 않는다. 다른 모델 분기에 max_tokens=1000, temperature=0.3. 2,000,000자 자르기는 토큰 한도 검증이 아니다.
- src/utils/keywords.py: gpt-4o-mini 고정, 최대 3,000자 입력. Notion 태그 추출에 사용.
- .env.example은 요약·번역·교정 모델 예시 gpt-4o-mini로 코드 기본값과 차이.
- Config: XDG config .env 우선, 개발용 .env 보충. 비밀 파일 값은 열지 않는다.
- docs/roadmap.md 2.1: 화자 분리 미착수. bot/ Telegram, deploy.sh Cloud Run memory=1Gi.
- 이전 턴에서 로컬 whisper-cpp 모델 경로가 없음을 확인함. 실행 경로 복구와 모델 성능 비교는 별개다.

## 장비와 사용량

이번 실행에서 확인: Apple M3 Max, 36GiB 메모리, 디스크 여유 약 60GiB. SQLite를 읽기 전용으로 재조회: 73건(2025-12~2026-11), mini ASR 65건·상위 ASR 8건, 최근 월 약 20건. DB에 기록된 중복 없는 경로 중 실제 존재하는 전사문 64개의 Python len(text) 기준 최소 1,564자, 중앙값 16,679자, p90(nearest-rank) 96,884자, 최대 212,142자. 이전 턴의 중앙값·p90은 표본 집계법이 불명확하여 이번 재집계로 교체한다. 원문은 보고서에 복제하지 않는다. 집계는 /tmp/open-scribe-research-2026-11/baseline.json. 신규 모델 실험 결과가 아니다. 오디오 길이는 아직 확인되지 않았으므로 비용은 명시적 길이 시나리오를 사용한다.

## 근거·검증 규칙

- jstack:research 자립 경로. /Users/jaesolshin/.codex-3/plugins/cache/jstack/jstack/0.0.1/payload/skills/research/
- 주제당 출처 20~40개, 약 60분 기준. 1차 출처만 증거로 채택. 검색은 내장 웹, 본문은 Jina Reader 우선. 실패하면 내장 웹 조회 사용. 로그인·클릭 자동화가 필요하면 ego-browser 스킬.
- 실제 접근한 문서의 날짜·버전·API ID를 기록하며 확인되지 않은 것은 [불명]. 사용자 제시 이름은 존재 여부부터 검증.
- 주장별 번호 인용 [n], 추론은 [추론], 근거 없는 항목은 [불명]과 미검색/검색했지만 미발견 구분. 서로 다른 벤치마크 점수를 직접 순위화하지 않는다.
- 필수 제목: ## 요약, ## open-scribe 적용 검토, ## 남은 질문, ## 출처. 한국어 문단 800자 이하.
- cite_check.js REPORT --pairs /tmp/.../pairs.jsonl. 기계 검사는 구조만 검사하며 모든 문장/출처 쌍을 실제 본문과 대조한다.
- 각 에이전트는 자기 보고서와 자기 /tmp 디렉토리만 쓴다. 소스 코드 변경·설치·추가 에이전트 생성 금지. /tmp의 git clone --depth 1은 문헌 조사로 허용.

## 산출물

deliverables/01-similar-projects.md, 02-speaker-diarization.md, 03-hosted-models.md, 04-open-asr-mlx.md. 메인은 00-synthesis.md를 작성한다. 검증 기록도 deliverables/에 둔다. 기존 git 변경은 보존한다.
