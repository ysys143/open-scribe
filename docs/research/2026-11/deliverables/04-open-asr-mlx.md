# T4 — 공개 ASR·양자화·Apple Silicon/MLX 문헌 조사

**사용자 확정 제약: 로컬 30B급 모델은 채택·추천 대상에서 제외한다.** Nemotron3.5 Transcribe는 총34B인 대형 MoE이며 active4.3B를 소형 모델로 분류하지 않는다. 양자화·GGUF·MLX 지원 정보는 검토 기록으로만 보존한다. mini64e 같은 pruned 변형도 크기·resident 메모리를 확인하지 않은 로컬 우회 대안으로 추천하지 않는다. 호스팅 검토는 T3 범위다.

조사 기준일: 2026-11-04 KST. 원문 조회는 11-04에 시작했으며 자정 이후 추가 확인은 11-05로 구분한다. 개별 모델 ID·문서 표기 시점과 조회 시점은 다르다. 날짜 없는 `main` 문서를 해당 프로젝트의 최신 릴리스라고 판정하지 않았다. 이번 작업은 문헌 조사이며 설치, 가중치 다운로드, 전사 실험, 제품 코드 변경은 수행하지 않았다.

질문: 한국어·영어 기술 강연과 대담을 전사하는 open-scribe에 적용할 수 있는 공개 ASR의 양자화 및 Apple Silicon/MLX 실행 경로는 무엇인가?

하위 질문은 ① 한국어를 명시적으로 지원하는 체크포인트는 무엇인가, ② 한국어 CER·영어 WER의 비교 조건은 무엇인가, ③ 각 모델에 어떤 로컬 런타임과 양자화 경로가 있는가, ④ 장시간·단어 시간·환각·라이선스 제약은 무엇인가, ⑤ 기존 whisper-cpp 복구와 MLX 어댑터의 적용 순서는 무엇인가이다. 심층 검토는 **A. 한국어 지원과 평가의 비교 가능성**, **B. Apple Silicon 실행과 통합 경로** 두 축으로 제한했다. 아래 사례 분석도 이 두 축에 포함한다.

## 요약

[추론] 사용자 제약 안의 로컬 추천은 **Whisper turbo/cpp 복구, Qwen3-ASR-0.6B·1.7B 비교, 영어 Parakeet·Phonon 비교**다.[1][3][5][8][20][24][60][64][72] Nemotron30B급의 native MLX 구현은 확인했으나 로컬 추천에서 제외했다.[66] 기능 지원과 사용자 장비에서 채택할 모델의 선택은 별개다.

Parakeet v3와 Canary v2의 25개 언어는 유럽 언어 중심이며 한국어를 포함하지 않는다.[5][6] Canary-Qwen-2.5B도 영어 전용이다.[7] Qwen3-ASR·SenseVoiceSmall·Dolphin·Cohere Transcribe·Nemotron 3.5는 각각 한국어를 명시한다.[8][14][29][33][38]

[추론] 한국음향학회 논문의 공백 제거 CER, BuzzASR 카드의 공백 차이를 포함하는 CER, 변환자의 FLEURS 382문장 CER은 조건이 달라 단일 순위로 합칠 수 없다.[2][30][36] Moonshine Korean Tiny의 6.46은 문서가 **WER**로 명시하므로 CER로 전재하지 않는다.[31]

Kyutai는 자체 MLX 구현을 제공한다.[11] MLX Whisper는 Apple의 `ml-explore` 예제이며 OpenAI가 제공한 MLX 가중치와 구별한다.[19] Qwen MLX 4bit는 `mlx-community` 변환이다.[32] IBM과 Cohere는 외부 `mlx-audio` 사용 경로를 자기 카드에 안내한다.[12][29][37] [추론] 이처럼 공식 구현, 제공자의 외부 통합 안내, 커뮤니티 변환을 따로 기록해야 한다.

[불명·미발견] M3 Max·36GiB에서 동일 조건으로 통제한 전체 후보의 CER/WER·RTF·최대 메모리 비교는 확보하지 못했다. 새 전사 실측도 없다. 초기 24행만으로 최신 후보 조사를 마친다는 판단은 철회했다. **11-05 KST에 HF ASR trending 첫 30카드를 모두 선별하고, 추가 모델·포맷 20행을 보완해 총44행**을 정리했다. ASR 범위 밖 6카드는 별도 제외 근거를 남겼다. 출처는 원문 확인71항목과 공식 GGUF 접근 실패1항목으로 총72항목이며, 최초 목표40을 초과한 자료도 보존했다.

## A. 한국어 지원과 평가의 비교 가능성

### 후보와 라이선스

다음 표의 “미지원”은 제공자가 열거한 ASR 언어 범위에 한국어가 없거나 영어 전용이라고 밝힌 경우다. 언어 식별이나 VAD의 언어 수를 ASR의 언어 수로 옮기지 않았다. “한국어 전용” 모델을 영어 전사용 모델로 추천하지 않는다. 라이선스는 조사한 카드·저장소의 표기를 옮긴 것이며 코드와 가중치가 다른 경우 분리했다.

| ID | 체크포인트·범위 | 한국어 / 영어 ASR | 가중치 라이선스·주의 | 확인 근거 |
| --- | --- | --- | --- | --- |
| M01 | Whisper large-v3, 약 1.55B | 지원 / 지원 | 원 저장소 MIT / Hub metadata Apache-2.0 불일치 | 다국어 Whisper·한국어 평가; 약정 표시 차이 보존 [1][30][70] |
| M02 | Whisper large-v3-turbo, 809M | 지원 / 지원 | MIT | decoder 32→4층; 모델 압축과 정수 양자화는 별개 [1][3] |
| M03 | distil-large-v3.5, 756M | 미지원 / 지원 | MIT | Distil-Whisper English 계열 [4] |
| M04 | Parakeet-TDT-0.6B-v3 | 미지원 / 지원 | CC-BY-4.0 | 25개 언어 목록에 ko 없음 [5] |
| M05 | Canary-1B-v2 | 미지원 / 지원 | CC-BY-4.0 | 25개 언어 목록에 ko 없음 [6] |
| M06 | Canary-Qwen-2.5B | 미지원 / 지원 | CC-BY-4.0 | 영어 전용이라고 명시 [7] |
| M07 | Qwen3-ASR-0.6B | 지원 / 지원 | Apache-2.0 | 30개 언어와 22개 중국 방언을 구분 [8] |
| M08 | Qwen3-ASR-1.7B | 지원 / 지원 | Apache-2.0 | 한국어 ko 명시; ForcedAligner는 별도 모델 [8] |
| M09 | Voxtral-Mini-3B-2507 | 한국어 보장 미확인 / 지원 | Hub 메타데이터 Apache-2.0; 약정 전문 미검토 | 열거된 주요 8개 언어에 한국어 없음; “다국어”만으로 지원 판정하지 않음 [10] |
| M10 | Voxtral-Mini-4B-Realtime-2602 | 지원 / 지원 | Apache-2.0 | 한국어를 포함한 FLEURS 언어별 표 [9] |
| M11 | Kyutai stt-2.6b-en | 미지원 / 지원 | CC-BY-4.0; Python 코드 MIT | 1B en_fr와 2.6B en을 구분 [11] |
| M12 | Granite-4.0-1b-speech | 미지원 / 지원 | Apache-2.0 | EN/FR/DE/ES/PT/JA의 6개 언어 [12] |
| M13 | Granite-speech-5.0-2b | 미지원 / 지원 | Apache-2.0 | 2026-10-20 공개 표기; 한국어 추가 없음 [37] |
| M14 | Moonshine Korean Tiny, 26M | 한국어 전용 / 영어용 별도 모델 | **Community 비상업 조건**; 영어·streaming 모델의 MIT와 구별 | 한국어 streaming 후속 모델은 읽은 문서에서 아직 미제공 [13] |
| M15 | SenseVoiceSmall | 지원 / 지원 | 코드 MIT; 가중치는 FunASR 모델 약정 참조 | 공개 Small 체크포인트는 중·광둥·영·일·한 5개 언어; 연구 전체의 50+와 다름 [14] |
| M16 | FireRedASR2-AED | 미지원 / 지원 | 저장소 Apache-2.0; 가중치별 약정은 [불명·미검색] | ASR은 중·영·중국 방언; 100+ 언어 VAD/LID와 구별 [15] |
| M17 | Dolphin small, 약 0.4B | 지원 / 영어는 열거 목록에서 미발견 | 코드·가중치 Apache-2.0 | ko/ko-KR 명시; 중동·아시아 등 40개 언어 [16][33] |
| M18 | omniASR_LLM_7B, 초기 계열 | 지원 / 지원 | Apache-2.0 | 한국어 결과 CSV와 1,600+ 언어 계열 [17][34] |
| M19 | omniASR_CTC_300M_v2 | 계열에 한국어 / 계열에 영어 | Apache-2.0 | **이 체크포인트 자체의 한국어 CER는 [불명·미발견]**; 7B LLM 점수 전용 금지 [17][34] |
| M20 | ghost613/whisper-large-v3-turbo-korean | 한국어 미세조정 / 영어 보존 [불명·미발견] | [불명·미발견] 읽은 카드에 가중치 라이선스 선언 없음 | Zeroth 한국어 미세조정 [18] |
| M21 | cohere-transcribe-03-2026, 2B | 지원 / 지원 | Apache-2.0; Hub 파일 접근 동의 화면은 별개 | 14개 언어에 Korean 명시 [29] |
| M22 | BuzzASR/korean, Whisper large-v3 기반 | 한국어 전용 / 영어 전용 사용 대상 아님 | MIT | 한국어 SFT 모델; 범용 Whisper와 구별 [36] |
| M23 | VibeVoice-ASR, MLX 문서상 9B | 한국어 학습 분포 확인 / 지원 | MIT | 카드의 언어 분포 그림에 Korean; 이것만으로 한국어 품질을 보장하지 않음 [23][35] |
| M24 | Nemotron-3.5-ASR-Streaming-0.6B | 지원 / 지원 | OpenMDW-1.1 | ko-KR를 transcription-ready로 구분 [38] |

Realtime 4B 카드에는 한국어 평가값이 있지만 Voxtral Mini 3B 카드의 주요 언어 목록에는 한국어가 없다.[9][10] [불명·미발견] 3B의 한국어 지원을 보장하는 추가 원문은 이번 검색에서 확보하지 못했다.

### 한국어 CER·WER: 데이터셋과 조건을 보존한 수치

| 출처·모델 | FLEURS 한국어 | Common Voice 한국어 | KsponSpeech clean / other | Zeroth 한국어 | 해석 경계 |
| --- | --- | --- | --- | --- | --- |
| 한국음향학회 Qwen3-ASR-1.7B | [불명·미검색] | [불명·미검색] | **12.76 / 12.60% CER_NS** | 권장 설정 전체셋 **3.77% CER_NS** | Kspon 값은 각 모델의 최적 디코딩; Zeroth와 설정이 다름 [30] |
| 같은 논문 Qwen3-ASR-0.6B | [불명·미검색] | [불명·미검색] | **15.15 / 15.01% CER_NS** | 권장 설정 전체셋 **5.02% CER_NS** | 공백 제거; 해당 논문 내 비교 [30] |
| 같은 논문 Whisper large-v3 | [불명·미검색] | [불명·미검색] | **13.89 / 13.62% CER_NS** | [불명·미발견] | 위 Qwen과 동일 오디오·참조·정규화; beam 탐색 포함 [30] |
| BuzzASR/korean 원모델 | **5.16% CER** | **4.24% CER**, CV25 | [불명·미발견] | [불명·미발견] | jiwer 3.0.4 정규화, 공백 차이 포함; 통합 CER 4.61% [36] |
| 같은 BuzzASR 카드의 Whisper large-v3 기준선 | **5.31% CER** | **6.01% CER**, CV25 | [불명·미발견] | [불명·미발견] | 이 카드 내부의 기준선으로만 비교 [36] |
| Moonshine Korean Tiny | **6.46% WER** | [불명·미발견] | [불명·미발견] | [불명·미발견] | accuracy.md가 WER로 명시; CER 값으로 사용 금지 [13][31] |
| Nemotron 3.5, 한국어 힌트 / 자동 감지 | 320ms에서 **7.27 / 7.81% CER** | [불명·미발견] | [불명·미발견] | [불명·미발견] | chunk 80ms~1.12s, 힌트/자동 감지에 따라 달라짐 [38] |
| Voxtral Realtime 4B | 480ms 지연에서 한국어 **15.74%** | [불명·미발견] | [불명·미발견] | [불명·미발견] | **카드 표에서 한국어 CER/WER 구분을 명시하지 않아 지표 [불명·미발견]**; 순위화 제외 [9] |
| ghost613 turbo 한국어 | [불명·미발견] | [불명·미발견] | [불명·미발견] | test **2.06% CER / 4.89% WER** | 원래 Zeroth test를 validation/test 각 절반으로 나눔; test 약 2h22m [18] |
| Omnilingual 초기 7B LLM | 데이터셋별 분리 [불명·미발견] | 데이터셋별 분리 [불명·미발견] | [불명·미발견] | [불명·미발견] | 공개 CSV의 kor_Hang **5.8% CER**; CSV에는 평가셋 식별자가 없음 [34] |
| SenseVoiceSmall·Dolphin·Cohere·VibeVoice | [불명·미발견] | [불명·미발견] | [불명·미발견] | [불명·미발견] | 읽은 텍스트에서 재현 조건까지 확보한 개별 한국어 수치 없음; 이미지·추가 논문 전체 수치 추출은 미완 |

2026-09-30 논문은 9개 코퍼스에서 10개 평가셋을 만들고, 조합별 표본 탐색 뒤 권장 설정을 전체 8개 평가셋에 검증했다.[30] NumPattern과 Welfare는 전체 검증에서 제외됐다.[30] 권장 설정의 Kspon clean 1.7B는 12.79%이고, 최적 조합의 12.76%와 다르다.[30] 저자도 이 두 Kspon 셋의 비교를 한국어 전반의 우위로 일반화하지 않는다.[30]

[추론] ghost613의 2.06%를 Qwen의 Zeroth 3.77%와 직접 비교하면 원래 test의 절반과 전체 457발화, 정규화 및 디코딩 차이를 섞게 된다.[18][30] [추론] 원 논문의 설정과 fine-tune의 분할부터 맞추는 비교가 필요하다.

### Apple M3의 별도 측정 사례

다음은 변환자 voyagar가 공개한 **M3·16GB** Tractus 측정값이다.[2] 사용자 **M3 Max·36GiB**에서 이번에 측정한 값이 아니다. FLEURS는 382문장, HiKE는 1,121발화, 회의는 4세션·5.2시간을 무음 기준 30초 이하로 나눴다고 밝힌다.[2] 원 오디오·전체 결과는 이번 조사에서 재현하지 않았다.

| 모델·해당 측정의 정밀도 | FLEURS-ko CER | HiKE MER / PIER | 회의 CER | 회의 영어 용어 재현율 | 회의 RTF | 최대 GPU 메모리 |
| --- | --- | --- | --- | --- | --- | --- |
| BuzzASR Korean MLX 8bit | 4.02% | 22.79 / 32.40% | 10.29% | 86.3% | 0.169 | 2.33GB |
| Qwen3-ASR-1.7B MLX 8bit | 2.62% | 28.30 / 35.43% | 9.49% | 71.6% | 0.136 | 3.63GB |
| Whisper large-v3-turbo, 정밀도 상세 미기재 | 3.08% | 27.73 / 35.37% | 14.92% | 87.4% | 0.100 | 2.15GB |

위 세 행의 출처는 변환자가 직접 수행했다고 기술한 동일 카드이며, RTF를 처리 시간/오디오 길이로 정의한다.[2] 원모델 FP16과 같은 평가셋에서 양자화 전후를 비교하지 않았다고 카드가 직접 밝힌다.[2] [추론] 따라서 이 표로 8bit 손실의 크기를 산출할 수 없다.

### 영어 WER와 Open ASR Leaderboard의 시점 차이

Open ASR 버전 레지스트리의 `02-11-2026` 항목은 기본 평가셋에서 LS Clean/Other를 빼고 URGENT24, Voice Arena 및 비공개 scripted/conversational 항목을 포함한다.[28] [추론] 따라서 예전 8개 공개셋 평균을 현재 기본 설정의 순위로 읽을 수 없다. 결과 CSV 본문은 이번 Jina·내장 조회에서 401/접근 실패였으며 접근 로그를 감사 메모에 남겼다. **현재 기본 설정의 순위는 [불명·미발견]**이다.

| 모델 | 제공자 문서의 Open ASR 평균 WER | 같은 문서의 속도 | 시점·범위 |
| --- | --- | --- | --- |
| Parakeet-TDT-0.6B-v3 | **6.34%** | [불명·미발견] 해당 표에 RTFx 없음 | AMI~VoxPopuli의 8개 공개셋; 카드 공개일 2025-08-14 [5] |
| Canary-1B-v2 | **7.15%** | **RTFx 749** | 8개 공개셋, 실행 장비는 해당 표에서 미발견 [6] |
| Canary-Qwen-2.5B | **5.63%** | **RTFx 418** | 문서 Version 2.5.0; 카드 공개일 2025-07-17 [7] |
| Granite-4.0-1b-speech | **5.52%** | **RTFx 280.02** | 8개 공개셋; 공개일 2026-03-06 [12] |
| Cohere Transcribe 03-2026 | **5.42%** | [불명·미발견] 재현 조건을 갖춘 해당 표 값 없음 | 카드에 인용된 8개 공개셋 평균 [29] |
| distil-large-v3.5 | [불명·미발견] Open ASR 동일 평균 미확보 | turbo 대비 상대 RTFx **1.46** | 자체 OOD short WER 7.08%, long 11.39%; Open ASR 평균과 구별 [4] |
| Granite Speech 5.0 2B | [불명·미발견] 본문 텍스트 수치 추출 미완 | [불명·미발견] | 카드 그림은 Open ASR 2026-10-21 결과라고 명시 [37] |
| 나머지 후보 | [불명·미발견] 동일 조건의 평균 미확보 | [불명·미발견] | 원문에 있는 개별 데이터셋 점수로 빈 평균을 채우지 않음 |

이 보고서에서 RTFx는 오디오 길이/처리 시간으로 정의하며 RTF의 역수다. [추론] 장비와 배치가 다른 값에서 M3 Max 처리 시간을 산출할 수 없다. Distil의 1.46은 turbo 대비 상대 RTFx다.[4] Voxtral의 480ms는 transcription delay이고, Qwen의 2,000배는 동시성128의 처리량이다.[8][9] [추론] 이 수치들은 같은 속도 지표로 정렬할 수 없다.

## B. Apple Silicon 실행과 통합 경로

### 모델 24행 × 요청된 런타임 9종

기호는 **D**=해당 체크포인트 또는 명시된 예제가 문서에 있음, **F**=계열 지원만 확인하고 해당 체크포인트의 변환·로드는 미확인, **V**=문서화된 변환 경로가 있지만 해당 산출물 검증은 미수행, **?**=[불명·미검색] 해당 조합의 개별 지원 검증을 하지 않음이다. D도 이번 장비에서 실행했다는 뜻은 아니다. `TF/MPS`의 V는 [추론] Transformers 구현과 일반 MPS 경로를 조합해 검토할 수 있다는 표기다. 개별 ASR의 MPS 연산 호환성은 [불명·미검색]이며, 일반 MPS 경로만 문서로 확인했다.[27]

| 모델 ID | whisper.cpp Metal/CoreML | faster-whisper int8 | mlx-whisper | lightning-whisper-mlx | mlx-audio | parakeet-mlx | WhisperKit | sherpa-onnx | TF/MPS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01 large-v3 | D | D | V | D | F | ? | V | F | V |
| M02 turbo | D | D | V | ? | D | ? | D | D | V |
| M03 distil v3.5 | D | D | V | F | F | ? | V | ? | V |
| M04 Parakeet v3 | ? | ? | ? | ? | D | D | ? | D | V |
| M05 Canary v2 | ? | ? | ? | ? | F | ? | ? | F | ? |
| M06 Canary-Qwen | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M07 Qwen3 0.6B | ? | ? | ? | ? | D | ? | ? | D | V |
| M08 Qwen3 1.7B | ? | ? | ? | ? | D | ? | ? | ? | V |
| M09 Voxtral 3B | ? | ? | ? | ? | D | ? | ? | ? | V |
| M10 Voxtral Realtime | ? | ? | ? | ? | D | ? | ? | ? | V |
| M11 Kyutai 2.6B | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M12 Granite 4.0 | ? | ? | ? | ? | D | ? | ? | ? | V |
| M13 Granite 5.0 | ? | ? | ? | ? | D | ? | ? | ? | V |
| M14 Moonshine ko Tiny | ? | ? | ? | ? | ? | ? | ? | F | ? |
| M15 SenseVoiceSmall | ? | ? | ? | ? | ? | ? | ? | D | ? |
| M16 FireRedASR2-AED | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M17 Dolphin small | ? | ? | ? | ? | ? | ? | ? | F | ? |
| M18 Omni LLM 7B | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M19 Omni CTC 300M v2 | ? | ? | ? | ? | ? | ? | ? | F | ? |
| M20 ghost613 turbo ko | V | V | V | ? | V | ? | V | ? | V |
| M21 Cohere Transcribe | ? | ? | ? | ? | D | ? | ? | D | V |
| M22 BuzzASR ko | V | V | V | ? | D | ? | V | ? | V |
| M23 VibeVoice-ASR | ? | ? | ? | ? | D | ? | ? | ? | V |
| M24 Nemotron 3.5 | ? | ? | ? | ? | D | ? | ? | ? | ? |

Whisper 계열의 cpp·faster·변환 경로는 각 런타임의 모델/변환 문서와 Distil의 사용 예제에서 확인했다.[4][19][20][21][25] 한국어 fine-tune 행의 V는 원 Whisper 아키텍처 기반의 변환 후보라는 [추론]이며, 동등한 출력을 검증한 뜻이 아니다.[18][19][36]

lightning 문서는 large-v3 및 distil-large-v3를 열거하고 4bit/8bit를 제공한다.[22] turbo·distil-v3.5의 명시적 항목은 [불명·미발견]이므로 각각 ?와 F로 남겼다. 문서의 10배·4배 속도 문구는 비교 장비·오디오·정밀도·WER 조건을 읽은 범위에서 확보하지 못해 성능 우위의 근거로 채택하지 않았다.[22]

mlx-audio의 STT 표와 예제는 Whisper turbo, Qwen3, Parakeet, Voxtral, VibeVoice, Nemotron 등을 열거한다.[23] Granite 4.0/5.0 및 Cohere는 각 제공자 카드에서도 mlx-audio 경로를 확인했다.[12][29][37] Python mlx-audio 표의 Moonshine은 EN이라고 쓰여 있어 한국어 Tiny까지 지원한다고 확대하지 않았다.[23]

sherpa 변경 기록은 turbo, Parakeet v3, Dolphin CTC, Moonshine, Omnilingual **CTC**, Qwen3-ASR **0.6B**, Cohere 지원을 구분한다.[26] [추론] Canary 계열 지원만으로 1B-v2 산출물의 호환성을 확정할 수 없고, FireRed CTC 또는 Omnilingual CTC 지원을 AED 또는 LLM 체크포인트에 확대할 수 없다.

요청된 9종 외에 **Kyutai의 자체 `moshi-mlx` 경로**가 있으며 제공자 저장소가 `kyutai/stt-2.6b-en-mlx`를 안내한다.[11] 따라서 공식 MLX 경로로 구분했고, 위 표의 mlx-audio 열이 ?여도 자체 MLX 구현은 이용 후보로 남는다.

### 런타임별 양자화·장치 경계

| 런타임 | Apple Silicon 실행·양자화 문헌 | 주의점·검증되지 않은 부분 |
| --- | --- | --- |
| whisper.cpp | GGML 가중치, Metal GPU; CoreML은 encoder를 ANE에서 실행; 정수 Q5_0 등 [20] | CoreML encoder 별도 산출물·빌드가 필요; Metal·MLX·CoreML은 다른 경로 |
| faster-whisper | CTranslate2 기반, CPU/GPU int8; ARM64 CPU 하드웨어 범위 확인 [21][39] | 읽은 CTranslate2 사전 빌드 GPU 목록은 NVIDIA/AMD; Apple GPU Metal 지원은 [불명·미발견] |
| mlx-whisper | Apple `ml-explore/mlx-examples`; 모델 변환과 4bit 양자화 예제, 단어 시간 API [19] | MLX 원본 변환과 미리 변환된 community 가중치를 구별 |
| lightning-whisper-mlx | community 구현, batched decoding, 4bit/8bit [22] | 기본 batch 12의 메모리 경고; 재현 가능한 한국어 양자화 손실은 [불명·미발견] |
| mlx-audio | community/외부 유지 프로젝트, 여러 STT 아키텍처와 양자화·변환 도구 [23] | 공용 변환 도구가 있다는 사실만으로 모든 STT 체크포인트·bit 수를 보장하지 않음 |
| parakeet-mlx | senstella의 외부 MLX 구현, community Parakeet 가중치, 문장·토큰 시간 [24] | NVIDIA 공식 MLX 가중치와 구별; 기본 120초 chunk/15초 overlap |
| WhisperKit | Argmax Swift/CoreML 변환 도구, turbo 압축·일반 변형 및 단어 시간 [25] | MLX가 아님; 626MB 표기는 모델 배포 크기이며 최대 메모리가 아님 |
| sherpa-onnx | ONNX 모델별 export와 C++/Python 등 API [26] | MLX가 아님; ONNX 지원과 macOS에서의 특정 가속 provider 성공은 별개 |
| Transformers MPS | 확인한 문서는 v5.22.1, PyTorch `mps`, 통합 메모리와 미지원 연산의 CPU fallback 설명 [27] | 특정 ASR의 MPS 성공·최대 메모리·양자화 정확도는 모두 [불명·미검색] |

### 메모리와 양자화 손실

| 근거·범위 | 수치·조건 | 적용 경계 |
| --- | --- | --- |
| OpenAI Whisper README | large 약 10GB VRAM, turbo 약 6GB; 상대 속도는 A100 영어 기준 [1] | PyTorch 경로 안내이며 MLX/cpp의 통합 메모리 실측이 아님 |
| whisper.cpp README | large 디스크 2.9GiB, 메모리 약 3.9GB [20] | 장비·정밀도·동시성 전체 조건이 없는 안내값; M3 Max의 여유 메모리 보증 아님 |
| faster-whisper v1.1.0 비교 | RTX3070Ti·CUDA12.4, large-v2·13분, beam5: FP16 63초/4525MB, int8 59초/2926MB [21] | **large-v2** 결과를 v3/turbo·M3 Max에 전용하지 않음 |
| 같은 README의 CPU 비교 | i7-12700K·8 threads, small: FP32 157초/2257MB, int8 102초/1477MB [21] | Intel CPU 수치이며 Apple CPU·GPU 실측 아님; 동일 WER 손실 값 미제시 |
| Qwen3-ASR-1.7B MLX 4bit 카드 | mlx-audio 0.3.1 변환, Hub 표기 1.6GB [32] | 가중치/배포 표시를 최대 실행 메모리로 해석하지 않음; FP16 대비 한국어 CER 손실 [불명·미발견] |
| BuzzASR ko MLX 8bit 카드 | 원 FP16 3.09GB→1.64GB; group size64, 원본 revision `411b68546497bd0efb87599ad7ad4d98fa3dbc62` [2] | 같은 평가셋의 FP16 정확도 미측정이라고 명시; 양자화 손실 크기 [불명·미발견] |
| Moonshine English Streaming Tiny | 같은 LibriSpeech-clean 비교: 재현 float WER4.52%→배포 int8 4.83%; VAD off, whole utterance [31] | **+0.31%p**는 이 영어 경로의 차이; 한국어 Whisper/Qwen의 int8 손실을 뜻하지 않음 |
| Omnilingual CTC300M_v2 / LLM7B | A100·BF16·batch1·30초: 약 2GiB/17GiB, RTF0.001/0.092 [17] | 다운로드 FP32 크기 1.3GiB/30GiB와 실행 VRAM을 분리; M3 Max 실측 아님 |
| 나머지 모델·bit 조합 | [불명·미발견] 읽은 카드·README에서 한국어 양자화 전후 통제 비교 없음 | 후보별 동일 오디오·정규화·디코딩 실험을 해야 할 미완 항목 |

Moonshine 문서는 2026-07-30 이전 tensor 단위 scale의 Tiny Streaming WER7.57%와 이후 per-channel scale의 4.83%를 구분한다.[31] [추론] 이 사례는 같은 int8이라도 산출물과 방식이 다르므로 모델 ID, revision, 변환 도구 버전, 양자화 방식·group size를 함께 기록해야 함을 보여 준다.[31]

### 장시간·시간 정보·환각

| 후보·경로 | 장시간 문헌 | 시간 정보 | 환각·누락 관련 경계 |
| --- | --- | --- | --- |
| Whisper large-v3/turbo | sliding window/chunking 경로 [1][3] | mlx-whisper/faster-whisper 단어 시간; cpp는 실험적 word timestamp [19][20][21] | 모델 카드가 비발화 텍스트·반복을 명시 [3]; 양자화의 환각 개선 효과는 [불명·미발견] |
| Distil v3.5 | sequential long-form과 chunked를 구분 [4] | Whisper 계열 경로; 해당 장비 정렬 정확도 [불명·미검색] | 자체 long OOD WER11.39%; 짧은 클립 점수로 장시간 우위를 단정하지 않음 [4] |
| Parakeet v3 | full attention 최대24분은 A100 80GB 조건, local attention 최대3시간 [5] | 단어·세그먼트; parakeet-mlx 결과 구조 제공 [5][24] | 무음 환각률의 M3 측정 [불명·미발견] |
| Canary v2 / Canary-Qwen | v2는 1초 overlap dynamic chunk; Qwen variant의 학습 입력 최대40초 [6][7] | v2는 보조 CTC 타임스탬프 모델 사용; Qwen variant는 [불명·미발견] [6][7] | MUSAN48h: v2 134.7, Qwen138.1 chars/min; 서로 같은 출력 제한인지 추가 확인 필요 [6][7] |
| Qwen3-ASR | streaming/offline·장시간 전사 도구 제공 [8] | **별도 ForcedAligner-0.6B**, 한국어 포함11개 언어·최대5분 단위 [8] | 생성 토큰 상한으로 인한 잘림과 인위적 반복 억제의 실제 반복어 삭제를 따로 점검 [30] |
| Voxtral 3B / Realtime4B | 3B 전사 최대30분; Realtime sliding attention, 구현의 사전 할당 제한 설명 [9][10] | Realtime의 지연과 단어 정렬 정확도는 다른 항목; 단어 시간 [불명·미발견] | 카드에 Transformers 지원 안내와 “현재 vLLM only” 문구가 공존; 설치 버전별 재확인 필요 [9] |
| Kyutai STT | native streaming [11] | 단어 시간·고정 text delay 보정 [11] | 2.6B는 영어용; 한국어 환각 평가로 전용 금지 |
| Granite4/5 | 장시간·번역 개선 설명; 본 장비 최대 길이 [불명·미검색] [12][37] | 선택한 기본 체크포인트의 단어 시간 [불명·미발견]; plus 모델과 혼동 금지 | 한국어 미지원이며 별도 한국어 점수·환각 수치를 채우지 않음 |
| Moonshine Korean Tiny | streaming 모델과 구별되는 non-streaming 경로 [13] | 한국어 단어 시간 [불명·미발견] | 비라틴 문자 토큰 수가 많아 반복 감지 임계값을 잘못 쓰면 정상 출력이 잘릴 수 있다고 설명 [13] |
| SenseVoiceSmall | VAD 분할 및 제한 메모리 창 경로 [14] | 현 repo는 words와 대응하는 ms timestamp 배열; 과거 포맷과 다름 [14] | 화자 정보는 별도 VAD/CAM++ 결합이며 ASR 자체의 개인 식별 아님 [14] |
| FireRedASR2-AED | VAD/ASR/Punc 결합 시스템 [15] | AED의 단어 timestamp 예제 [15] | VAD/LID의 다국어 수를 한국어 ASR 지원으로 전용 금지 |
| Dolphin | VAD·분할 지원; 2026-05-09 공지에 word timestamp 추가 [16] | 제공자는 모든 Dolphin 모델의 단어 시간 지원이라고 기술 [16] | 실제 한국어 단어 경계 품질·무음 오류율 [불명·미발견] |
| Omnilingual | CTC/LLM 일반 suite는 40초 미만, Unlimited v2는 별도 계열 [17] | 선택 모델의 단어 시간 [불명·미발견] | 초기7B CSV·v2·Unlimited의 점수와 실행 조건을 섞지 않음 |
| ghost613 / BuzzASR | Whisper 창/외부 분할 후보; Buzz MLX 측정은 ≤30초 VAD 분할 [2][18] | 런타임 정렬 기능 후보; 한국어 오차 실측 [불명·미검색] | Buzz 변환자는 확인한50문장 중1건의 발화 뒤 연장 출력과 FP16 대조 미실시를 공개 [2] |
| Cohere | 분할 전사 예제; 단일 사전 지정 언어가 적합 [29] | **timestamp·diarization 내장 없음** [29] | 자동 언어 식별 없음, code-switch 불안정, 무음에 VAD/noise gate 권고 [29] |
| VibeVoice-ASR | 최대60분·64K 입력 문맥, 구조화 출력 [35] | speaker/시작/종료 구조; 단어 시간인지 [불명·미발견] | 내장 익명 화자 번호와 저장된 개인 목소리 재식별은 별개라는 [추론] |
| Nemotron 3.5 | cache-aware RNNT streaming, chunk80ms~1.12s [38] | 해당 카드에서 단어 시간 [불명·미발견] | 언어 힌트/자동 감지, locale별 표기 등 평가 조건 유지 |

### 보존해야 하는 문헌 간 차이

Moonshine의 Available Models는 한국어 행을 WER/CER 공용 열에 싣지만 Accuracy 문서는 한국어 6.46을 WER라고 명시한다.[13][31] 이 보고서는 WER로 보존하고 CER 순위를 만들지 않았다. 영어 floating-point와 배포 int8의 점수는 문서에서도 구분한다.[31]

BuzzASR 원 카드의 현재 권장값은 beam5이며 이전 greedy·반복 제한 권장값이 더 나빴다는 평가를 소개한다.[36] 반면 2026-10-22 변환 카드의 제한 사항은 원 카드가 그 이전 반복 제한값을 권장한다고 기술한다.[2] [추론] 두 문서가 같은 설정 시점을 반영하지 않으므로, 변환 카드의 품질·속도를 원 카드의 새 설정에 대한 MLX 측정으로 취급할 수 없다.[2][36]

Voxtral Realtime 카드는 13개 언어 설명과 “dozens” 문구, Transformers 사용 절과 “currently only vLLM” 문구가 공존한다.[9] 문서 전체가 특정 릴리스에 맞춰 정리됐다고 가정하지 않았다. [불명·미검색] 정확한 라이브러리 버전별 지원 경계는 남아 있다.

### HF trending 첫 페이지 30카드 전수 선별 보완

원래 질문의 최신 후보 범위를 다시 확인하기 위해 `pipeline_tag=automatic-speech-recognition&sort=trending` 첫 페이지 **30항목을 2026-11-05 00:16 KST경**에 저장했다.[41] 이 날짜는 조회일이며 조사 기준일은 11-04로 유지한다. 순서는 저장 당시의 순서다. 다운로드·좋아요 수나 “updated N days ago”를 모델 품질·공개일·11-04 시점 상태의 근거로 쓰지 않았다. 각 카드의 본문, 조회일, API의 revision/lastModified/언어/약정 메타데이터를 별도 저장했다.

| 순번 | 실제 카드 ID | 판정 | 한·영 범위·형식 및 근거 |
| --- | --- | --- | --- |
| 1 | nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B | 추가분석 M25 | 한국어·영어, BF16 원 체크포인트; streaming0.6B와 다른34B MoE [42] |
| 2 | pyannote/speaker-diarization-community-1 | 한영 ASR 대상 제외 | 화자 구간 분리 pipeline, 단어 전사 모델 아님; T2 계약 범위 [43] |
| 3 | pyannote/speaker-diarization-3.1 | 한영 ASR 대상 제외 | 위와 다른 구버전 화자 분리 pipeline; ASR 모델 수에 합산하지 않음 [44] |
| 4 | third-intelligence/Haas-ja-v1.0 | 한영 대상 제외 | 일본어 ASR; CUDA/Triton 필요, 카드가 macOS 미지원 명시 [45] |
| 5 | AtomicChat/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-GGUF | 변형구분 M29 | AtomicChat 자체 양자화·imatrix; NVIDIA 공식 GGUF와 다름 [46] |
| 6 | openai/whisper-large-v3 | 기존검토 M01 | 실제 HF 카드 재열람; 원 저장소 MIT와 Hub Apache-2.0 표시 차이 [1][70] |
| 7 | nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-NVFP4 | 변형구분 M26 | 공식 ModelOpt NVFP4, 공식 GPU 경로는 Blackwell; MLX 별도 구현 검토 [47][66] |
| 8 | nvidia/nemotron-3.5-asr-streaming-0.6b | 기존검토 M24 | 한국어 RNNT streaming; Transcribe30B와 구별 [38] |
| 9 | ibm-granite/granite-speech-5.0-2b | 기존검토 M13 | 6개 언어, 한국어 없음 [37] |
| 10 | nvidia/parakeet-tdt-0.6b-v3 | 기존검토 M04 | 유럽25개 언어, 한국어 없음 [5] |
| 11 | Cactus-Compute/whistle | 추가분석 M31 | 영어 포함7개 언어, 한국어 없음;16.9MB `.cact`/Needle CPU [48] |
| 12 | nvidia/nemotron-labs-unified-asr-0.6b | 추가분석 M32 | offline/streaming 통합 RNNT, 유럽25개 언어;한국어 없음 [49] |
| 13 | erayyapagci/balbal-v2-manas | 추가분석 M33 | 터키어·영어 CPU CTC+KenLM; community 약정 [50] |
| 14 | CohereLabs/cohere-transcribe-03-2026 | 기존검토 M21 | 한국어·영어, timestamp/LID 제한 유지 [29] |
| 15 | moondream/parakeet-ultra | 추가분석 M34 | Parakeet v3 post-training·full precision; 25개 언어, 한국어 없음 [51] |
| 16 | akhaliq/nemotron-3.5-transcribe-mini-64e | 변형구분 M30 | REAP expert pruning;BF16/W4A16·speech fused/text-only backbone 구분 [52] |
| 17 | Phsoft-ai/Notesoop-STT-Ko-v1 | 추가분석 M35 | 한국어 강의 특화, PyTorch MPS 직접 측정 공개;MLX 아님 [53] |
| 18 | openai/whisper-large-v3-turbo | 기존검토 M02 | turbo 원 카드 재열람 [3] |
| 19 | ai4bharat/indic-conformer-600m-multilingual | 한영 대상 제외 | 22개 인도 언어용; 영어·한국어 ASR 지원 근거 미발견 [54] |
| 20 | ibm-granite/granite-speech-5.0-470m-turboctc | 추가분석 M36 | 10-21 multilingual 업데이트, 영어 포함7언어, Apache-2.0;한국어 없음 [55] |
| 21 | inclusionAI/Ming-3.0-asr-tiny | 추가분석 M38 | 중·영 ASR, MIT; 한국어 없음, tiny라는 이름을 크기 보증으로 쓰지 않음 [56] |
| 22 | ConwayResearch/Underdog-Bark-3.0 | 추가분석 M39 | 영어, ultra 기반 압축;MLX/CoreML 패키지별 조건 구분 [57] |
| 23 | ggerganov/whisper.cpp | 변형구분·기존 M01/M02 연결 | GGML 변환 가중치 저장소이며 새 ASR 아키텍처가 아님 [58] |
| 24 | Qwen/Qwen3-ASR-1.7B | 기존검토 M08 | 한국어 명시 및 Apache-2.0 Hub 표기 재확인 [71] |
| 25 | ibm-granite/granite-speech-5.0-470m-turboctc-nc | 변형구분 M37 | 영어 전용·CC-BY-NC-SA-4.0; 일반판7언어/Apache와 다름 [59] |
| 26 | FermionResearch/Phonon-2 | 추가분석 M40 | 영어용 low-bit Parakeet,164MB,MLX 경로 [60] |
| 27 | LocalDoc/speakwrite-azerbaijani | 한영 대상 제외 | 아제르바이잔어 CPU ASR,CC-BY-NC-4.0 [61] |
| 28 | oruk/oruk-loop-153M | 추가분석 M41 | 영어 Qwen distillation/weight sharing;상업 사용 약정 별도 [62] |
| 29 | Quran-Lab/zipformer_p-arabic-v3 | 한영 대상 제외 | 아랍어 꾸란 낭송의251기호 음소 출력;일반 한영 전사 아님,NPL1.2 [63] |
| 30 | FermionResearch/Phonon-2.5 | 추가분석 M42 | 유럽25개 언어 low-bit,156.2MB;Phonon2/2.5-English와 다른 모델 [64] |

이 표는 첫30개 **카드의 목적·지원 범위 선별**을 마쳤다는 뜻이다. 실제 모델 실행을 전수 수행했다는 뜻이 아니며 HF ASR 전체를 포괄하지도 않는다. 주요 누락으로 지적된 모델을 포함했고, 페이지 밖의 공식 FP8, 공식 GGUF 식별자, native MLX/새 GGML 런타임과 Phonon2.5-English도 추가 조사했다. 공식 GGUF 카드 본문만은 접근 실패 상태를 유지한다.

### Nemotron 3.5 Transcribe: 원 모델·서빙·변환을 나눈 검토

NVIDIA의 2026-10-28 연구 페이지는 BF16/FP8/NVFP4와 **NVIDIA 명의 GGUF**, NeMo-Speech.cpp를 직접 연결한다.[67] 공식 GGUF 링크의 존재는 확인했으나 해당 Hub 카드 본문은 Jina 재조회에서404 표시, API/raw에서401, 내장 open에서 접근 실패였다.[68] 따라서 공식 GGUF의 파일 목록·정확한 배포 크기는 [불명·접근실패]이며 AtomicChat의 파일을 대신 공식 파일이라고 기재하지 않는다.

원 체크포인트 카드는 이름의30B와 별도로 **encoder 포함 총34B·active4.3B**, Mamba-2/Transformer hybrid MoE,40개 언어,1시간·65,536 context를 명시한다.[42] 한국어는 ASR·번역·multispeaker·code-switching 행이 있고, 선택적 단어 timestamp와 speaker-attributed 출력을 제공한다.[42] BF16 예제는 H10080GB, NVFP4 예제는 RTX PRO6000 Blackwell96GB이며 공식 GPU 호환표에서 NVFP4는 Blackwell용이다.[42][47] [추론] active4.3B만으로 저장·실행 메모리를4B dense 모델 수준이라고 추정할 수 없다.

| 원문 평가 | 수치·조건 | 적용 경계 |
| --- | --- | --- |
| NVIDIA FLEURS 한국어 | **2.78% CER**, 한국어 열 명시 [42] | 동일 정규화·데이터에서 본 장비 재현은 미실행 |
| NVIDIA 영어 Open ASR | **4.71% WER**, 9개 공개셋 균등 평균;결과 capture2026-10-12 [42] | 기존8개셋·최근7개셋 평균과 직접 순위화 금지 |
| NVIDIA long-form | **10.98% WER**, CORAAL/Earnings21/22;55분 chunk·5초 overlap [42] | 명목1시간 입력 지원과 실제 평가 분할 조건을 구별 |
| 최적화 NIM | 최대2238초/초와30초 오디오0.13초,Blackwell·NVFP4+DFlash2 [42] | 카드가 **이 최적화는 공개 소스 릴리스에 아직 없고 공개 vLLM 경로는 약2배 느릴 것으로 예상**한다고 명시 |
| AtomicChat 양자화 | 2200발화·6.7h, A10080GB·NeMo-Speech.cpp `6a62501`, seed0·greedy·언어 힌트 [46] | 영/독/불/서/중 평가이며 한국어 양자화 손실은 [불명·미발견] |
| akhaliq REAP64e | 평균 WER teacher4.12→64e5.08→64e-W4A16 5.16;300클립,en/de/es+LS-clean [52] | pruning 손실과 추가 양자화 차이0.08%p를 분리;한국어·M3 수치로 전용 금지 |

### 새 런타임 NeMo-Speech.cpp와 native MLX의 실제 경로

NeMo-Speech.cpp는 `/tmp`에 source-only shallow clone하여 commit `536b17a41bef62d2a67a40ed3df61df26a4389fe`의 문서와 코드만 읽었다.[69] `metal-server` preset은 Metal ASR를 상속하고 `NEMO_SPEECH_BUILD_SPEECHLM=ON`을 켠다.[69] SALM은 PEE encoder와 llama.cpp decoder를 연결하며 일반 GPU/IGPU 선택과 `n_gpu_layers` 설정을 사용한다.[69] 따라서 단순 Metal 상수의 존재뿐 아니라 **Metal preset→SpeechLM target→SALM backend 선택 경로**까지 확인했다. 빌드·모델 로드·연산 성공은 [불명·미실행]이다.

SALM 플랫폼 문서는 CUDA batched 경로와 CPU/Vulkan 일반 경로를 열거하고 Metal을 그 표에 따로 적지 않는다.[69] 반면 AtomicChat 카드는 IQ4_NL/Q8_0의 Metal 사용을 안내한다.[46] [추론] 위 코드 연결은 Metal 실행을 검토할 구체적 경로이나, 이 문서 차이를 M3 Max 검증 완료로 덮을 수 없다. CUDA 전용 fast path의 조건이 맞지 않으면 코드가 MTP draft를 끄므로 CUDA의 batching/speculative 성능도 Metal에 전용하지 않는다.[69]

GGUF 입력은 decoder 한 파일로 끝나지 않고 **decoder+동일 checkpoint의 encoder F16 GGUF**가 필요하다.[46][69] AtomicChat은 IQ4_NL decoder19.68GB와 encoder1.67GB, 더 작은 Q2_0 변형을 제공한다고 밝힌다.[46] [추론] 이 디스크 합계만으로36GiB에서1시간 입력·KV/state·workspace가 모두 들어간다고 판정할 수 없다. NVFP4 GGUF, ModelOpt NVFP4 safetensors, MLX affine4bit는 다른 산출물이다.

별도로 mlx-audio의 native Nemotron 구현을 commit `e0833581c52963ff52b9916dc6eace8ca870aae0`에서 확인했다.[66] 공식 BF16/FP8/NVFP4의 직접 로드를 안내하며, FP8은 BF16으로 확장하고 NVFP4는 packed 상태를 유지한다고 구분한다.[66] 코드에는 CTC/alignment tokenizer가 없으면 단어 시간을 거부하는 분기와 MTP 가중치가 없으면 speculative 요청을 거부하는 분기가 있다.[66] “NVFP4이므로 MLX”라는 추정 대신 **체크포인트 형식을 읽는 별도 community 런타임 구현**을 근거로 삼는다.

| native MLX 경로의 메모리·기능 | 원문 내용 | M3 Max 검토 |
| --- | --- | --- |
| 공식 BF16 | 저장약67.5GB, 짧은 입력 MLX 측정약68.5GB [66] | 사용자 제약으로 로컬 채택 제외 |
| 공식 FP8 | 다운로드약34.7GB이나 로드 시BF16 메모리로 확장 [66] | 사용자 제약으로 로컬 채택 제외;파일크기는 resident 메모리가 아님 |
| 공식 NVFP4 | 다운로드약21.6GB, FP8모듈 확장 후 **loaded parameters약24.4GB**, 추가runtime allocation 별도 [66] | 사용자 제약으로 로컬 채택 제외;36GiB 실험을 후속 로컬 과제로 제안하지 않음 |
| nativ-community EA4bit | 가중치약19.3GB, **MTP·CTC heads 없음** [66] | 사용자 제약으로 로컬 채택 제외;지원 기능 차이의 기록만 유지 |

이 MLX 경로는 녹음을 모두 encoding한 뒤 text decode를 stream하므로 실시간 오디오 입력 streaming과 다르다.[66] SAA의 speaker ID는 녹음 내부 ID이며 개인 목소리 재식별 ID가 아니다.[66] 이 계약과 timestamp 포함/미포함 segment 차이만 T2 연결 항목으로 남기며 호스팅/OpenRouter 비교는 T3 범위다.

### 추가 후보의 한국어·품질·약정·런타임 표

아래20행을 초기24행에 더해 총44개 **체크포인트/배포 변형 행**으로 센다. 같은 base의 포맷·heads 차이를 모델 계열 수로 부풀리지 않는다. N=새 NeMo-Speech.cpp, MA=mlx-audio, T=MPS/Transformers 계열이다. D/F/V/?의 의미는 위 표와 같고 실제 실행은 없다. 표에 없는 whisper.cpp/faster/mlx-whisper/lightning/parakeet-mlx/WhisperKit/sherpa 조합은 [불명·미검색]이며 이름이 비슷하다는 이유로 지원을 채우지 않았다.

| ID | 후보·변형 | 한국어 / 영어 | 약정·품질 근거 | 새 실행 경로·구분 |
| --- | --- | --- | --- | --- |
| M25 | NVIDIA Transcribe BF16 | 지원 / 지원 | OpenMDW1.1;KO CER2.78,EN9셋WER4.71 [42] | MA D;N V(변환);공식CUDA와MLX메모리 분리 [66][69] |
| M26 | NVIDIA Transcribe NVFP4 | 지원 / 지원 | OpenMDW1.1;한국어양자화전후손실 [불명·미발견] [47] | 공식GPU Blackwell;MA D는별도구현 [66] |
| M27 | NVIDIA Transcribe FP8 | 지원 / 지원 | OpenMDW1.1 [65] | MA D지만BF16확장;파일크기로36GiB적합판정금지 [66] |
| M28 | NVIDIA 공식 GGUF 식별자 | base는한영지원 | 연구페이지가공식링크열거 [67];카드본문 [불명·접근실패] [68] | N 경로는소스확인,공식파일별형식·크기는미확인 [69] |
| M29 | AtomicChat Transcribe GGUF | base는한영지원 | OpenMDW1.1계열;2200발화검사는KO없음 [46] | N D;IQ4_NL/Q2_0/AD-NVFP4 차이;MA ? |
| M30 | akhaliq mini64e + fused W4A16 | 40언어계승주장 / 지원 | OpenMDW1.1;영어등300클립평가,KO CER불명 [52] | Transformers/vLLM Marlin CUDA;T-MPS ?,MA ?;text-only backbone별도 |
| M31 | Whistle `.cact` | 미지원 / 지원 | Apache2.0,영어등7언어 [48] | Needle자체CPU,macos-arm64,단어시간;MA ? |
| M32 | Nemotron Labs Unified0.6B | 미지원 / 지원 | OpenMDW1.1;유럽25언어 [49] | NeMo offline/streaming;기존3.5streaming과다름,MA ? |
| M33 | balbal-v2-manas | 미지원 / 지원 | balbalCommunity1.1,EN8셋WER8.67 [50] | PyTorch/ONNX+KenLM CPU;MA ?;MPS실측불명 |
| M34 | parakeet-ultra | 미지원 / 지원 | CC-BY4.0,같은저자비교EN7셋6.26→5.80 [51] | Photon GPU 예제;원Parakeet용MLX로의동등출력은미검증 |
| M35 | Notesoop-STT-Ko-v1 | 지원 / 영어보장불명 | Apache2.0,저자M1Pro16GB Zeroth457 CER16.21/WER45.40 [53] | T-MPS D(bf16);강의41:43 RTF0.0251/CER22.46,MA ? |
| M36 | Granite5.0 470M TurboCTC | 미지원 / 지원 | Apache2.0;10-21판7언어, 영어 WER5.51 대 이전판5.78 [55] | Transformers 구현/MA D(제공자 안내); MPS 성공은 미검증 |
| M37 | Granite5.0 TurboCTC-NC | 미지원 / 지원 | **CC-BY-NC-SA4.0**,영어전용 [59] | Transformers≥5.16,MA F;일반판약정·언어전용금지 |
| M38 | Ming3.0 ASR Tiny | 미지원 / 지원 | MIT,중영·hotword/context;개별EN WER숫자미추출 [56] | CUDA예제,MA D는외부port [23];T-MPS ? |
| M39 | Underdog Bark3.0 | 미지원 / 지원 | CC-BY4.0,저자EN7셋WER4.94 [57] | MA D,별도CoreMLGPU/ANE패키지;10분M2메모리약15GB 사례 |
| M40 | Phonon-2 | 미지원 / 지원 | CC-BY4.0,164MB,저자EN7셋WER5.21 [60] | MA D(5값Parakeet);M5속도를M3로전용금지 [23] |
| M41 | oruk-loop153M | 미지원 / 지원 | PolyForm small-business/noncommercial;7셋beam4 WER7.12 [62] | custom Transformers, test셋에서 checkpoint를 선택했다고 고지;MA ? |
| M42 | Phonon-2.5 | 미지원 / 지원 | CC-BY4.0,유럽25언어156.2MB,EN7셋WER5.06 [64] | Fermion MLX/CPU,단어시간;MA계열지원 [23] |
| M43 | nativ-community EA4bit | 계열한영 / 계열한영 | 약정 [불명·미검색],원본EA/정식release약정구별필요 [66] | MA D, MTP/CTC빠진19.3GBexport;공식NVFP4와기능차이 |
| M44 | Phonon-2.5-English | 미지원 / 지원 | CC-BY4.0,저자EN7셋WER4.82 [72] | 별도영어전용가중치, Fermion MLX/CPU;2.5다국어와구별 |

Notesoop의 41분43초 강의 CER22.46은 해당 저자의 M1 Pro 표본이며 Qwen/Buzz의 다른 회의·Zeroth 결과와 직접 비교하지 않는다.[53] [추론] Phonon·Underdog·Ultra의7개셋, Granite의9개셋, NVIDIA의9개셋도 정규화·revision·cleaned split이 달라 전체 평균 하나로 순위를 합치지 않는다.[42][51][55][57][60][64][72]

추가20행의 런타임 교차표도 따로 남긴다. `TF/MPS`의 V는 Transformers 구현에서 MPS를 검토할 후보일 뿐 실행 성공이 아니다. Notesoop의 D는 **자체 PyTorch MPS 예제**이며 일반 Transformers pipeline이라는 뜻은 아니다.[53] NeMo-Speech.cpp의 C는 **구현 경로를 코드로 확인하고 실제 실행은 미검증**이라는 추가 기호다.[69]

| ID | whisper.cpp | faster int8 | mlx-whisper | lightning | mlx-audio | parakeet-mlx | WhisperKit | sherpa | TF/MPS | NeMo-Speech.cpp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M25 | ? | ? | ? | ? | D | ? | ? | ? | V | V/C |
| M26 | ? | ? | ? | ? | D | ? | ? | ? | ? | ? |
| M27 | ? | ? | ? | ? | D | ? | ? | ? | ? | ? |
| M28 | ? | ? | ? | ? | ? | ? | ? | ? | ? | C |
| M29 | ? | ? | ? | ? | ? | ? | ? | ? | ? | C |
| M30 | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M31 | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M32 | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M33 | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M34 | ? | ? | ? | ? | F | F | ? | ? | ? | ? |
| M35 | ? | ? | ? | ? | ? | ? | ? | ? | D | ? |
| M36 | ? | ? | ? | ? | D | ? | ? | ? | V | ? |
| M37 | ? | ? | ? | ? | F | ? | ? | ? | V | ? |
| M38 | ? | ? | ? | ? | D | ? | ? | ? | ? | ? |
| M39 | ? | ? | ? | ? | D | F | ? | ? | V | ? |
| M40 | ? | ? | ? | ? | D | ? | ? | ? | ? | ? |
| M41 | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? |
| M42 | ? | ? | ? | ? | D | ? | ? | ? | ? | ? |
| M43 | ? | ? | ? | ? | D | ? | ? | ? | ? | ? |
| M44 | ? | ? | ? | ? | F | ? | ? | ? | ? | ? |

위 표의 D/F는 각 카드의 실행 예제와 mlx-audio의 모델 표에 대응한다.[23][53][55][57][60][64][66][72] Phonon-2.5-English의 MA는 같은5값 Parakeet 계열이지만 해당 ID의 직접 로드까지 별도 검증하지 않아 F다. Whistle의 Needle, balbal의 CPU/ONNX, Ultra의 Photon은 요청된 기존9종 밖의 자체 경로로 이미 별도 표기했다.[48][50][51]

새 약정 차이는 실제 선별 결과에 영향을 준다. TurboCTC 일반판은7언어 Apache2.0인데 `-nc`는 영어 CC-BY-NC-SA4.0이다.[55][59] balbal과 Oruk는 코드의 공개 약정과 가중치의 사업규모/상업 사용 조건을 나누고 있다.[50][62] Whisper large-v3의 원 저장소 MIT와 Hub Apache2.0 표시도 불일치로 남겼다.[1][70]

## open-scribe 적용 검토

### 용도별 추천 3개

1. **현재 로컬 경로 복구·한국어/영어 기준선: whisper.cpp Metal + Whisper turbo, large-v3 대조.** 기존 엔진이 whisper.cpp를 호출하고 turbo는 decoder를 축소한 모델이다.[3][40] [추론] Metal 지원 경로를 기준선으로 복구한 뒤 한국어·영어·혼용·무음 표본에서 full/quantized를 비교하는 순서가 적합하다.[20] 복구 자체는 정확도 개선을 검증한 결과가 아니다.

2. **한국어 강연·정확도와 정렬 비교: mlx-audio + Qwen3-ASR-0.6B/1.7B.** 두 크기의 한국어 지원·별도 ForcedAligner, 국내 독립 평가, 1.7B의 외부 M3 8bit 측정이 각각 존재한다.[2][8][30] [추론] 우선 8bit 비교 후 4bit를 검토하고, BuzzASR ko 8bit를 기술 용어·코드 전환 대조군에 포함하는 것이 적합하다.[2][36] 4bit 변환은 있으나 한국어 손실 수치는 [불명·미발견]이므로 bit 수를 아직 확정하지 않았다.[32]

3. **영어 대량 처리·단어 시간: Parakeet-TDT-0.6B-v3와 Phonon-2/2.5-English 비교.** Parakeet은 기존 단어·문장 시간 구조를, Phonon은 경량 가중치와 MLX 실행 경로를 제공한다.[24][60][72] [추론] 같은 영어 표본의 WER·단어 정렬·장시간 메모리·RTF로 비교할 소형 후보들이다. 한국어가 섞이면 이 추천의 언어 전제가 깨진다.[5][60][72]

이전 초안의 **Nemotron Transcribe NVFP4 native MLX 로컬 우선 실험 추천은 철회했다**. 공식 BF16/FP8/NVFP4·GGUF, AtomicChat·EA·pruned 변형은 기록을 유지하되 로컬30B급 제외 제약을 우회할 근거로 사용하지 않는다. 단어 시간·화자 기능은 소형 ASR와 별도 정렬/화자 모듈의 결합으로 검토하고, Nemotron 호스팅 채택·비용·서빙은 T3로 남긴다.

[추론] 영어 경량 전용 작업에는 Phonon-2.5-English/Phonon-2를 기존 Parakeet 기준선과 함께 우선 비교할 만하다.[5][60][72] 이들은 한국어용 추천이 아니다. Notesoop MPS는 한국어 특화 대조군으로 추가하되 저자의 M1 Pro 측정만으로 Qwen/Whisper 대체를 확정하지 않았다.[53] 기존 추천은 이 보완을 반영해 재검토했으며 trending 순위를 정확도 순위로 사용하지 않았다.

### 현재 whisper-cpp 복구의 범위

이번 세션의 읽기 전용 확인에서 HEAD는 `3880fcfe007965711cb89a2f4778db09d2918bfd`였다.[40] 기본 `WHISPER_CPP_EXECUTABLE`의 `whisper.cpp/build/bin/whisper-cli`와 기본 `WHISPER_CPP_MODEL`의 `whisper.cpp/models/ggml-large-v3.bin`은 **둘 다 존재하지 않았다**.[40] `.env` 값을 읽지 않은 기본 경로 검사이므로 사용자 설정의 모든 별도 경로까지 없다는 뜻은 아니다.

코드의 `is_available()`은 모델 경로 존재 여부와 실행 파일 `--help`의 반환 코드0을 검사한다.[40] 10분 초과 입력은 300초 조각으로 나누고 작업 풀에서 여러 실행 파일 프로세스를 호출한다.[40] SRT는 세그먼트 시작 시각만 남긴 문자열로 바뀌고, 합칠 때 chunk index×300초를 더한다.[40] 공통 반환형은 `Optional[str]`이며 단어 시작/끝·구조화 세그먼트 필드는 없다.[40]

[추론] 코드가 요구하는 실행 파일·가중치 경로를 맞추고 짧은 샘플의 Metal 초기화·언어·출력을 확인한 뒤, 장시간 chunk 결합과 실패 보존을 검증하는 순서로 복구를 설계할 수 있다.[20][40] CoreML 경로는 encoder 별도 산출물 생성과 빌드를 안내하므로 `.bin` 경로 설정만으로 완료되는 절차가 아니다.[20] 이 보고서에서는 복구를 실행하지 않았다.

### MLX 대체 어댑터 개요

현재 작업 풀의 whisper-cpp 메모리 상수4GB는 주석상 모델3GB+runtime1GB 가정이다.[40] MPS 문서는 CPU/GPU의 통합 메모리 공유를 설명한다.[27] [추론] 새로운 MLX 모델에 기존 상수를 그대로 적용하지 말고, 모델을 한 번 로드하는 단일 작업자를 시작점으로 실제 최대 메모리·처리량을 측정하는 설계가 적합하다.

[추론] 공통 결과 구조에는 원문 text, segments(start/end/text), 선택적인 words(start/end/text), 감지/지정 언어, 모델 ID·revision·정밀도·런타임 버전, chunk 오프셋·실패 상태를 담는 설계를 제안한다. 현재 문자열 반환과 달리 MLX Whisper와 Parakeet은 단어·토큰 시간 구조를 제공한다.[19][24][40] [추론] 기존 파일 포맷은 구조화 결과의 렌더링 계층으로 연결하고, 별도 정렬기를 쓰는 Qwen은 `timing_source`로 구분할 수 있다.[8]

[추론] Qwen의 별도 ForcedAligner가 최대5분 단위를 지원하므로 긴 녹음은 정렬 단위별 결과에 전역 오프셋을 더하는 경로를 검토할 수 있다.[8] Parakeet은 `AlignedResult`의 문장·토큰을 제공하고, Whisper MLX는 `word_timestamps`를 제공한다.[19][24] [추론] chunk 시작 시각과 단어 시작/끝은 구별해 저장해야 한다.

### 후속 검증 설계 — 이번 조사에서 실행하지 않음

다음 로컬 검증 설계는 사용자 제약 안의 소형 후보에만 적용한다. Nemotron30B급과 그 파생 대형 변형의 로컬 실험은 후속 과제로 배정하지 않는다.

[추론] M3 Max·36GiB 실험은 한국어 낭독/자유발화/기술 강연/한영 혼용, 영어 강연/대담, 무음·음악·저음량, 30·60·120분 입력을 구분해 설계할 수 있다. 문헌에는 CER_NS·공백 포함 CER·기술 용어 재현율처럼 서로 다른 평가 정의가 있고, 비발화 텍스트와 반복도 알려져 있다.[2][3][30][36] [추론] 같은 원문에서 이 지표와 영어 WER, RTF·지연, 최대 통합 메모리, 누락·반복·정렬 오차를 함께 기록해야 한다.

BuzzASR 변환자는 같은 셋의 FP16 대조 미실시를 밝히며, Moonshine은 float와 배포 int8 수치를 따로 비교한다.[2][31] [추론] 후속 양자화 실험은 같은 revision·오디오·정규화·언어 힌트·디코딩·VAD·정렬을 유지하고, 가중치 크기와 최대 실행 메모리를 따로 측정해야 한다. 제공자 카드나 다른 장비의 수치를 이 실험의 완료값으로 쓰지 않는다.

## 남은 질문

| 항목 | 상태·검색 범위 | 다시 확인할 주체·조건 |
| --- | --- | --- |
| M3 Max에서 후보별 실제 CER/WER·RTF·최대 메모리 | **미완·미실행**. 문헌 조사만 허용됐으며 실행 수치 없음 | 메인/사용자가 별도 설치·다운로드·실험을 승인한 후 실험 담당자가 위 조건으로 측정 |
| 한국어 4bit/8bit 손실 | [불명·미발견] 읽은 Whisper/Qwen/Buzz 모델 카드·런타임 README에서 동일 원모델 대조 미확보 | 실험 담당자, FP16와 동일 corpus·decoder를 확보한 시점 |
| Open ASR 현재 기본 설정의 영어 순위 | [불명·미발견] 버전 레지스트리는 확인, 결과 CSV는 Jina·내장 조회에서 접근 실패 | 조사 담당자, 결과 원문 접근 가능 시 2026-11-04 이전 revision을 고정하여 재검토 |
| Voxtral Realtime 한국어 15.74의 정확한 지표 | [불명·미발견] 카드의 FLEURS 표는 확인, 한국어 CER/WER 구분 미확보 | 조사 담당자, 기술 보고서의 scoring 구현을 확인할 때까지 순위화 보류 |
| 나머지 모델의 데이터셋별 한국어 수치 | [불명·미발견] 텍스트 원문 중심, 그림 전체 숫자 추출은 미완 | 조사 담당자, SenseVoice/Dolphin/Cohere 등 원 평가 코드·버전 확보 시 |
| TF/MPS 개별 모델·연산, `?` 조합 | [불명·미검색] 일반 MPS 문서와 계열 구현만 확인 | 구현 담당자, 어댑터 후보가 정해진 뒤 해당 버전의 실제 경로 실행 |
| ghost613 가중치 약정·FireRed 체크포인트별 약정·Voxtral3B 약정 전문 | [불명] 앞의 두 항목은 카드 미발견/별도 약정 미검색, 마지막은 Hub의 Apache-2.0 표기만 확인 | 도입 담당자, 재배포·서비스 사용 전에 해당 revision의 원 LICENSE를 확인 |
| 한국어 단어 시간 품질과 개인 화자 재식별 | [불명·미검색] timestamp 기능과 개인 식별의 정확도 실험을 수행하지 않음 | T2 통합/실험 담당자, 공통 결과 구조·정답 표본 확보 뒤 평가 |
| 공식 NVIDIA GGUF 카드 본문·파일 목록 | [불명·접근실패] 공식 연구 페이지의 링크는 확인, Jina/Hub API/raw/내장 open에서본문 미확보 | 조사 담당자, 공식 공개 카드 접근이 가능해지면 AtomicChat과 파일별 revision·정밀도를 대조 |
| Nemotron native MLX/NeMo-Speech.cpp의 실제 성능 | [불명·미실행] 소스 연결·문서 수치만 확인; **사용자 제약으로 로컬 채택 제외** | 로컬 후속 실험 대상으로 배정하지 않음;호스팅 관련 질문만 T3가 검토 |
| mini64e 등 pruned 변형의 resident 규모 | [불명·미실행] 텍스트 backbone 크기와 fused speech·runtime 메모리를 구별해야 함 | 로컬 우회 추천하지 않음;사용자 제약이 바뀌지 않는 한 도입 후보로 승격하지 않음 |

필수 수량의 문헌·후보 표는 충족했으나 위 표의 미완 실험과 세부 원문 검증을 완료한 것으로 보고하지 않는다. 출처별 확인 구절·조회 시점은 `/tmp/open-scribe-research-2026-11/t4/source-notes.md`, 전체 인용 감사는 같은 디렉터리의 `citation-audit.jsonl`에 보존한다. 모델명 검사용 훅의 경고는 본 보고서의 존재·가격·폐기일 근거로 사용하지 않았다.

## 출처

1~40은 초기 조사 자료이고41~72는2026-11-05 KST의추가조회다. 68번은공식링크의접근실패기록이며본문을읽은근거로세지않았다. 40번과69번의고정commit코드는로컬에서읽었다. 초기스냅샷의11-04조회일은보존하고재조회일을추가한다. 날짜없는`main`은조회당시본문이며공개일을추정하지않았다.

[1] OpenAI, [Whisper README](https://github.com/openai/whisper), `main`; 모델 규모·A100 상대 속도·MIT·long-form 안내, 문서 개정일 미확인.

[2] voyagar, [BuzzASR-korean-mlx-8bit](https://huggingface.co/voyagar/BuzzASR-korean-mlx-8bit), 변환일 2026-10-22, mlx-audio0.5.7/MLX0.32.3, 원 revision `411b68546497bd0efb87599ad7ad4d98fa3dbc62`; 직접 수행한 M3·16GB 평가.

[3] OpenAI, [whisper-large-v3-turbo](https://huggingface.co/openai/whisper-large-v3-turbo), 해당 checkpoint 카드; 층 축소·장시간·환각, 개정일 미확인.

[4] Distil-Whisper 저자, [distil-large-v3.5](https://huggingface.co/distil-whisper/distil-large-v3.5), v3.5 카드; English, 자체 OOD·상대 RTFx, cpp/faster 예제.

[5] NVIDIA, [parakeet-tdt-0.6b-v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3), 공개일 2025-08-14 표기; 25개 언어·8개셋 WER·장시간 조건.

[6] NVIDIA, [canary-1b-v2](https://huggingface.co/nvidia/canary-1b-v2), v2 카드; 유럽25개 언어·dynamic chunk·보조 시간 모델·환각 평가.

[7] NVIDIA, [canary-qwen-2.5b](https://huggingface.co/nvidia/canary-qwen-2.5b), 공개일 2025-07-17, 평가 Version2.5.0.

[8] Qwen 팀, [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR), `main`; 2026-01-29 공개/2026-06-26 Transformers 지원 공지, 0.6B·1.7B·ForcedAligner 구분.

[9] Mistral, [Voxtral-Mini-4B-Realtime-2602](https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-2602), `2602` checkpoint 카드; 지연별 한국어 평가표·라이브러리 안내. 추출기의 Published Time 메타데이터는 공개일 근거로 채택하지 않음.

[10] Mistral, [Voxtral-Mini-3B-2507](https://huggingface.co/mistralai/Voxtral-Mini-3B-2507), `2507` checkpoint 카드; 열거 언어·30분 전사·Transformers 안내. 11-04 최초 저장, 11-05 Hub 라이선스 표기 추가 확인.

[11] Kyutai, [delayed-streams-modeling](https://github.com/kyutai-labs/delayed-streams-modeling), `main`, moshi/moshi-mlx≥0.2.6 안내; 공식 MLX·언어·단어 시간·가중치 약정.

[12] IBM, [granite-4.0-1b-speech](https://huggingface.co/ibm-granite/granite-4.0-1b-speech), 공개일 2026-03-06; 6개 언어·Open ASR 표·mlx-audio 경로.

[13] Moonshine AI, [Available Models](https://github.com/moonshine-ai/moonshine/blob/main/docs/models/available-models.md), `main`; 한국어 Tiny·라이선스·언어별 streaming 구분.

[14] SenseVoice 유지관리자, [SenseVoice README](https://github.com/FunAudioLLM/SenseVoice), 조회 시 QwenAudio/SenseVoice로 연결; Small의 5개 언어·현재 timestamp·약정 설명, `main` 개정일 미확인.

[15] FireRedTeam, [FireRedASR2S](https://github.com/FireRedTeam/FireRedASR2S), 2026-02-12 시스템/2026-02-25 LLM 가중치 공지; ASR·VAD·LID 범위 구분.

[16] Dataocean AI·Tsinghua, [Dolphin README](https://github.com/DataoceanAI/Dolphin), `main`; 2026-05-09 word timestamp 공지, 모델 크기·Apache-2.0.

[17] Meta 저자, [Omnilingual ASR README](https://github.com/facebookresearch/omnilingual-asr), December2025 Update 포함; CTC/LLM/Unlimited 계열, A100·BF16 메모리·RTF.

[18] ghost613, [whisper-large-v3-turbo-korean](https://huggingface.co/ghost613/whisper-large-v3-turbo-korean), 카드 날짜 미확인; 저자 자신의 Zeroth 분할·평가.

[19] Apple MLX 예제 유지관리자, [mlx-examples/whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper), `main`; 모델 변환·4bit·word_timestamps.

[20] ggml-org, [whisper.cpp README](https://github.com/ggml-org/whisper.cpp), 조회 당시 `main`; GGML/Metal/CoreML·메모리 안내·실험적 단어 시간.

[21] SYSTRAN, [faster-whisper README](https://github.com/SYSTRAN/faster-whisper), 비교표의 faster-whisper v1.1.0/cpp v1.7.2/Transformers v4.46.3; RTX3070Ti·i7 조건 포함.

[22] Mustafa Aljadery, [lightning-whisper-mlx](https://github.com/mustafaaljadery/lightning-whisper-mlx), `main`; 열거 모델·batch12·4bit/8bit, 개정일 미확인.

[23] Neywa Labs/Blaizzy 유지관리자, [mlx-audio](https://github.com/Neywa-Labs/mlx-audio), 구 Blaizzy URL에서 이동한 조회 당시 `main`; STT 모델 표·변환·API.

[24] senstella, [parakeet-mlx](https://github.com/senstella/parakeet-mlx), `main`; Parakeet v3·chunk120/overlap15·AlignedResult, 개정일 미확인.

[25] Argmax, [Argmax OSS Swift/WhisperKit](https://github.com/argmaxinc/argmax-oss-swift), 구 WhisperKit URL에서 이동한 `main`; CoreML 변환·turbo·incremental loading·word 시간.

[26] k2-fsa 유지관리자, [sherpa-onnx CHANGELOG](https://github.com/k2-fsa/sherpa-onnx/blob/master/CHANGELOG.md), `master`; 버전1.12.34 Qwen3 0.6B, 1.12.35 Cohere 등 개별 export 기록.

[27] Hugging Face, [Transformers Apple Silicon](https://huggingface.co/docs/transformers/v5.22.1/apple_silicon), **v5.22.1** 문서; MPS·통합 메모리·연산 fallback. 제품별 ASR 호환성 실측 문서 아님.

[28] Hugging Face Audio, [Open ASR version registry init.py](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard/blob/main/init.py), `02-11-2026` 항목 및 결과 revision `887838715af6ee8d95cf54d7dcde2ae7d2651292`; 결과 CSV 본문 접근 실패는 별도 기록.

[29] Cohere Labs, [cohere-transcribe-03-2026](https://huggingface.co/CohereLabs/cohere-transcribe-03-2026), `03-2026` 모델 ID; Transformers≥5.4.0, 언어·8개셋 WER·제약·MLX 생태계 안내.

[30] 박소영·김선만, [다중 한국어 음성 코퍼스에서의 Qwen3-ASR 평가 및 추론 파라미터 분석](https://www.jask.or.kr/articles/xml/wJay/), 한국음향학회지45(5), 582–590, **2026-09-30**, doi:10.7776/ASK.2026.45.5.582; 원 실험 보고.

[31] Moonshine AI, [Accuracy](https://raw.githubusercontent.com/moonshine-ai/moonshine/main/docs/models/accuracy.md), `main`; 2026-07-30 전후 양자화 구분·영어 float/int8·한국어 WER 표.

[32] MLX Community 변환자, [Qwen3-ASR-1.7B-4bit](https://huggingface.co/mlx-community/Qwen3-ASR-1.7B-4bit), mlx-audio0.3.1 변환이라고 명시; Qwen 제공자의 원 가중치와 구별.

[33] Dataocean AI, [Dolphin languages.md](https://github.com/DataoceanAI/Dolphin/blob/main/languages.md), `main`; ko·ko-KR를 직접 확인.

[34] Meta 저자, [Omnilingual 7B LLM language results CSV](https://raw.githubusercontent.com/facebookresearch/omnilingual-asr/main/per_language_results_table_7B_llm_asr.csv), 초기7B 결과 파일; `kor_Hang,5711.6,5.8`, 데이터셋별 열 없음.

[35] Microsoft, [VibeVoice-ASR](https://huggingface.co/microsoft/VibeVoice-ASR), 카드·language_distribution_horizontal 그림; 60분·구조화 전사·Korean 학습 분포·MIT.

[36] BuzzASR 저자, [BuzzASR/korean](https://huggingface.co/BuzzASR/korean), arXiv:2609.09554 연결 카드; CV25/FLEURS·jiwer3.0.4·현재 beam5 권고.

[37] IBM, [granite-speech-5.0-2b](https://huggingface.co/ibm-granite/granite-speech-5.0-2b), 공개일 **2026-10-20**, Open ASR 그림 기준2026-10-21; mlx-audio≥0.5.9 안내.

[38] NVIDIA, [nemotron-3.5-asr-streaming-0.6b](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b), 공개일 문서 표기 **06/04/2026**; locale·지연별 CER·OpenMDW-1.1.

[39] OpenNMT, [CTranslate2 Hardware support](https://opennmt.net/CTranslate2/hardware_support.html), **4.8.5** 문서; 사전 빌드 CPU/GPU 지원 범위.

[40] open-scribe 로컬 코드, [HEAD 3880fcf config.py](https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/config.py) 및 같은 HEAD의 `src/transcribers/whisper_cpp.py`, `base.py`, `src/cli.py`, `src/utils/worker_pool.py`; 이번 세션에서 로컬 파일·기본 두 경로 존재 여부 확인. 실제 수정 없음.

[41] Hugging Face, [ASR trending 첫 페이지](https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&sort=trending), 2026-11-05 00:16 KST경 조회·30항목 스냅샷. 필터·정렬·순서를 보존하고 상대 갱신일은 공개일로 해석하지 않음.

[42] NVIDIA, [NVIDIA-Nemotron-3.5-Transcribe-30B-A4B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B), 11-05 조회; 공개2026-10-28, 결과 capture10-12, Hub revision `c17667641` 접두어. 아키텍처·언어·평가·NIM/공개 구현 차이 원문.

[43] pyannote, [speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1), 11-05 조회; revision `3533c8cf8` 접두어, CC-BY-4.0 표기; 화자 분리 pipeline.

[44] pyannote, [speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1), 11-05 조회; revision `84fd25912` 접두어, MIT 표기; pyannote.audio≥3.1 pipeline.

[45] Third Intelligence, [Haas-ja-v1.0](https://huggingface.co/third-intelligence/Haas-ja-v1.0), 11-05 조회; revision `660728d39` 접두어, 일본어·CUDA/Triton/macOS 미지원·Apache-2.0.

[46] AtomicChat, [Transcribe30B GGUF](https://huggingface.co/AtomicChat/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-GGUF), 11-05 조회; revision `dbd06c5ca` 접두어. 자체 변환·2200발화 원 실험·파일 크기·Metal 안내; NVIDIA 명의 배포와 구별.

[47] NVIDIA, [Transcribe30B NVFP4](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-NVFP4), 11-05 조회; revision `66c6adc40` 접두어, ModelOpt NVFP4·Blackwell 예제·OpenMDW-1.1.

[48] Cactus Compute, [Whistle](https://huggingface.co/Cactus-Compute/whistle), 11-05 조회; revision `741118687` 접두어, 7언어·`.cact`·CPU/Needle·Apache-2.0.

[49] NVIDIA, [nemotron-labs-unified-asr-0.6b](https://huggingface.co/nvidia/nemotron-labs-unified-asr-0.6b), 11-05 조회; revision `023ce9072` 접두어, 25개 언어·offline/streaming·OpenMDW-1.1.

[50] erayyapagci, [balbal-v2-manas](https://huggingface.co/erayyapagci/balbal-v2-manas), 11-05 조회; revision `a0a842424` 접두어, 터키어/영어·원 저자 영어 평가·balbal Community1.1와 코드Apache 분리.

[51] moondream, [parakeet-ultra](https://huggingface.co/moondream/parakeet-ultra), 11-05 조회; revision `73175eb7a` 접두어, Parakeet v3 full precision post-training·7셋 영어·25언어 FLEURS 직접 비교.

[52] akhaliq, [nemotron-3.5-transcribe-mini-64e](https://huggingface.co/akhaliq/nemotron-3.5-transcribe-mini-64e), 11-05 조회; revision `0a4798310` 접두어, REAP pruning·64e/96e·W4A16·300클립 원 평가, OpenMDW-1.1.

[53] Phsoft-ai, [Notesoop-STT-Ko-v1](https://huggingface.co/Phsoft-ai/Notesoop-STT-Ko-v1), 11-05 조회; revision `030e4720b` 접두어, 저자 M1 Pro16GB 평가·Zeroth457·강의41분43초·MPS·Apache-2.0.

[54] AI4Bharat, [indic-conformer-600m-multilingual](https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual), 11-05 조회; revision `2a77d3050` 접두어, 22개 인도 언어·MIT metadata.

[55] IBM, [granite-speech-5.0-470m-turboctc](https://huggingface.co/ibm-granite/granite-speech-5.0-470m-turboctc), 11-05 조회; revision `1dd23f46f` 접두어, 2026-10-21의7언어 업데이트, Apache-2.0·mlx-audio 안내.

[56] inclusionAI, [Ming-3.0-asr-tiny](https://huggingface.co/inclusionAI/Ming-3.0-asr-tiny), 11-05 조회; revision `ac95e7b16` 접두어, 중영·CUDA 예제·MIT·별도 Apache 소스 고지.

[57] ConwayResearch, [Underdog-Bark-3.0](https://huggingface.co/ConwayResearch/Underdog-Bark-3.0), 11-05 조회; revision `85db2ad18` 접두어, 저자7셋 영어·M2 메모리 사례·MLX/CoreML 패키지·CC-BY-4.0.

[58] ggerganov, [whisper.cpp GGML weights](https://huggingface.co/ggerganov/whisper.cpp), 11-05 조회; revision `5359861c7` 접두어, 변환 가중치 저장소·MIT metadata.

[59] IBM, [granite-speech-5.0-470m-turboctc-nc](https://huggingface.co/ibm-granite/granite-speech-5.0-470m-turboctc-nc), 11-05 조회; revision `af0a8e866` 접두어, 영어·CC-BY-NC-SA-4.0·Transformers≥5.16.0.

[60] FermionResearch, [Phonon-2](https://huggingface.co/FermionResearch/Phonon-2), 11-05 조회; revision `3e6ab3a81` 접두어, 영어·164MB·7셋WER5.21·MLX·CC-BY-4.0.

[61] LocalDoc, [speakwrite-azerbaijani](https://huggingface.co/LocalDoc/speakwrite-azerbaijani), 11-05 조회; revision `4ad010ee4` 접두어, 아제르바이잔어·CPU PyTorch/ONNX·CC-BY-NC-4.0.

[62] Oruk AI, [oruk-loop-153M](https://huggingface.co/oruk/oruk-loop-153M), 11-05 조회; revision `58b0065fe` 접두어, 영어·153M weight sharing·자체7셋 평가·test checkpoint 선택·가중치 PolyForm 조건.

[63] Quran-Lab, [zipformer_p-arabic-v3](https://huggingface.co/Quran-Lab/zipformer_p-arabic-v3), 11-05 조회; revision `5a115aa91` 접두어, 내장 웹으로 카드 본문 저장; 아랍어 꾸란 음소·NPL1.2. 파일 동의는 하지 않음.

[64] FermionResearch, [Phonon-2.5](https://huggingface.co/FermionResearch/Phonon-2.5), 11-05 조회; revision `2af4bb8cc` 접두어, 25언어·156.2MB·7셋영어WER5.06·MLX/CPU·CC-BY-4.0.

[65] NVIDIA, [Transcribe30B FP8](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-FP8), 11-05 조회; 공식 FP8 카드 원문, OpenMDW-1.1. MLX의 BF16 확장은66번 별도 구현 문서.

[66] Neywa Labs 유지관리자, [native MLX Nemotron Transcribe README·구현](https://github.com/Neywa-Labs/mlx-audio/tree/e0833581c52963ff52b9916dc6eace8ca870aae0/mlx_audio/stt/models/nemotron_transcribe), 11-05 source-only 조회; 공식 정밀도별 로드·EA heads 차이·메모리·CTC/MTP 검증 분기. 이 commit을11-04 상태로 소급하지 않음.

[67] NVIDIA Research, [Nemotron 3.5 Transcribe 연구 페이지](https://research.nvidia.com/labs/nemotron/NVIDIA-Nemotron-3.5-Transcribe/), Published2026-10-28, 11-05 Jina 원문 저장; 공식 GGUF 및 NeMo-Speech.cpp 직접 링크.

[68] NVIDIA 공식 GGUF 식별자, [NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-GGUF](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-GGUF), **11-05 접근 실패 기록**. 링크 존재 근거는67번이며 이 카드의 파일·수치를 읽었다고 간주하지 않음.

[69] NVIDIA, [NeMo-Speech.cpp 고정 commit](https://github.com/NVIDIA/NeMo-Speech.cpp/tree/536b17a41bef62d2a67a40ed3df61df26a4389fe), 11-05 source-only shallow clone; `CMakePresets.json`, `docs/salm/models.md`, `docs/build.md`, `src/speechlm/CMakeLists.txt`, `salm_engine.cpp`, `src/runtime/ggml/backend.cpp` 확인. 설치·빌드·가중치 로드 없음.

[70] OpenAI, [whisper-large-v3 HF 카드](https://huggingface.co/openai/whisper-large-v3), 11-04 최초/11-05 trending 재조회; revision `06f233fe0` 접두어, Hub metadata Apache-2.0 및 한국어 목록. 원 저장소 MIT와 차이 보존.

[71] Qwen, [Qwen3-ASR-1.7B HF 카드](https://huggingface.co/Qwen/Qwen3-ASR-1.7B), 11-04 최초/11-05 재조회; revision `7278e1e70` 접두어, 한국어 명시·Apache-2.0 Hub 표기.

[72] FermionResearch, [Phonon-2.5-English](https://huggingface.co/FermionResearch/Phonon-2.5-English), 11-05 조회; 영어 전용 별도 카드·7셋WER4.82·MLX/CPU·CC-BY-4.0.
