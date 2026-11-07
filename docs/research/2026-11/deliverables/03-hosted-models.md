# T3 — 호스팅 모델의 요약·교정·번역·전사 적용 검토

조사 기준일: 2026-11-04 KST. 대부분의 원문은 11-04에 조회했다. 자정 이후 조회한 Speechmatics 요금표 [32], OpenAI 종료 일정 [42], Nemotron 호스팅·카드·API·PAYG 자료 [43][44][45][46]는 11-05 보완 자료다. 새 가격의 11-04 적용 여부를 소급하지 않는다. 문서의 출시일·지식 기준일·조회일은 서로 구별한다. 갱신일 없는 문서는 아래의 조회 시점에 읽힌 내용만 입증한다.

조사 질문: 2026-11-04에 확인 가능한 호스팅 모델 가운데 open-scribe의 한국어·영어 기술 강연 요약·교정·번역·전사에 적합한 후보와 도입 조건은 무엇인가?

하위질문은 ① 제시된 이름의 실제 API ID와 추론 설정, ② 공급자별 가격·문맥·출력·구조화 기능, ③ 한국어 품질 근거와 지연, ④ 전사 가격·파일 한도·단어 시간, ⑤ 현재 코드의 변경 범위와 월 20건 비용이다. 심층 축은 **장문 후처리의 호출·출력 제약**과 **한국어 전사의 근거·시간 정보·비용** 두 개이며, 아래 사례와 계산은 이 두 축에 포함한다.

범위는 문헌 조사와 로컬 코드 읽기다. 모델 추론 API·모델 목록 API·키 조회·설치·가중치 다운로드·제품 코드 수정·커밋을 수행하지 않았다. `[불명·미발견]`은 읽은 문서와 검색 범위에서 근거를 찾지 못했다는 뜻이고, 부재의 증명이 아니다. `[불명·미검색]`은 조사하지 않은 항목이다. `[추론]`은 문헌과 코드에서 도출한 판단이다.

Nemotron 30B급 모델은 이 보고서에서 **원격 호스팅 전용 후보**이며, 로컬 30B급 모델은 추천 대상에서 제외한다.

## 요약


- [추론] 요약의 우선 비교군은 `gpt-6-luna`, `claude-haiku-5-5`, `deepseek-flash`다. 모두 약 1M 문맥을 명시하고, 짧은 입력 구간에서 낮은 단가를 제공한다 [1][5][10]. 한국어 강연 요약의 동일 조건 품질 순위는 [불명·미발견]이다.

- 제시된 DeepSeek 버전과 Haiku·Luna 계열은 공식 문서에서 확인했다 [1][5][10]. 그러나 `deepseek-flash-v4.1-1017`은 확인된 호출 ID가 아니며, `max`는 별도 추론 매개변수다 [1][6][10][11]. 실행 환경의 모델 목록은 API ID·가격의 근거로 사용하지 않았다.

- [추론] 최대 212,142자 전사문은 1M 문맥만으로 처리 가능성을 판정할 수 없다. 입력 토큰 수, 교정용 두 원문, 출력·추론 토큰, 장문 할증을 함께 계산해야 한다. 특히 번역·교정은 출력 한도가 병목이 된다 [1][5][8][10][13].

- OpenAI 파일 전사 문서는 `gpt-transcribe`를 권장하며, 기존 `whisper-1`·GPT-4o 전사 모델들의 종료일을 2027-02-26으로 명시한다 [4]. 새 모델의 단어 시간 지원은 읽은 범위에서 [불명·미발견]이며, 기존 단어 시간 예시는 `whisper-1`에 한정된다 [4].

- [추론] 전사는 OpenAI의 새 경로, ElevenLabs, Google, RTZR과 **Nemotron 3.5 Transcribe 호스팅 경로**를 우선 비교한다 [4][23][29][35][43][44]. Nemotron의 사용량 단가는 $0.1188/시간이며, NVIDIA 카드에는 한국어 FLEURS CER 2.78%가 있다 [43][44]. 단어 시간이 필요하면 Voxtral 3의 `word` 요청 400 제약과 Nemotron 호스팅의 미확정 응답 계약을 구별해야 한다 [31][45]. 한국어 품질 수치는 시험·시점·지표가 달라 하나의 순위로 합치지 않았다.

## 조사 범위와 원문 시점

LLM 공급자 11곳(OpenAI, Anthropic, Google, DeepSeek, Qwen/Alibaba, Moonshot/Kimi, Zhipu/Z.ai, MiniMax, Mistral, xAI, OpenRouter), 지정된 전사 공급자 9곳(OpenAI, ElevenLabs, Deepgram, AssemblyAI, Google, Mistral, Speechmatics, RTZR, CLOVA), NVIDIA/OpenRouter/DeepInfra 호스팅 경로를 확인했다. 아래 텍스트 모델 10종, 전사 모델·서비스 12종, 별도 기준선 4종과 OpenRouter 텍스트 경로 1개를 구별한다.

출처 목록은 외부 1차 문서 46개로 목표 20~40개보다 6개 많다. AssemblyAI 파일 한도 FAQ, 기존 모델의 종료 일정 검증, Nemotron의 호스팅·한국어 근거·API·PAYG 계약을 포함한다. 로컬 근거는 HEAD `3880fcf`의 파일과 집계법을 기록한 [brief.md](../brief.md)이며 외부 출처 수에 넣지 않았다. 원문의 시점은 Haiku 출시 2026-10-07 [5], Gemini Flash-Lite 갱신 2026-07 [8], Qwen 가격표 갱신 2026-11-02 [12], Mistral Small 4 출시 2026-03-16 [20], Grok 4.7 출시 기록 2026-09-21 [21], RTZR 평가 글 발행 2023-08-25 [36]로 구별한다.

### 제시된 세 이름의 검증

| 사용자 표기 | 확인한 공식 호출 ID | 문맥 / 최대 출력 | `max`의 정확한 위치와 의미 |
|---|---|---|---|
| `deepseek-flash-v4.1-1017` | `deepseek-flash`; 문서의 모델 버전은 `DeepSeek-V4.1-Flash-1017`; 사용자 문자열을 호출 ID로 인정하는 근거는 [불명·미발견] | 1M / 384K | Chat: `reasoning_effort="max"`; 생각 활성화는 `extra_body.thinking.type="enabled"`; 기본 강도는 `high`; `medium`·`xhigh`는 실제 `high`로 매핑된다 [10][11]. |
| `claude-haiku-5.5 max` | `claude-haiku-5-5` | 1M / 표준 128K; Batch 베타는 300K | Messages: `output_config.effort="max"`; `low/medium/high/xhigh/max`, 기본 `medium`; 모델 ID·구독 Max·`max_tokens`와 다르다 [5][6]. |
| `gpt-6-luna max` | `gpt-6-luna` | 총 1,050,000, 최대 입력 922,000 / 출력 128,000 | Responses: `reasoning.effort="max"`; Chat: `reasoning_effort="max"`; `none/low/medium/high/xhigh/max`, 기본 `medium` [1][2]. |

[추론] 세 공급자의 `max`를 동등한 품질·지연·비용 수준으로 취급할 수 없다. DeepSeek에는 별도 매핑 규칙이 있고, Anthropic의 effort는 응답·도구·사고 토큰 전반에 영향을 준다. OpenAI의 모델별 지원 수준도 별도다. `max`에 대한 고정 추가 요금표는 [불명·미발견]이며, 추가 출력·사고 토큰은 총비용과 지연을 바꿀 수 있다 [1][6][11].

### 텍스트 후보의 가격과 장문 제약

아래 금액은 USD/100만 토큰이다. 입력·출력은 표준 호출 기준이며 캐시 읽기·쓰기는 별도 열이다. 실제 계정 접근성·청구 검증은 [불명·미검색]이다. 일반 JSON 출력과 스키마를 강제하는 structured output은 구별한다.

| 공급자 / 후보 | 입력 / 출력 | 캐시 읽기 / 쓰기 | 문맥 / 최대 출력 | 입력 → 출력·구조화 |
|---|---|---|---|---|
| OpenAI `gpt-6-luna` | 0.10 / 0.50; 입력 >272K이면 전체 요청 입력·캐시 2배, 출력 1.5배 | 0.01 / 0.125(짧은 TTL 기본표); 장문 할증 적용 | 총 1.05M / 128K, 최대 입력 922K | 텍스트·이미지 → 텍스트; structured outputs 지원 [1][3]. |
| Anthropic `claude-haiku-5-5` | 입력 ≤100K: 0.10 / 0.50; >100K: 0.50 / 2.50 | 읽기 0.01 / 0.05; 5분 쓰기 0.125 / 0.625; 1시간 쓰기 0.20 / 1.00 | 1M / 128K | 텍스트·이미지 → 텍스트; 표준 SDK의 스키마 지정은 추가 확인 필요 [5]. |
| Google `gemini-3.5-flash-lite` | 0.30 / 2.50; 출력에 thinking 포함 | 읽기 0.03; 저장 1.00/100만 토큰·시간 | 입력 1,048,576 / 출력 65,536 | 텍스트·이미지·영상·음성·PDF → 텍스트; structured outputs 지원 [8][9]. |
| DeepSeek `deepseek-flash` | 비혼잡 0.15 / 0.60; 혼잡 0.30 / 1.20 | 읽기 0.003 / 0.006; 별도 쓰기 단가는 [불명·미발견] | 1M / 384K | 텍스트·이미지 → 텍스트; JSON output 명시, strict schema 보장은 이 표의 근거에서 [불명·미발견] [10]. |
| Qwen `qwen3.7-plus-2026-05-26` | 싱가포르 International 고정 버전: 입력 ≤256K 0.40 / 1.60; >256K 1.20 / 4.80 | 캐시 지원; 해당 버전의 정확한 캐시 요율은 [불명·미발견] | 1M / 128K | 텍스트·이미지·영상 → 텍스트; structured output 지원; alias의 한시 할인과 고정 버전의 정가를 섞지 않았다 [12][13]. |
| Moonshot `kimi-k3.1-pro` | 2.00 / 10.00 | 읽기 0.20; 5분/1시간 쓰기 2.00/4.00 | 총 1,048,576; 출력 기본 131,072, 설정 상한 1,048,576이나 총 문맥 안에서 사용 | 텍스트·시각 입력 → 텍스트; `json_schema`와 `strict:true` 지원; 사고 항상 활성화, 기본 effort `max` [14][15]. |
| Zhipu `glm-5.3-flash` | 0.15 / 0.50 | 읽기 0.03; 저장은 한시 무료, 종료일 [불명·미발견] | 1M / 128K | 텍스트·영상·이미지·파일 → 텍스트; JSON structured output 명시; strict 보장 범위는 [불명·미발견] [16][17]. |
| MiniMax `MiniMax-M3.1-Flash` | 0.15 / 0.60 | 읽기 0.015; 쓰기 요율 [불명·미발견] | 1,000,000 / 출력 상한 [불명·미발견] | 텍스트·이미지·영상 → 텍스트; 도구 지원, 강제 JSON 스키마는 [불명·미발견]; 기본 effort `max`, 사고 비활성화 불가 [18][19]. |
| Mistral `mistral-small-2603` | 0.15 / 0.60 | 해당 모델 캐시 요율 [불명·미발견] | 256K / 출력 상한 [불명·미발견] | 텍스트 → 텍스트의 hybrid 모델; Chat Completions·structured outputs 지원; 추가 모달리티의 상세 계약은 [불명·미발견] [20]. |
| xAI `grok-4.7` | 입력 <200K: 2.00 / 6.00; 장문 구간 4.00 / 12.00 | 읽기 0.50 / 장문 1.00; 별도 쓰기 요율 [불명·미발견] | 500K / 독립 텍스트 출력 제한 없다고 명시하나 총 문맥 제약 존재 | 텍스트·이미지 → 텍스트; `low/medium/high/xhigh`, 기본 `high`; strict schema 지원 범위는 [불명·미발견] [21]. |

DeepSeek 혼잡 시간은 중국 공휴일을 제외한 월~금 UTC 01~04시·06~10시이며, 나머지는 비혼잡 요금이다. KST로는 평일 10~13시·15~19시에 해당한다. [추론] 비동기 후처리를 비혼잡 구간에 배치하면 표의 단가 차이를 이용할 수 있지만, 재시도·생성 토큰 수가 같다는 전제다 [10].

OpenRouter에서는 `deepseek/deepseek-v4.1-flash` 경로를 확인했다 [22]. 공급자별 가격·캐시·지연과 전체 페이지의 표시 가격이 서로 다르고 라우팅도 달라질 수 있다 [22]. [추론] 이것을 DeepSeek 직판 `deepseek-flash`의 ID·버전·최대 출력·가격 보장으로 옮겨 적으면 안 된다 [10][22]. 이 보고서의 직판 비용 계산에는 OpenRouter의 표시 최저가를 쓰지 않았다.

### 한국어 품질과 지연 근거의 한계

Anthropic은 Haiku 5.5의 Global-MMLU 한국어 점수를 **동일 모델 영어 점수 대비 97.0%**로 제시한다. 이는 한국어 절대 정답률 97%나 번역·교정 정확도 97%가 아니다. 문서는 목표 언어를 명시하라고 안내한다. [추론] 한국어 후보로 남길 근거는 되지만 기술 강연의 숫자·용어·부정문 보존을 입증하지는 못한다 [7].

Luna·DeepSeek·Gemini·Qwen·Kimi·GLM·MiniMax·Mistral·Grok의 이번 후보들을 동일한 한국어 강연 요약·교정·번역 표본에서 비교한 공급자 원문은 [불명·미발견]이다. Haiku의 `Fastest` [5], Gemini Flash-Lite의 저지연 [8], Kimi Highspeed의 상대 속도 설명 [15]은 공급자 내부 설명이며 서로 비교 가능한 한국어 장문 지연 수치는 [불명·미발견]이다. OpenRouter의 지연은 그 플랫폼 관측이며 open-scribe 실측이 아니다 [22].

## open-scribe 적용 검토

### 로컬 기준선과 호출 변경

이번 읽기에서 HEAD `3880fcf`, `requirements.txt`·`requirements.cloud.txt`의 `openai==1.107.0`을 확인했다. 기본 후처리 모델은 [src/config.py](/Users/jaesolshin/Documents/GitHub/open-scribe/src/config.py:44)의 `gpt-5-mini`다. [summary.py](/Users/jaesolshin/Documents/GitHub/open-scribe/src/utils/summary.py:111)는 Chat Completions를 사용하며 `gpt-5` 접두어만 예외 처리한다. 그 밖의 모델에는 `max_tokens=1000`, `temperature=0.3`을 전달한다. 이 1000은 긴 구조적 요약을 자를 수 있는 별도 제약이다.

[subtitle_corrector.py](/Users/jaesolshin/Documents/GitHub/open-scribe/src/utils/subtitle_corrector.py:85)는 `temperature=0.1`, `max_tokens=4000`을 전달한다. [translator.py](/Users/jaesolshin/Documents/GitHub/open-scribe/src/utils/translator.py:260)는 타임스탬프·일반 텍스트 경로 모두 `max_completion_tokens=4000`이다. [추론] 모델별 추론 토큰 소비를 빼고도 전체 전사 번역·교정을 4000 토큰에 담을 수 없는 표본이 생긴다. 실제 유료 호출로 잘림·오류를 재현하지 않았으므로 발생률은 [불명·미검색]이다.

OpenAI 문서는 사고 강도가 `none`이 아니면 `temperature` 등을 제거하도록 명시한다. [추론] 현재 요약 함수에 Luna 이름만 넣으면 기본 `medium`과 `temperature=0.3`이 충돌할 수 있다. 교정 함수도 별도 매개변수 수정 대상이다. `gpt-5` 접두어 예외를 새 이름까지 단순 확장하는 것만으로 SDK·출력 길이·응답 형식의 적합성이 검증되지는 않는다 [1][2].

| 경로 | 문헌상 확인한 호출 특성 | 예상 변경량 — 실행 검증하지 않은 [추론] |
|---|---|---|
| OpenAI Luna | Chat·Responses 지원, Chat의 도구 호출은 effort `none`일 때만 지원 | 작음~중간: 모델별 매개변수 표, `max_completion_tokens`/사고 예산, 종료 이유·usage 기록, 기존 SDK의 새 필드 수용성 확인 [1][2]. |
| Anthropic Haiku | Messages/effort 경로, sampling 매개변수 생략, 텍스트·thinking 블록 | 큼: 별도 클라이언트와 응답 어댑터, 출력 예산, 모델별 토큰 계산; 토크나이저가 Haiku 4.5보다 약 30% 많이 셀 수 있다 [5][6]. |
| Google Gemini | 텍스트 모델과 전사 모델이 서로 다른 기능·설정을 제공 | 중간~큼: 공급자 어댑터, 구조화 응답 파싱, 한국어·타임코드 보존 검증; 현재 SDK의 호환 엔드포인트 사용 가능 범위는 [불명·미발견] [8][29]. |
| DeepSeek | 공식 표가 OpenAI 형식 base URL을 명시; 생각 설정은 `extra_body` 사용 예시 존재 | 중간: base URL·키 이름의 공급자별 분리, effort 매핑, 사고/최종 텍스트 분리, 가격 시간대 기록 [10][11]. |
| Qwen | 문맥·structured output·고정 버전 제공 | 중간: 리전/버전/매개변수 매핑; 현재 OpenAI SDK 그대로 쓰는 경로의 세부 호환성은 [불명·미발견] [12][13]. |
| Kimi | Chat Completions, `reasoning_content`, strict schema; sampling 값 고정 | 중간: 고정 sampling 필드 제거, 긴 출력·사고 예산, 완전한 assistant 메시지 보존, 캐시 쓰기 요금 기록 [14][15]. |
| Z.ai | GLM의 JSON·도구·문맥 캐시 기능 | 중간: 공급자 어댑터와 스키마 검증; 이번 원문만으로 현재 SDK의 무수정 호환성은 [불명·미발견] [16][17]. |
| MiniMax | Anthropic 호환 API, `output_config.effort`, 일부 sampling 필드는 무시됨 | 큼: Messages 응답 처리 또는 별도 호환 경로 조사, 사고로 출력 예산이 소진되는 경우 처리 [19]. |
| Mistral | `/v1/chat/completions`, structured output | 중간: 공급자 어댑터, 256K 문맥 전 분할, 응답·출력 길이 검증 [20]. |
| xAI | Responses의 암호화된 reasoning 반환, 독자 effort·장문 요금 | 중간: endpoint/매개변수·usage 어댑터, 200K 가격 경계 확인; 현재 SDK 버전의 동작은 [불명·미검색] [21]. |
| OpenRouter | 동일 경로에 여러 제공자와 라우팅·캐시·성능 조건 | 중간: 제공자·모델 버전 고정 여부, 지원 매개변수, 경로별 실패·청구 기록; 새로운 모델 품질 후보로 중복 계산하지 않는다 [22]. |

[추론] 공통 결과에는 최종 텍스트, 모델 ID·버전·공급자, 입력/캐시/출력/사고 usage, 완료·잘림·실패 상태가 필요하다. 교정·번역에는 세그먼트 ID와 원문/수정문을 담고, 허용 변경 범위와 누락 여부를 검증하는 구조가 적합하다. structured output은 형식 오류를 줄이는 수단이며 원문의 사실 보존 증거가 아니다. 문헌상의 기능과 실제 SDK `1.107.0` 호환성은 분리해 검증해야 한다 [1][8][13][15][17][20].

### 21만 자 입력과 출력 예산

중복 없는 DB transcript_path 중 존재하는 64파일을 Python `len(text)`로 집계한 표본은 중앙값 16,679자, p90(nearest-rank) 96,884자, 최대 212,142자다. 이는 이번 모델들의 성능 측정이 아니라 기존 파일 크기 표본이다. 집계법과 기준선은 [brief.md](../brief.md)에 기록돼 있다.

다음 토큰 수는 **계획용 가정**이다. 한국어·영어 혼합, 타임코드, 코드·식별자, 공급자별 토크나이저 차이를 포괄하려고 문자당 0.25~1.5토큰을 둔다. 한국어의 검증된 환산 계수나 신뢰구간으로 주장하지 않는다. 실제 토큰 수를 세는 API는 호출하지 않았다.

| 파일 길이 시나리오 | 한 번 읽는 원문 토큰 추정 | 의미 |
|---|---:|---|
| 중앙값 16,679자 | 약 4,170~25,019 | 일반 요약은 수용 가능성이 높지만 4000 토큰 번역 상한은 별도 문제 |
| p90 96,884자 | 약 24,221~145,326 | Haiku 100K 요금 경계를 넘을 수 있음 |
| 최대 212,142자 | 약 53,036~318,213 | Luna 272K·Qwen 256K·Grok 200K 가격 경계와 Mistral 256K 문맥을 넘을 수 있음 |

[추론] 요약은 원문과 작은 출력의 합으로 판단할 수 있다. 반면 원문과 비슷한 길이의 번역·교정은 입력 318K+출력 318K가 될 수 있다. Gemini Flash-Lite 65,536, Luna·Haiku·Qwen·GLM 128K 표준 출력 한도로는 이 시나리오를 한 번에 처리할 수 없다. Haiku Batch 베타 300K도 상단 가정에 모자라며 표준 호출과 구별해야 한다. DeepSeek의 384K 출력은 수치상 유리하지만 한국어 보존 품질·지연은 별도다 [1][5][8][10][13][17].

[추론] 현 교정처럼 YouTube 자막과 별도 ASR 전사 두 개를 넣으면 입력이 약 두 배다. 최대 표본의 상단 가정에서는 입력만 약 636K가 되어 Grok 500K·Mistral 256K보다 크다 [20][21]. 원문·출력·사고·지시문을 포함하는 모델별 토큰 예산과 세그먼트 단위 분할이 선행 조건이다 [1][20][21]. 요약의 `transcript[:2000000]`은 토큰 한도 검증이 아니다. 로컬 근거: [교정 호출부](/Users/jaesolshin/Documents/GitHub/open-scribe/src/utils/subtitle_corrector.py:50), [요약 프롬프트](/Users/jaesolshin/Documents/GitHub/open-scribe/src/utils/summary.py:62).

### 전사 API: 한국어·시간 정보·한도

금액은 파일 전사 중심이며 USD/시간, 국내 서비스는 KRW/시간이다. 공통된 한국어 CER·60분 처리 지연 측정은 수행하지 않았다. API ID 없는 서비스명은 호출 가능한 모델 문자열로 취급하지 않는다. 화자 분리의 상세 설계는 T2의 범위다.

| 공급자 / 후보 | 시간당 단가 | 파일·길이 한도 | 단어 시간과 한국어 근거 |
|---|---:|---|---|
| OpenAI `gpt-transcribe` | $0.27 ($0.0045/분) | 파일 25MB; 별도 길이 한도는 읽은 범위에서 [불명·미발견] | 새 모델의 단어 시간은 [불명·미발견]; 언어 힌트·키워드·자유 문맥 제공; 기존 모델 종료 뒤의 시간 정렬 대안 확인 필요 [3][4]. |
| ElevenLabs Scribe v2 | $0.22 기본; keyterm·편집 옵션 추가 과금 | 3GB, 표준 10시간 | 단어 `start/end` 반환; 한국어는 문서의 >10~≤20% WER군이며 CER이 아니다; 정확한 호출 문자열은 이 개요의 본문에서 [불명·미발견] [23][24]. |
| Deepgram `nova-3` / `nova-3-general` | 파일 요율 [불명·미발견]; 11-04 canonical 가격표에는 streaming $0.0077/분(단일), $0.0092/분(다국어)이 노출됨 | 2GB; 처리 시간 10분 제한은 오디오 10분 제한과 다름 | 한국어 `ko`와 다국어 지원; `words[].start/end` 초 단위; streaming 단가를 파일 단가로 바꾸어 비용 합산하지 않았다 [25][26][39]. |
| AssemblyAI Universal-2 | $0.15; 화자 옵션 +$0.02 | transcript 5GB·10시간; 로컬 upload는 2.2GB | `ko` 지원; Universal-3.5 Pro의 파일용 18언어 목록에는 한국어가 없으므로 그 품질·가격을 한국어 Universal-2의 결과로 간주하지 않는다; 단어 시간은 별도 검증 필요 [27][28][41]. |
| Google `gemini-3.5-transcribe` | 약 $0.30: 입력·출력 토큰 가정에 따른 추정 $0.005/분 | 기본 1시간; 단어 시간 또는 화자 옵션 사용 시 30분; 바이트 한도는 본문에서 [불명·미발견] | `ko-KR`, 단어 시작·종료 지원; 단어 시간 활성화가 인식 정확도를 낮출 수 있음; custom vocabulary와 단어 시간 동시 사용 불가 [9][29]. |
| Mistral Voxtral Small Transcribe 3 / `voxtral-small-transcribe-latest` | $0.24 ($0.004/분) | 읽은 모델·이행 자료에서 파일 상한 [불명·미발견] | Voxtral 3는 세그먼트만 지원, `word` 요청은 400; 발표의 FLEURS 집계는 한국어에 CER을 사용하지만 한국어 개별 수치는 [불명·미발견] [30][31]. |
| Mistral `voxtral-mini-transcribe-3-0` | $0.21 ($0.0035/분) | 파일 상한 [불명·미발견] | Small과 같은 이행 문서의 단어 시간 제거 제약; 모델 크기·가격 차이를 한국어 정확도 차이로 대체하지 않는다 [30][31]. |
| Speechmatics Melia 1 서비스 | 11-05 보완: 무할인 파일 $0.24, 실시간 $0.40; 화면의 $0.12/$0.20은 할인 적용 표시 | 읽은 가격·한국어 소개에서 파일 상한 [불명·미발견] | 단어 시간 지원; 한국어 소개의 최대 96% word accuracy는 시험셋·CER·Melia 고정 버전의 근거가 아님; Melia의 정확한 API selector는 [불명·미발견] [32][33]. |
| RTZR `sommers` | 1,000원; 월 1,000시간 이하 T1 | 2GB·4시간, 작업 시작까지 일반 5분 이내 또는 혼잡 시 30분 이상 가능 | 한국어·일본어, `use_word_timestamp=true`; 시작 대기 시간과 전체 처리 시간은 구별 [34][35]. |
| RTZR `whisper` | 동일 1,000원 | 동일 2GB·4시간 | `language` 필수, `multi`·`detect` 경로와 `use_word_timestamp` 제공; 최신 한국어 CER은 [불명·미발견] [34][35]. |
| CLOVA Speech 장문 서비스 | 음성 인식 1,200원; 15초당 5원 | 2GB; sync 2시간, async/Batch 6시간 | `language="enko"` 한/영 동시 인식, `wordAlignment`, 단어 `[시작ms,종료ms,텍스트]` 반환; 고정 모델 API ID는 도메인 기반 서비스여서 이 자료에 없음 [37][38][40]. |
| NVIDIA / OpenRouter `nvidia/nemotron-3.5-transcribe` | $0.1188 ($0.000033/초); PAYG 충전 수수료 별도 | 원모델·라우터 카드 최대 1시간; 공통 multipart 25MB, JSON도 제공자별 한도 적용 | NVIDIA 카드에 한국어·영어와 40언어, 한국어 FLEURS CER 2.78%; 원모델 단어 시간과 OpenRouter 응답 노출은 구별; 해당 경로의 word/diari 계약은 [불명·미발견] [43][44][45][46]. |

기존 OpenAI 기준선은 mini $0.003/분, 상위 전사·Whisper $0.006/분이다 [3]. 현재 코드의 GPT-4o 계열 타임스탬프는 30초 청크 시작값을 붙이는 경로이며 단어 정렬이 아니다. 공식 문서는 기존 GPT-4o 전사 응답 형식과 Whisper의 `verbose_json`·단어 옵션을 구별한다 [4]. [추론] 새 엔진을 붙일 때 문자열만 반환하는 공통 인터페이스를 유지하면 새 단어 시간을 저장·소비할 경로가 없다. 로컬 근거: [base.py](/Users/jaesolshin/Documents/GitHub/open-scribe/src/transcribers/base.py:23), [openai.py](/Users/jaesolshin/Documents/GitHub/open-scribe/src/transcribers/openai.py:110).

### Nemotron 호스팅 경로와 기존 추천에 미치는 영향

OpenRouter 카드의 정확한 ID는 `nvidia/nemotron-3.5-transcribe`, 출시 표기는 2026-10-29이며 11-05 조회 당시 제공자는 DeepInfra 한 곳이다; EU in-region 경로는 없다고 명시한다 [43]. NVIDIA 공식 카드는 40언어·최대 1시간·65,536토큰 문맥과 한국어 ASR·영어 간 번역·다화자 ASR·code-switching을 표기한다 [44]. 라우터는 약 30B/4B active라고 소개하고, 원카드는 음성 인코더를 포함한 **총 34B 중 약 4.3B active**로 설명하므로 전체 가중치 규모와 토큰당 활성 규모를 구별한다 [43][44]. [추론] 활성 4.3B를 전체 34B 가중치의 상주 메모리 규모로 취급할 수 없다.

원모델의 한국어 FLEURS CER은 **2.78%**다; 카드의 같은 표에서 한국어 CoVoST2는 미보고다 [44]. [추론] 한국어 근거가 있는 저단가 비교군에 이 후보를 추가할 이유가 된다. 이 수치를 RTZR의 2023 평균 CER이나 Scribe의 WER군과 직접 순위화하지 않는다. NVIDIA 카드의 원모델 시험이지 DeepInfra의 호스팅 정밀도·프롬프트·옵션·한국어 강연 표본을 고정한 재현 결과는 아니다. 카드의 한국어 `Leading`도 공급자 등급이며 외부 검증 점수가 아니다 [44].

모델 페이지의 예시는 `POST /api/v1/audio/transcriptions`에 JSON `input_audio:{data:<base64>,format:"wav"}`를 보내 `text`를 읽는다 [43]. 공통 STT 가이드는 OpenAI SDK 방식의 multipart도 지원하지만, 응답 형식은 `json/verbose_json`이며 **`text/srt/vtt`는 400으로 거부**한다고 명시한다 [45]. [추론] 현재 코드가 기본적으로 `response_format="text"`를 보내므로 base URL·모델명만 바꾼 무수정 호환은 성립하지 않는다. JSON 요청 또는 문서화된 multipart 경로와 응답 어댑터, 엔진 등록·인증 설정·예외 처리가 필요하다. 로컬 근거: [현재 전사 호출부](/Users/jaesolshin/Documents/GitHub/open-scribe/src/transcribers/openai.py:110).

가이드는 multipart 25MB, 일부 제공자 외의 큰 JSON 본문 제한, upstream 처리 timeout 60초를 명시한다 [45]. [추론] 모델이 1시간 오디오를 지원한다는 사실은 1시간 파일이 게이트웨이를 통과한다는 보장이 아니다. 큰 녹음은 압축·청크·시간 offset 보존을 함께 검토해야 한다. OpenRouter의 약 10초 P50 표시는 요청 오디오 길이와 한국어 표본이 고정되지 않아 60분 파일의 처리 시간으로 사용할 수 없다 [43].

NVIDIA 카드에는 `ctc_timestamps`와 화자 정보가 있지만, OpenRouter 가이드는 모델·제공자마다 구조화 응답이 다르고 미지원 `verbose_json`은 거부될 수 있다고 설명한다 [44][45]. 해당 Nemotron 경로가 단어·화자 필드를 실제로 노출하는지와 provider 옵션은 [불명·미발견]이며, generic `timestamp_granularities` 설명만으로 지원을 단정하지 않는다. 상세 diarization 계약은 별도 T2 검토 대상이다.

[추론] 이 후보는 저비용 파일 전사 비교의 우선순위가 높아진다. 기존 OpenAI·Scribe·Google·RTZR 후보도 같은 표본에서 함께 비교한다. 단일 제공자의 장애 대체 경로, 한국어 실측 CER·용어 보존·단어 시간 계약이 검증되지 않아 운영 기본 엔진 교체를 확정할 근거는 아니다 [43][44][45]. 텍스트 요약·교정·번역 추천은 오디오 전사 모델 추가만으로 바뀌지 않는다.

2023-08-25 RTZR 공개 평가의 그 표본에서는 테스트셋별 3,000문장을 평가했고 평균 CER은 RTZR 6.18%, RTZR Whisper 7.79%, CLOVA 9.52%, OpenAI Whisper 11.39%, Google API v2 11.50%였다. 한국어 강의 열에서는 각각 7.76%, 8.68%, 13.71%, 10.89%, 11.48%다. 평가자는 공급자 RTZR이며 그 당시 엔진·표본의 결과다. 2026 후보의 승패·교체 효과로 옮길 수 없다 [36].

[추론] 현재 후보의 한국어 CER 비교표는 대부분 비어 있다. ElevenLabs의 WER군, Speechmatics의 word accuracy, Mistral의 다국어 평균 WER/CER를 위 2023 CER 열에 넣는 것은 지표·시점·시험셋을 혼합한다. 한국어·영어 혼합 강연에서는 용어·숫자·부정 표현의 오류, CER 정규화 규칙, 단어 시간 오차와 처리 지연을 같은 표본에서 따로 측정해야 한다. 이번 문헌만으로 가장 정확한 공급자를 확정하지 않는다 [23][30][33][36].

### 용도별 비교군 — 최소 3개씩

다음은 [추론]에 따른 평가 우선순위이며, 성능 승자나 도입 확정이 아니다. 공개 가격·한도와 구현 조건으로 후보를 좁혔고, 공통 한국어 실측은 [불명·미검색]이다.

| 용도 | 비교할 후보 | 기대되는 장점 | 판정을 가르는 항목 |
|---|---|---|---|
| 요약 | Luna, Haiku 5.5, DeepSeek Flash, Gemini Flash-Lite | Luna·짧은 Haiku 입력은 저단가; DeepSeek는 긴 출력 여유; Gemini는 문서 처리·구조화 기능 | 근거 없는 내용 추가, 핵심 누락, 타임코드 일치, effort별 총토큰·완료 지연 [1][5][8][10]. |
| 교정 | Haiku 5.5, Luna, DeepSeek Flash | 긴 문맥으로 전후 용어를 볼 수 있고 별도 추론 설정을 제공 | ASR 오류와 실제 발화의 구별, 숫자·명사·부정문 보존, 수정 구간 외 변경, 세그먼트 누락; 출력 분할 선행 [1][5][10][11]. |
| 번역 | Gemini Flash-Lite, Haiku 5.5, DeepSeek Flash, Luna | Gemini 가격 문서는 번역을 용도로 명시; 다른 세 모델은 긴 문맥과 설정 가능한 추론 | 한국어 자연스러움과 의미 보존을 분리 평가, 용어집 일관성, 65K/128K 출력 한도, 문장·시간 정렬 [1][5][9][10]. |
| 전사 | GPT-Transcribe, Scribe v2, Gemini Transcribe, RTZR Sommers/Whisper, Nemotron 3.5 Transcribe 호스팅 | 기존 비교군에 Nemotron의 낮은 초당 단가와 원카드 한국어 근거를 추가 | 한국어 CER, 혼합 영어 용어, 청크 경계, 단어 시간 노출, 단일 제공자와 JSON/multipart 응답 형식, 재시도 포함 비용 [4][23][29][35][43][44][45]. |

[추론] 전사의 새 공급자 도입은 텍스트 LLM보다 변경량이 크다. 공통 결과에 세그먼트·단어 시작/종료, 원문, 언어, 공급자, 완료 상태를 보존하고 현재 문자열 출력은 그 결과의 렌더링으로 두는 편이 적합하다. REST 비동기 작업·polling·시간 단위 정규화·파일 한도 분할도 공급자별로 필요하다. 현 경로의 부분 청크 실패를 성공 문자열과 구별하는 요구도 함께 검토해야 한다. 근거: [현재 인터페이스](/Users/jaesolshin/Documents/GitHub/open-scribe/src/transcribers/base.py:23), [청크 결과 처리](/Users/jaesolshin/Documents/GitHub/open-scribe/src/transcribers/openai.py:186), 공급자 응답·한도 [23][29][35][39][40].

### 월 20건 비용 시나리오

실제 오디오 길이는 [불명·미검색]이다. 20건 모두 30/60/120분이라고 가정하면 월 10/20/40시간이다. 아래는 ASR 사용량 환산액이며 세금·환율·플랜 기본료/최소청구·추가 기능·재시도·저장·네트워크 비용은 제외한다. Google은 공급자의 입력 25 audio tokens/초, 출력 175 text tokens/분 가정에 따른 근사치다. 한국어 출력 토큰 수가 다르면 변한다 [9].

| 전사 경로 | 월 10시간 | 월 20시간(60분×20) | 월 40시간 | 계산 근거 |
|---|---:|---:|---:|---|
| 기존 OpenAI mini | $1.80 | $3.60 | $7.20 | $0.003/분 [3]. |
| 기존 OpenAI 상위 / Whisper | $3.60 | $7.20 | $14.40 | $0.006/분 [3]. |
| GPT-Transcribe | $2.70 | $5.40 | $10.80 | $0.0045/분 [3]. |
| Scribe v2 | $2.20 | $4.40 | $8.80 | 표시 단가 $0.22/시간; 계정 플랜의 최소청구는 별도 확인 필요 [24]. |
| AssemblyAI Universal-2 | $1.50 | $3.00 | $6.00 | $0.15/시간 [27]. |
| Gemini 3.5 Transcribe | 약 $3.00 | 약 $6.00 | 약 $12.00 | 공급자 추정 $0.005/분 [9]. |
| Voxtral Small / Mini 3 | $2.40 / $2.10 | $4.80 / $4.20 | $9.60 / $8.40 | $0.004/$0.0035/분 [30]. |
| Speechmatics Melia 파일 | $2.40 | $4.80 | $9.60 | **11-05 보완 요금** 무할인 $0.24/시간; 11-04 소급 적용 [불명·미발견] [32]. |
| RTZR 두 모델 | 10,000원 | 20,000원 | 40,000원 | T1 1,000원/시간, 최초 가입 무료분 제외한 반복월 [34]. |
| CLOVA 장문 음성 인식 | 12,000원 | 24,000원 | 48,000원 | 15초당 5원 [38]. |
| Nemotron 3.5 Transcribe / OpenRouter | $1.188 | $2.376 | $4.752 | 오디오 초당 $0.000033; 120분 파일은 1시간 이하로 분할, 중첩·재시도 제외 [43]. |

Deepgram은 파일용 정확한 단가를 확정하지 못해 위 합산에 넣지 않았다 [25]. 기존 표본을 streaming 요금으로 대신 계산하지 않았다. [불명·미발견]인 비용 항목이며 미완 사항이다. RTZR은 가입 시 10시간 무료, CLOVA의 Free 플랜은 20분 무료지만 반복월 기본 단가 비교와 구분했다 [34][38].

Nemotron은 `0.000033×3,600=$0.1188/시간`이며, `20×60×60×0.000033=$2.376`이 60분×20건의 순수 사용량 환산이다 [43]. 입력·출력 토큰 가격에 `$0`가 표시돼도 오디오 초당 과금이 있으므로 무료가 아니다 [43]. OpenRouter Standard PAYG는 사용량을 선충전 크레딧에서 차감하고 충전 시 5.5%, Business는 8% 수수료를 부과하며 요청별 추가 마크업과 구별한다 [46]. 월 최소 사용량이 없다는 설명은 실제 충전 거래의 최소액·최소 수수료까지 없다는 증명이 아니다; 이번 가격표만으로 그 금액은 [불명·미발견]이다.

[추론] Standard에서 장기간 소비액만큼 충전하고 거래별 최소 수수료가 영향을 주지 않는다는 가정이면 Nemotron 20시간은 `2.376×1.055≈$2.507`이다 [43][46]. 이는 현금 청구액이나 첫 충전액이 아니다. 재시도·청크 중첩·세금과 실제 결제 조건은 별도다.

후처리 계산도 [추론]의 계획용 시나리오다. 원문 토큰 수를 `T`라 하고 요약·단일 전사 교정·번역을 각각 한 번 수행한다. 각 단계가 원문 `T`를 읽고, 교정·번역 출력은 각각 `T`, 요약 출력은 1000토큰이라 가정한다. 월 입력은 `60T`, 출력은 `40T+20,000`이다. 현재 두 원문 교정의 추가 입력·프롬프트·분할 중첩·사고 토큰은 포함하지 않는다. 비용 공식은 `입력토큰×입력단가/1M + 출력토큰×출력단가/1M`이다.

Luna는 짧은 캐시 쓰기 단가 0.125, Haiku는 5분 캐시 쓰기 0.125/장문 0.625로 모든 입력을 보수적으로 계산했다. 캐시 재사용 절감은 가정하지 않는다. DeepSeek는 혼잡 시간, Gemini는 캐시 저장 없이 계산했다. Haiku 100K·Luna 272K 경계를 각 끝값에 적용했다. 아래 금액은 `max`의 숨은 사고 토큰을 포함한 견적이나 실청구액이 아니다 [1][5][9][10].

| 20건 모두 해당 크기라는 가정 | 코드 기본 GPT-5 mini의 단가 산술 | Luna | Haiku 5.5 | DeepSeek Flash 혼잡 | Gemini Flash-Lite |
|---|---:|---:|---:|---:|---:|
| 중앙값 16,679자 | $0.44~2.42 | $0.12~0.70 | $0.12~0.70 | $0.30~1.68 | $0.54~3.00 |
| p90 96,884자 | $2.34~13.85 | $0.68~4.01 | $0.68~20.03 | $1.62~9.62 | $2.91~17.20 |
| 최대 212,142자 | $5.08~30.27 | $1.47~14.33 | $1.47~43.80 | $3.52~21.03 | $6.31~37.60 |

표의 GPT-5 mini 단가는 입력 0.25·출력 2.00을 적용한 비교 기준선이다 [3]. 공식 lifecycle 원문은 `gpt-5-mini`와 `gpt-5-mini-2025-08-07`을 deprecated로 표시하고 종료 예정일을 **2026-12-11**로 명시한다 [42]. 이 일정은 11-05 보완 조회이며,사용자의 계정에서 현재 호출된다는 보장은 아니다. 가격표 존재와 훅 경고를 종료 상태의 근거로 사용하지 않았다. 이 행은 현재 호출 가능한 운영 견적이 아닌 **공개 단가의 산술 기준선**이다.

[추론] 최대 크기 행의 단일 호출 수용성은 충족하지 않을 수 있으므로 이 금액은 실행 가능한 한 번의 요청 비용이 아니다 [1][5][8][10]. 실제 분할은 장문 할증을 낮출 수도 있고, 반복 입력·사고·재시도로 비용을 높일 수도 있다 [1][5][10]. 현 두 원문 교정이면 월 입력 `20T`가 더 필요하다.

[추론] 중앙값 파일 20건·오디오 각 60분의 단순 조합에서는 GPT-Transcribe와 Luna 후처리가 약 **$5.52~6.10/월**, Scribe와 Luna는 약 **$4.52~5.10/월**이다 [1][3][24]. 이는 위 두 가정의 합이며 현재 실청구·최고 품질·`max` 사용 비용을 뜻하지 않는다. 긴 원문과 추가 사고 토큰이 비용 비교에 더 큰 영향을 줄 수 있다 [1].

[추론] 같은 가정의 Nemotron+Luna 조합은 사용량 기준 약 **$2.50~3.07/월**이다; Nemotron의 충전 수수료·프롬프트/옵션 지원·분할·재시도를 제외한 산술이다 [1][43][46]. 낮은 금액만으로 한국어 품질이나 기존 코드의 적합성을 확정하지 않는다.

## 남은 질문

1. **[불명·미발견] 최신 한국어 품질 순위:** 후보들의 동일 강연 CER·요약 누락·교정 오수정·번역 의미 보존·완료 지연을 함께 측정한 1차 근거를 찾지 못했다. 2023 CER 수치만으로 2026 교체를 확정할 수 없다.

2. **[불명·미발견] 일부 정확한 API 계약:** Scribe v2의 호출 문자열, Melia의 selector, MiniMax·Mistral의 최대 출력, 일부 공급자의 캐시 쓰기·strict schema 세부 조건을 이번 원문 범위에서 확정하지 못했다. 문서 소개명과 실행 ID를 구별해 남겼다.

3. **[불명·미발견] 전사 미완 항목:** 새 OpenAI 전사의 단어 시간, Deepgram 파일 요금, Voxtral·Speechmatics 파일 한도, AssemblyAI 단어 시간의 별도 응답 계약이다. Google 단어 시간 사용 시 30분·정확도·어휘 옵션 배타성은 확인했다.

4. **[불명·미검색] 실행 적합성과 실비용:** 계정별 모델 접근성, 설치된 SDK의 새 필드, 실제 오디오 길이·한국어 토큰 수·effort별 사고 토큰·지연·재시도율은 호출 금지 범위에 따라 측정하지 않았다. 제품 코드 변경과 실행 시험은 이번 산출물에 포함되지 않는다.

5. **시점과 할인:** Speechmatics 11-05 가격은 보완 조회다; 공개 HTML의 무할인 `baseHourly`는 파일 0.24·실시간 0.40이며 화면은 학습 할인·물량 할인 스위치가 켜진 상태다 [32]. [추론] 파일 `0.24×0.67×0.75=0.1206`은 표시 $0.12를 설명한다. 계정의 학습 할인은 기본 꺼짐이라는 설명도 확인했다. 11-04 계산기의 $0.24/시간과 무할인 파일 요율은 일치하지만, 해당 날짜의 정책 적용 보장은 [불명·미발견]이다. 공개 HTML과 날짜별 추출을 감사 자료에 보존했다.

외부 1차 출처는 46개로 목표 20~40개보다 6개 많다. 위 미확정 계약·품질·실비용과 Nemotron 호스팅의 단어/화자 응답 계약은 미완으로 남긴다. 추적 자료는 `/tmp/open-scribe-research-2026-11/t3/source-notes.md`, 전체 인용쌍은 `pairs.jsonl`, 문장별 판정은 `citation-audit.jsonl`이다. 기계 검사 통과를 근거 검증으로 간주하지 않는다.

## 출처

[1] OpenAI, GPT-6 Luna 모델 원문, https://developers.openai.com/api/docs/models/gpt-6-luna — 조회 2026-11-04. 문서 갱신일 미표기; 지식 기준일 2026-05-18은 발행일이 아님. 동일 공식 `.md` 원문도 확인.

[2] OpenAI, Using GPT-6, https://developers.openai.com/api/docs/guides/latest-model — 조회 2026-11-04. 갱신일 미표기; 매개변수 호환 절 확인.

[3] OpenAI, API Pricing, https://developers.openai.com/api/docs/pricing — 조회 2026-11-04. 갱신일 미표기; Standard와 전사 표 사용.

[4] OpenAI, File transcription, https://developers.openai.com/api/docs/guides/speech-to-text — 조회 2026-11-04. 종료 예정일 2027-02-26·25MB·기존 timestamp 옵션 확인.

[5] Anthropic, Claude Haiku 5.5 overview, https://platform.claude.com/docs/en/models/haiku-5-5/overview — 조회 2026-11-04. 명시 출시일 2026-10-07.

[6] Anthropic, Effort, https://platform.claude.com/docs/en/build-with-claude/effort — 조회 2026-11-04. 갱신일 미표기; Haiku 5.5의 다섯 강도·기본값 확인.

[7] Anthropic, Multilingual support, https://platform.claude.com/docs/en/build-with-claude/multilingual-support — 조회 2026-11-04. 갱신일 미표기; Global-MMLU 영어 대비 비율.

[8] Google, Gemini 3.5 Flash-Lite, https://aistudio.google.com/docs/models/gemini-3.5-flash-lite — 조회 2026-11-04. 명시 latest update 2026-07. ai.google.dev 경로의 공식 리디렉션 본문도 확인.

[9] Google, Gemini Developer API pricing, https://aistudio.google.com/docs/pricing — 조회 2026-11-04. 갱신일 미표기; Flash-Lite·Transcribe 입력/출력·캐시 표.

[10] DeepSeek, Models & Pricing, https://api-docs.deepseek.com/quick_start/pricing/ — 조회 2026-11-04. 본문 모델 버전 V4.1-Flash-1017; 문서의 HTTP/Jina 날짜를 발행일로 간주하지 않음.

[11] DeepSeek, Thinking Mode, https://api-docs.deepseek.com/guides/thinking_mode/ — 조회 2026-11-04. 갱신일 미표기; 강도 매핑과 OpenAI 형식 예시.

[12] Alibaba Cloud, Model inference pricing, https://www.alibabacloud.com/help/en/model-studio/model-pricing — 조회 2026-11-04. 원문 명시 갱신일 2026-11-02; 싱가포르 고정 버전 사용.

[13] Alibaba Cloud, Text generation models, https://www.alibabacloud.com/help/en/model-studio/text-generation-model — 조회 2026-11-04. 조회 본문 Qwen3.7/3.8 표; 발행일 미확인.

[14] Moonshot, Model Inference Pricing, https://platform.kimi.ai/docs/pricing/chat — 조회 2026-11-04. 갱신일 미표기; K3.1 Pro·캐시 TTL 가격 표.

[15] Moonshot, Kimi K3.1 Pro guide, https://platform.kimi.ai/docs/guide/kimi-k3-1-pro-quickstart — 조회 2026-11-04. 갱신일 미표기; 출력·effort·schema·sampling 제약.

[16] Z.ai, Pricing, https://docs.z.ai/guides/overview/pricing — 조회 2026-11-04. 갱신일 미표기; GLM-5.3-Flash의 유료 요율.

[17] Z.ai, GLM-5.3-Flash/FlashX, https://docs.z.ai/guides/vlm/glm-5.3-flash — 조회 2026-11-04. 갱신일 미표기; Flash와 FlashX 속도를 구별.

[18] MiniMax, API Pricing, https://platform.minimax.io/subscribe/token-plan?tab=api-enterprise — 조회 2026-11-04. 조회 시 공식 pricing/overview로 연결되는 본문; M3.1-Flash 표 사용.

[19] MiniMax, Anthropic SDK/API compatibility, https://platform.minimax.io/docs/api-reference/text-anthropic-api — 조회 2026-11-04. 갱신일 미표기; M3.1-Flash 호출 ID·1M 문맥·기본 max 확인.

[20] Mistral, Mistral Small 4, https://docs.mistral.ai/models/mistral-small-4-0-26-03 — 조회 2026-11-04. 명시 출시일 2026-03-16, API ID mistral-small-2603.

[21] xAI, Developer release notes, https://docs.x.ai/developers/release-notes — 조회 2026-11-04. Grok 4.7의 2026-09-21 항목 사용; 별도 4.6 표와 구별.

[22] OpenRouter, DeepSeek V4.1 Flash route, https://openrouter.ai/deepseek/deepseek-v4.1-flash — 조회 2026-11-04. 동적 제공자/가격 표; 모델 출시 표기는 2026-09-10.

[23] ElevenLabs, Transcription capabilities, https://elevenlabs.io/docs/overview/capabilities/speech-to-text/ — 조회 2026-11-04. 갱신일 미표기; Scribe v2 언어군·응답·한도.

[24] ElevenLabs, ElevenAPI pricing, https://elevenlabs.io/pricing/api — 조회 2026-11-04. 갱신일 미표기; PAYG와 부가 기능 표.

[25] Deepgram, Pricing, https://deepgram.com/pricing — 조회 2026-11-04. 갱신일 미표기; canonical 본문의 streaming 표와 prerecorded 설명 구별.

[26] Deepgram, Models & Languages Overview, https://developers.deepgram.com/docs/models-languages-overview — 조회 2026-11-04. 갱신일 미표기; Nova-3 한국어·다국어 목록.

[27] AssemblyAI, Pricing, https://www.assemblyai.com/pricing — 조회 2026-11-04. 갱신일 미표기; Universal-2와 Pro 및 부가 기능 구별.

[28] AssemblyAI, Models, https://www.assemblyai.com/docs/getting-started/models — 조회 2026-11-04. 기존 FAQ URL이 이 문서로 리디렉션됨; 파일용 18언어와 Universal-2 한국어 구별.

[29] Google, Audio transcription, https://aistudio.google.com/docs/transcribe — 조회 2026-11-04. 갱신일 미표기; Gemini 3.5 Transcribe의 1시간/30분·어휘/시간 옵션 배타성.

[30] Mistral, Voxtral 3 announcement, https://mistral.ai/news/voxtral-3/ — 조회 2026-11-04. 추출 원문 발행일 2026-10-22; 모델 카드의 10-20 표기와 구별. 가격·다국어 집계 시험 설명 사용.

[31] Mistral, Migrate from Voxtral 2, https://docs.mistral.ai/studio/audio/migrate-from-voxtral-2 — 조회 2026-11-04. 갱신일 미표기; Voxtral 3의 word timestamp 제거·API alias 표.

[32] Speechmatics, Pricing, https://www.speechmatics.com/pricing — **조회 2026-11-05 KST**. 갱신일 미표기; 원문 추출·공개 HTML의 할인 스위치 상태·내장 공개 요율 설정을 함께 확인. 파일/실시간 무할인 baseHourly 0.24/0.40과 할인 표시 0.12/0.20 구별.

[33] Speechmatics, Korean speech to text, https://www.speechmatics.com/speech-to-text/korean — 조회 2026-11-04. 갱신일 미표기; 한국어 지원·시간 정보·word accuracy 주장.

[34] RTZR, 사용 요금, https://developers.rtzr.ai/docs/pricing/ — 조회 2026-11-04. 갱신일 미표기; T1·최소 10초·가입 무료분·VAT 별도.

[35] RTZR, 일반 STT API, https://developers.rtzr.ai/docs/stt-file/ — 조회 2026-11-04. 갱신일 미표기; 모델명·단어 시간·2GB/4시간·대기 시간.

[36] RTZR, 한국어 음성인식 AI 랭킹, https://blog.rtzr.ai/korean-speechai-benchmark/ — 조회 2026-11-04. 발행 2023-08-25. 공급자가 직접 시행한 과거 평가.

[37] Naver Cloud, CLOVA Speech 사용 준비, https://guide.ncloud-docs.com/docs/clovaspeech-spec — 조회 2026-11-04. 갱신일 미표기; 언어·파일 크기·동기/비동기 길이.

[38] Naver Cloud, 요금 안내의 CLOVA Speech 표, https://www.ncloud.com/charge/region/ko — 조회 2026-11-04. 갱신일 미표기; 음성/화자/이벤트의 별도 15초 요율.

[39] Deepgram, Pre-recorded audio getting started, https://developers.deepgram.com/docs/pre-recorded-audio — 조회 2026-11-04. 갱신일 미표기; 2GB·처리 timeout·단어 시작/종료 응답.

[40] Naver Cloud, Object Storage 파일 인식 API, https://api.ncloud-docs.com/docs/ai-application-service-clovaspeech-longsentence — 조회 2026-11-04. 갱신일 미표기; language·wordAlignment·단어 배열 계약.

[41] AssemblyAI, File size/duration limits FAQ, https://www.assemblyai.com/docs/faq/are-there-any-limits-on-file-size-or-file-duration-for-files-submitted-to-the-api — 조회 2026-11-04. 현 문서 갱신일 미표기; 같은 제목의 이전 지원 문서는 2024-06-25 갱신 표기였으며 이를 현 문서 갱신일로 복제하지 않음.

[42] OpenAI, Deprecations, https://developers.openai.com/api/docs/deprecations — **조회 2026-11-05 KST**. 2026-06-11 공지 항목의 GPT-5 mini 종료 예정일 2026-12-11을 확인한 보완 조회.

[43] OpenRouter, Nemotron 3.5 Transcribe 호스팅 카드·요청 예시, https://openrouter.ai/nvidia/nemotron-3.5-transcribe — **조회 2026-11-05 KST**. 출시 표기 2026-10-29; DeepInfra 단일 제공자·오디오 초당 과금·EU 경로 부재 확인.

[44] NVIDIA, NVIDIA-Nemotron-3.5-Transcribe-30B-A4B 공식 모델 카드, https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B — **조회 2026-11-05 KST**, main의 원문 스냅샷 보존. 한국어 지원 행·FLEURS CER 2.78·원모델 시간 정보와 호스팅 계약 구별. 가중치는 다운로드하지 않음.

[45] OpenRouter, Speech-to-Text API guide, https://openrouter.ai/docs/guides/overview/multimodal/stt — **조회 2026-11-05 KST**. 갱신일 미표기; JSON/base64와 multipart·25MB·60초 timeout·응답 형식·모델별 structured output 차이.

[46] OpenRouter, Pricing / Standard·Business PAYG, https://openrouter.ai/pricing — **조회 2026-11-05 KST**. 갱신일 미표기; 충전 시 5.5%/8%와 사용량 과금 구별. 과거 블로그의 최소 수수료를 현 가격표 수치로 대체하지 않음.
