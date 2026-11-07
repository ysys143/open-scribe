# open-scribe 개선 조사 종합

조사 기간: **2026-11-04~05 KST**. 최초 원문과 사용량 기준선은 11월 4일, Hugging Face 트렌딩 목록·Nemotron Transcribe 등 보완 조회는 11월 5일이다. 조회 시점을 소급해 동일한 날의 상태로 합치지 않는다. 코드 기준: `3880fcfe007965711cb89a2f4778db09d2918bfd`. 이 문서는 문헌 조사와 코드 열람 결과를 종합하며 실제 모델 비교 실행 결과는 포함하지 않는다.

사용자 제약: **30B 모델의 로컬 실행은 추천에서 제외한다.** Nemotron 30B의 공개 구현·양자화·MLX 지원은 조사 기록으로 남기며 채택 후보는 호스팅 경로다. 로컬 추천은 전체 가중치·실제 메모리 부담을 고려한 소형 ASR 중심이다.

## 요약

[추론] 화자 분리와 정밀한 자막을 도입하려면 전사 결과를 문자열로 만드는 시점을 출력 단계로 옮기고, 세그먼트·단어·화자 정보를 먼저 보존하는 구조가 필요하다. 현재 인터페이스는 문자열을 반환하며, GPT-4o 전사 청크의 시간 표시와 SRT의 추정 종료 시각은 실제 단어 정렬 결과와 다르다.[1][2][3]

[추론] 요약 모델의 공급자·옵션 분리는 이 결과 구조 개편과 병렬로 진행할 수 있다. 다만 현행 캐시는 모델 버전이나 프롬프트를 키에 포함하지 않으므로, 비교 가능한 모델 교체에는 단계별 설정 식별자와 결과 메타데이터가 함께 필요하다.[4][5]

OpenAI 공식 종료 일정은 코드 기본 후처리 모델 `gpt-5-mini`의 종료 예정일을 **2026-12-11**, 기존 Whisper·GPT-4o 전사 계열을 **2027-02-26**으로 명시한다. 이는 11월 5일 보완 조회로 확인한 일정이며 실제 계정의 접근성을 시험한 결과는 아니다. [추론] 따라서 후처리 호출부의 모델 교체 준비를 우선 작업에 포함해야 한다.[20]

[추론] 호스팅 요약 비교군은 **Luna·Haiku 5.5·DeepSeek Flash**, 로컬 한국어 ASR 비교군은 **Whisper turbo·Qwen3-ASR-0.6B/1.7B**, 영어 경량 비교군은 **Phonon-2.5-English·Parakeet v3**로 정리한다. 화자 기능은 **Community-1 + 독립 임베딩 registry**를 로컬 기준선으로 삼고 ONNX·호스팅 대안을 함께 비교하는 안이다. 아래 권고는 문헌과 통합 조건에 따른 비교 순서이며 동일 조건 성능 우승자가 아니다.[12][13][14][15][16][17][19][21][36]

[추론] **Nemotron 3.5 Transcribe 30B-A4B는 호스팅 ASR 비교군**으로 추가한다. 기존에 검토한 `nemotron-3.5-asr-streaming-0.6b`와 별도 모델이다. 원모델은 한국어를 포함한 40개 언어와 최대 1시간, 요청 시 화자별 단어 시간을 지원한다. OpenRouter 호스팅의 응답 계약은 공개 모델의 실행 경로와 구별해야 한다. 모델이 제공하는 익명 화자 번호와 영구 인물 재식별은 여전히 별개다.[28][29][30][31]

보완 조사에서는 HF ASR 트렌딩 첫 페이지 **30카드의 목적·언어·원모델/변형을 전수 선별**했다. 전체 모델 표는 **44개 체크포인트·배포 변형 행**이며, 이를 44개 독립 모델 계열로 세지는 않는다. 첫 페이지 밖의 모든 HF 모델을 검토했다는 의미도 아니다.[32] 공식 NVFP4를 읽는 native MLX 구현도 확인했지만, 해당 30B급 모델은 사용자 제약에 따라 로컬 추천에서 제외했다.[35]

상세 보고서: [유사 프로젝트](01-similar-projects.md), [화자 분리·재식별](02-speaker-diarization.md), [호스팅 모델·비용](03-hosted-models.md), [공개 ASR·양자화·MLX](04-open-asr-mlx.md). 수량과 검증 결과는 [검증 기록](verification.md)에 따로 남긴다.

## 확인한 현재 상태

| 항목 | 코드에서 확인한 상태 | 개선 검토에 주는 의미 |
|---|---|---|
| 전사 기본값 | `gpt-4o-mini-transcribe`; 상위 별칭은 `gpt-4o-transcribe`.[6] | 실제 실행 설정과 코드 기본값을 구분한다. 이번 조사에서 비밀 설정 파일은 열지 않았다. |
| 요약·교정·번역 기본값 | 모두 `gpt-5-mini`; 키워드는 `gpt-4o-mini`로 고정.[6][7] | [추론] 모델 정책은 요약만 바꾸어서는 통일되지 않는다. |
| 요약 호출 | OpenAI Chat Completions에 고정. 모델 접두어에 따라 일부 파라미터만 분기. 추론 강도는 지정하지 않음.[5] | [추론] 새 모델의 이름만 바꾸는 방식으로 호환성을 보장할 수 없다. |
| 전사 결과 | `Optional[str]`; 단어·화자 공통 객체 없음.[1] | [추론] 정렬·화자 결합 전에 원본 응답과 정규화 결과를 저장해야 한다. |
| 청크 완전성 | 실패한 결과를 필터링한 뒤 성공한 문자열만 병합.[2] | [추론] 누락 청크를 별도로 기록하고 전체 완료와 부분 완료를 구분해야 한다. |
| 캐시·재개 | `video_id + engine` 중심. 요약 모델·프롬프트와 무관한 완료 플래그.[4] | [추론] 단계마다 입력·설정·모델 버전의 fingerprint가 필요하다. |
| 로컬 입력 정리 | 로컬 파일은 `args.audio=False`가 되고 마지막 정리에서 해당 경로를 `unlink()`할 수 있음. 이 경로는 열람만 했다.[4] | [추론] 화자 등록용 샘플 보존은 입력 소유권과 명시적 보존 정책을 먼저 정해야 한다. |
| 클라우드 | Cloud Run 메모리 1Gi, worker의 DB·작업 경로는 `/tmp`, 전사 factory는 CLI와 별도.[8] | [추론] 로컬 MLX와 지속적인 화자 저장소를 현재 컨테이너에 그대로 넣는 설계는 별도 검토가 필요하다. |

이번 세션에서 SQLite를 읽기 전용으로 재집계한 결과 작업 73건, 그중 mini 전사 65건·상위 전사 8건이었다. 2026년 9월 20건, 10월 21건이었다. DB에 기록된 중복 없는 경로 중 실제 존재하는 전사문 64개의 길이는 최소 1,564자, 중앙값 16,679자, p90 96,884자, 최대 212,142자였다. p90은 nearest-rank, 길이는 Python `len(text)`이다. 집계와 파일 해시는 [baseline.json](../baseline.json)에 보존했다. 이 집계는 신규 모델의 품질 측정이 아니다.

## open-scribe 적용 검토

### 구조 반입의 선행 조건

[추론] WhisperX의 `TranscriptionResult`·정렬 결과 구조, Scriberr의 전사·화자 어댑터 분리, Speaches의 모델 참조 수·TTL 관리는 각각 데이터 계약, 기능 선택, 로컬 메모리 관리에 참고할 수 있다. 언어와 배포 구조가 다르므로 구조를 참고한 자체 구현과 원본 코드를 복사하는 작업은 구분해야 한다.[9][10][11]

| 우선순위 | 작업 | 대상 | 완료를 판단할 경로 | 선행 조건 |
|---|---|---|---|---|
| P0 | 입력 소유권·원본 보존 정책 | `src/cli.py`, 향후 등록 CLI | 사용자 원본·임시 변환물·등록 샘플의 정리 정책이 각각 적용됨 | [추론] 화자 샘플 저장 전 필요.[4] |
| P0 | 정규화 전사 결과와 기존 텍스트 출력 호환 | `src/transcribers/base.py`, 각 엔진, 출력기 | 세그먼트·단어·화자·정렬 출처가 JSON에 남고 기존 텍스트 출력도 유지됨 | [추론] 화자·자막 정밀화의 공통 기반.[1][2][3][9] |
| P0 | 청크 manifest·실패 상태·단계별 캐시 | `src/database.py`, `src/utils/audio.py`, `src/cli.py` | 중간 청크 실패가 전체 완료로 기록되지 않고 설정 변경 시 해당 단계만 재실행됨 | [추론] 엔진 교체 및 장문 재개와 함께 적용.[2][4] |
| P0 | 공급자·모델 capability와 후처리 호출 분리 | `src/config.py`, `src/utils/summary.py`, 번역·교정·키워드 모듈 | 공급자별 정확한 파라미터와 토큰 한도가 적용되고 모델·추론 옵션이 기록됨 | [추론] 결과 구조 개편과 병렬 가능; 캐시 키 변경과 기존 모델 종료 일정 반영.[5][6][7][20] |
| P1 | 엔진 registry와 환경별 가용성 | CLI·bot의 전사 factory | 같은 엔진 ID의 언어·정렬·화자·메모리 요구가 두 진입점에서 일관되게 판정됨 | [추론] 로컬 GPU와 Cloud Run 실행 환경 구분.[8][10] |
| P1 | 공통 결과 기반 writer | `src/utils/srt_converter.py`, `src/utils/file.py`, `src/cli.py` | TXT·JSON·SRT·VTT가 같은 결과를 소비하며 추정 시간과 정렬 시간이 구별됨 | [추론] 정규화 결과 계약과 호출부 이행에 연결.[1][3][9] |
| P1 | whisper.cpp 복구 기준선과 MLX 어댑터 비교 | `src/transcribers/whisper_cpp.py`, 신규 MLX 어댑터 | 선택한 실행 파일·모델 버전으로 언어·장문·실패 경로 확인 | [추론] 구조화 결과·환경 registry와 모델별 라이선스 확인 필요.[15][16][21] |
| P1 | 화자 분리·단어 결합 및 통합 모델 응답 매핑 | 신규 diarization 모듈, 결과 결합기, 통합 ASR 어댑터 | 원본 시간축·겹침을 보존하고 단어별 모호성을 표시 | [추론] 별도 단계 조합과 Nemotron 통합 응답을 같은 공통 결과로 연결; 청크 완전성 필요.[1][2][17][29] |
| P1 | 검증한 모델 파일만 반영하는 준비 단계 | `src/config.py`, 모델 artifact helper | 임시 파일의 크기·해시·취소 상태와 최종 반영이 구별됨 | [추론] T1의 Vibe·Buzz·Handy 사례에 따른 별도 반입 후보; 실제 파일 반입 전 고지·라이선스 확인.[24] |
| P2 | 목소리 등록·재식별 | 영구 SQLite registry, 등록·확인 CLI | 미등록자·모호한 후보를 미상으로 남기고 확인된 등록 버전만 갱신됨 | [추론] 단독 음성 품질 필터·동의·보존·모델/보정 버전이 선행.[17][18][19] |
| P2 | 로컬 모델 수명 관리 | 향후 로컬 ASR·화자 엔진 | 사용 중 모델이 해제되지 않고 유휴 시 메모리가 회수됨 | [추론] 실제 통합 후 측정한 메모리 사용량을 바탕으로 TTL 결정.[11] |

이 표의 순위와 완료 경로는 조사에 따른 설계 제안이며 제품 구현·실험 결과가 아니다. T1은 비교 10개·심층 사례 5개에서 반입 후보 8개를 도출했다. 그중 작업량은 helper 수준 S, 여러 모듈 계약 변경 M, DB·실행 흐름 이행 L로 구분했으며 공통 결과·청크 저장·캐시 fingerprint는 L, writer·capability·파일 준비·runtime 관리는 M으로 추정했다. 구현 기간과 회귀 비용을 측정한 수치는 아니다. 근거 파일과 위험은 [T1 반입 후보 표](01-similar-projects.md)에 있다.

### 호스팅 모델의 실제 호출 이름과 선택 조건

가격은 조회 당시의 표준 USD/100만 토큰이며 캐시 쓰기·추론 토큰·장문 할증을 제외한 기본 구간이다. 이 표는 `max` 사용 실청구액이 아니다.[12][13][14]

| 비교군 | 실제 API ID | 기본 입력 / 출력 단가 | 문맥·출력과 `max` | open-scribe 적용 판단 |
|---|---|---:|---|---|
| GPT-6 Luna | `gpt-6-luna` | $0.10 / $0.50 | 총 1.05M, 입력 최대 922K·출력 128K; Chat은 `reasoning_effort`, Responses는 `reasoning.effort` | [추론] 현재 OpenAI 호출부와 가까워 첫 연결 후보. 기본 medium 추론에서 sampling 필드 호환성을 확인해야 함.[12] |
| Claude Haiku 5.5 | `claude-haiku-5-5` | 입력 ≤100K: $0.10 / $0.50; 초과: $0.50 / $2.50 | 1M·표준 출력 128K; `output_config.effort="max"` | [추론] 한국어 후처리 비교군. Messages 응답·thinking 블록과 공급자 어댑터 필요. 장문 할증 반영.[13] |
| DeepSeek V4.1 Flash 1017 | `deepseek-flash` | 비혼잡 $0.15 / $0.60, 혼잡 $0.30 / $1.20 | 1M·출력 384K; 생각 활성화와 `reasoning_effort="max"`를 별도 지정 | [추론] 긴 교정·번역 출력 비교군. 발표 버전명을 호출 ID로 사용하지 말고 시간대·캐시·usage를 기록.[14] |

[추론] 21만 자 입력을 1M 문맥에 넣을 수 있다는 것과 같은 길이의 번역을 한 번에 출력할 수 있다는 것은 다른 조건이다. T3의 계획용 문자당 0.25~1.5토큰 가정에서 최대 표본은 약 53K~318K 토큰이다. 이는 검증된 한국어 환산율이 아니다. 입력에 더해 원문과 비슷한 길이의 교정·번역, 사고 토큰을 고려하면 128K 출력 제한 때문에 분할이 필요할 수 있다.[12][13][14]

[추론] 요약 모델을 Luna로 바꾸더라도 현재 `gpt-5` 접두어 밖의 분기가 전달하는 `temperature=0.3`, `max_tokens=1000`을 그대로 두면 적합한 호출이라고 보장할 수 없다. 교정·번역의 4,000토큰 출력 예산도 별도 변경 대상이다. 공급자별 capability·토큰 예산·잘림 상태를 공통 계층에서 처리하고 비교에 사용한 effort를 기록해야 한다.[5][12][13][14]

T3의 **월 20건, 각 60분** 가정에서 GPT-Transcribe 기본 전사료는 **$5.40**, Scribe v2는 **$4.40**이다. 이는 오디오 실제 길이를 재지 않은 시나리오이며 화자·키워드·추가 옵션, 재시도, 세금 등을 제외한다. [추론] 현재 작업량에서는 분당 단가 외에 단어 시간·한국어 오류·실패 복구가 교체 판단에 영향을 준다. 후처리·장문 비용과 나머지 공급자는 [T3 비용 표](03-hosted-models.md)에 있다.[23]

### Nemotron 3.5 Transcribe의 호스팅·로컬 경로

NVIDIA 연구 발표일은 2026-10-28이고 OpenRouter의 경로 출시 표시는 10월 29일이다. 원모델은 오디오 encoder를 포함해 총 34B·활성 약 4.3B, Mamba–Transformer MoE 구조와 65,536토큰 문맥을 명시한다. BF16·FP8·NVFP4·공식 GGUF를 구분하며, NVIDIA GPU 호환표의 NVFP4 경로는 Blackwell용이다. 별도 native MLX 구현은 이 NVFP4 형식을 읽는 자체 경로를 제공한다. **활성 파라미터 4.3B를 전체 가중치 메모리로 해석할 수는 없다.**[29][31][35]

| 경로 | 확인한 계약 | 도입 판단 |
|---|---|---|
| OpenRouter `nvidia/nemotron-3.5-transcribe` | 조회 시 DeepInfra 한 공급자. JSON `input_audio`에 base64를 담는 예시와 일반 multipart 경로. 오디오 초당 $0.000033 | [추론] 시간당 **$0.1188**, 월 20시간 **$2.376**의 기본 요금 비교군. 충전 수수료 등 별도. 현재의 `response_format="text"`는 공통 가이드상 400 오류이므로 base URL만 교체하는 이행은 불가.[2][28][34][38] |
| NVIDIA BF16/FP8·vLLM 등 | 원모델의 CTC 정렬·화자 encoder와 선택적 시간 응답. H100 80GB 예시와 GPU별 precision 표 | [추론] 서버 추론용 비교. 원모델의 단어·화자 출력 계약이 호스팅 제공자의 응답에도 노출되는지는 별도 확인.[29] |
| Native MLX·공식 NVFP4 | mlx-audio 고정 소스가 공식 BF16/FP8/NVFP4 로드를 명시. NVFP4 파라미터 약 24.4GB, FP8은 로드 때 BF16으로 확장 | 사용자 제약으로 **로컬 채택 제외**. 지원 여부의 문헌 기록이다. EA 4bit export는 CTC/MTP heads가 빠져 같은 기능으로 대체할 수 없음.[35] |
| 공식 GGUF 식별자·NeMo-Speech.cpp | NVIDIA 공식 native runtime이 SALM·단어 시간·화자 label을 열거하고 Metal 빌드 경로도 안내. 공식 GGUF 링크는 연구 발표에서 확인, 카드 본문·파일 목록은 접근 실패 | 사용자 제약으로 **30B 로컬 채택 제외**. AtomicChat GGUF는 별도 배포이며 decoder+encoder가 필요. 소형 Nemotron·Parakeet의 runtime 지원은 별도 검토.[30][31][37] |

[추론] 이 모델은 기존의 ASR→별도 정렬→별도 화자 결합 외에, 통합 모델이 내놓는 단어·화자 결과를 직접 정규화하는 경로를 추가한다. 원문 전사·written form·문맥 힌트·화자 표시 같은 작업 스타일도 실행 설정과 캐시 키에 포함해야 한다. transcript의 화자 tag를 영구 이름으로 쓰거나 공개 모델의 기능을 OpenRouter에서도 무조건 제공한다고 가정하지 않는다.[4][28][29]

OpenRouter 공통 STT 가이드는 multipart 25MB, upstream 처리 timeout 60초, 공급자별 structured output 차이를 명시한다. [추론] 모델의 최대 1시간이라는 설명과 게이트웨이의 파일·처리 한도는 분리해 청크 설계를 검토해야 한다. 또 native MLX는 전체 음성을 먼저 encode한 뒤 텍스트 decode를 stream하므로 실시간 오디오 입력 전사와 다르다.[34][35]

NVIDIA가 공개한 영어 9개 공개셋 평균 WER 4.71%와 다국어 7개 언어 평균 4.62%는 그 발표의 평가 결과다. [추론] T4의 이전 8개셋 모델 카드 평균이나 새 기본 리더보드 전체 순위와 바로 합칠 수 없고, 한국어 강연의 오류율이나 M3 Max 성능을 대신하지도 않는다.[31]

### 화자를 기억하고 같은 사람인지 확인하는 구조

[추론] 녹음마다 생성되는 `local_speaker_id`는 영구 `person_id`와 분리한다. 분리기는 “언제 누가 말했는가”라는 익명 구간을 만들고, 별도 임베딩 모델이 단독 음성의 벡터를 만든다. 같은 모델·가중치·전처리로 등록한 벡터만 비교한다. cosine 점수는 동일인 확률이나 이름의 진위 증명이 아니다.[17][18][19]

[추론] 저장 단위는 인물, 등록 동의, 원본 음성의 최소 구간, 녹음 세션, exemplar 임베딩, centroid 버전, 모델 버전, 보정 버전, 후보 점수와 사람 확인 이력이다. 여러 녹음·마이크의 확인된 클립을 사용하고, 겹침·잡음·짧은 발화를 품질 필터로 걸러낸다. 자기소개·영상 제목·발표자 명단은 독립된 문맥 단서로 보존한다. 이들을 음성 일치 증거와 합쳐 두 번 센 것으로 처리하지 않는다.[17][18][19]

[추론] 조회는 centroid 후보 검색 후 exemplar 재평가를 하고, 절대 점수·1·2위 차이·유효 길이·여러 구간의 일관성 중 조건을 만족하지 못하면 `unknown/needs_review`로 둔다. 사람이 확인한 뒤에만 인물 연결과 등록 벡터를 갱신한다. 임계값은 등록·평가 녹음을 분리하고 미등록자를 포함한 FAR/FRR·open-set 오류를 측정해 정한다. 보편적인 cosine 임계값은 확정하지 않는다.[18][19]

[추론] 로컬 기준선은 Community-1의 일반 구간과 exclusive 구간을 함께 보존하는 안이다. exclusive는 읽기용 단일 화자 배정에 사용하고 일반 구간은 겹침 평가와 등록 클립 필터에 남긴다. macOS arm64 경로를 중시하면 sherpa-onnx 대안을, 원격 처리라면 pyannoteAI·Speechmatics의 opaque voiceprint를 검토한다. 원격 식별자를 로컬 float 벡터처럼 평균하거나 공급자 사이에서 이전할 수 있다고 가정하지 않는다. 대안별 라이선스·속도·보존 제약과 SQLite 초안은 [T2](02-speaker-diarization.md)에 있다.[17][18][27]

### 로컬 ASR·양자화의 비교 순서

| 용도 | 우선 비교 경로 | 판단 근거와 남은 검증 |
|---|---|---|
| 기존 로컬 경로 복구·한영 기준선 | Whisper turbo / large-v3 + whisper.cpp Metal | [추론] 기존 어댑터 연결을 활용한 기준선. 경로 복구와 정확도 개선은 다른 결과. CoreML encoder·MLX는 서로 다른 실행 경로.[21] |
| 한국어 강연·정렬·한영 용어 | Qwen3-ASR-0.6B/1.7B + mlx-audio, 8bit 비교 후 4bit 검토; BuzzASR ko 대조 | [추론] 한국어 명시 지원, 별도 한국어 ForcedAligner. community 변환·체크포인트·양자화 버전과 같은 조건의 품질을 확인해야 함.[15] |
| 영어 경량·시간 정보 | Phonon-2.5-English/Phonon-2와 Parakeet-TDT-0.6B-v3 대조 | [추론] MLX/CPU 경량 변형과 Parakeet 기준선의 정확도·정렬·처리량 비교. **한국어용 추천이 아님**. “25개 언어”를 한영 겸용으로 해석하지 않음.[16][36] |

[불명: 문헌에서 동일 조건 대조 미발견] 한국어 Whisper/Qwen의 FP16 대비 4bit·8bit 손실과 M3 Max 36GiB에서의 장문 RTF·최대 메모리는 확정하지 못했다. 외부 M3 16GB 결과는 해당 저자의 측정 조건으로 보존했고 사용자 장비 값으로 환산하지 않았다.[25] 44개 체크포인트·변형 행, 요청한 9종 런타임의 교차표, 추가 native MLX/NeMo-Speech.cpp 경로, 비상업 가중치와 한국어 미지원 후보는 [T4](04-open-asr-mlx.md)에 있다.

### 보고서 사이의 차이와 충돌

| 쟁점 | 보존한 차이 | 통합 판단 |
|---|---|---|
| OpenAI 화자 기능과 새 전사 API | T2의 known reference 계약은 폐기 예정 `gpt-4o-transcribe-diarize`의 문서. T3 새 전사 경로는 단어 시간 지원 미확정 | [추론] 새 모델 이름으로 바꿨다는 이유만으로 기존 정렬·화자 등록 계약의 호환을 인정하지 않음.[20][23] |
| 호스팅 Voxtral 3와 공개 Voxtral Realtime | T3 호스팅 3 이행 자료는 word 요청 제거, T4 공개 4B Realtime은 별도 체크포인트 | [추론] 브랜드가 같아도 한 경로의 시간·언어 계약을 다른 경로에 적용하지 않음.[39] |
| Speechmatics 요금 | 11-04 계산기 $0.24와 11-05 추출 화면 $0.12가 달랐음 | T3가 공개 HTML 요율·할인 스위치를 대조해 무할인 파일 $0.24와 할인 표시 $0.12를 구분. [추론] 화면의 “from” 요금을 무조건 기본 PAYG로 계산하지 않음.[33] |
| 한국어 CER·WER·양자화 | T4 Moonshine 한국어 6.46은 WER, Qwen·Buzz CER는 표본·공백 정규화가 다름 | [추론] 지표 이름과 평가 프로토콜이 같을 때만 직접 비교. MLX 실행 경로가 있다는 사실을 한국어 정확도·양자화 손실 보증으로 취급하지 않음.[22][26] |

이 차이들은 결론을 하나로 맞추기 위해 삭제하지 않았다. 데이터 계약·평가 조건이 다른 사례는 각 상세 보고서의 구체 원문과 미확정 항목을 함께 읽어야 한다.

### 후속 실험에서 구분할 지표

[추론] 기존 전사문에는 정답 전사와 정답 화자 구간이 없으므로, 현재 사용 기록으로 신규 후보의 CER·WER·DER를 계산할 수 없다. 후속 비교는 언어·대담·겹친 발화·녹음 길이를 구분한 음성과 사람이 만든 정답을 사용해야 한다. 로컬 실험 대상은 사용자 제약에 맞는 소형 모델로 한정한다. 이번 조사에서는 해당 정답 작성이나 모델 실행을 수행하지 않았다.

| 비교 항목 | 같은 조건으로 고정할 것 | 함께 보고할 결과 |
|---|---|---|
| ASR·양자화 | 같은 checkpoint, 음성, 디코딩 옵션, 장비 | CER/WER, 숫자·고유명사 오류, 전체 작업 RTF, 최대 메모리, 양자화 전후 차이 |
| 화자 분리 | 동일 collar, overlap 포함 정책, 화자 수 제공 여부 | DER/JER, 겹친 발화, 화자 수 오차, 단어별 귀속 오류 |
| 인물 재식별 | 등록·평가 세션 분리, 미등록자 포함, gallery 크기 | FAR/FRR, 미상 비율, 잘못 수락한 인물 수, 정정 후 변화 |
| 요약·교정·번역 | 같은 원문, 프롬프트, 모델 버전, 추론 옵션 | 원문 근거, 누락, 숫자·이름·부정 보존, 시간 링크, 실제 사용량·비용 |

위 표는 이번 문헌 조사에 이어 수행할 비교의 설계 항목이다. 수치 기준이나 표본 수가 승인·검증된 평가 프로토콜이라는 의미는 아니다.

## 남은 질문

- [불명: 이번 범위에서 실험하지 않음] M3 Max 36GiB에서 후보별 장문 RTF·최대 메모리·한국어 양자화 손실.
- [불명: 이번 범위에서 측정하지 않음] 실제 음성 길이와 공급자별 reasoning 사용량에 따른 월 청구액. 비용 표는 명시적 시나리오로 해석해야 한다.
- [불명: 정책 미정] 화자 등록 대상·이름 확인 주체·보존 기간·클라우드 업로드 허용 범위.

## 출처

[1] open-scribe BaseTranscriber, 로컬 HEAD 열람, 2026-11-04. https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/transcribers/base.py

[2] open-scribe OpenAI 전사·청크 병합, 로컬 HEAD 열람, 2026-11-04. https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/transcribers/openai.py

[3] open-scribe SRTConverter, 로컬 HEAD 열람, 2026-11-04. https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/utils/srt_converter.py

[4] open-scribe CLI·SQLite, 로컬 HEAD 열람, 2026-11-04. https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/cli.py ; https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/database.py

[5] open-scribe 요약·교정·번역 호출, 로컬 HEAD 열람, 2026-11-04. https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/utils/summary.py ; https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/utils/subtitle_corrector.py ; https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/utils/translator.py

[6] open-scribe Config 기본값, 로컬 HEAD 열람, 2026-11-04. https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/config.py

[7] open-scribe 키워드 모델, 로컬 HEAD 열람, 2026-11-04. https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/src/utils/keywords.py

[8] open-scribe Cloud Run worker·배포 설정, 로컬 HEAD 열람, 2026-11-04. https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/bot/transcribe_worker.py ; https://github.com/ysys143/open-scribe/blob/3880fcfe007965711cb89a2f4778db09d2918bfd/deploy.sh

[9] WhisperX schema, 5d3678b8535698a2826a5db9eb3e4105aef85dd9, 조사 clone 원문·메모 대조, 2026-11-04. https://github.com/m-bain/whisperX/blob/5d3678b8535698a2826a5db9eb3e4105aef85dd9/whisperx/schema.py

[10] Scriberr interfaces, a353078fd96b8aca4002681813524b7397c90df1, 조사 clone 원문·메모 대조, 2026-11-04. https://github.com/rishikanthc/Scriberr/blob/a353078fd96b8aca4002681813524b7397c90df1/internal/transcription/interfaces/interfaces.go

[11] Speaches BaseModelManager, 993994f7984bf3fe9655b267448328cf66fccb42, 조사 clone 원문·메모 대조, 2026-11-04. https://github.com/speaches-ai/speaches/blob/993994f7984bf3fe9655b267448328cf66fccb42/src/speaches/executors/shared/base_model_manager.py

[12] OpenAI 공식 GPT-6 Luna 모델·호환 매개변수 원문, T3 원문과 대조, 2026-11-04 조회. https://developers.openai.com/api/docs/models/gpt-6-luna ; https://developers.openai.com/api/docs/guides/latest-model

[13] Anthropic 공식 Haiku 5.5 overview·Effort, T3 원문과 대조, 2026-11-04 조회. https://platform.claude.com/docs/en/models/haiku-5-5/overview ; https://platform.claude.com/docs/en/build-with-claude/effort

[14] DeepSeek 공식 Models & Pricing·Thinking Mode, T3 원문과 대조, 2026-11-04 조회. https://api-docs.deepseek.com/quick_start/pricing/ ; https://api-docs.deepseek.com/guides/thinking_mode/

[15] Qwen3-ASR 공식 README·MLX 어댑터, T4 근거와 대조, 2026-11-04~05 조회. https://github.com/QwenLM/Qwen3-ASR ; https://github.com/Neywa-Labs/mlx-audio

[16] NVIDIA Parakeet-TDT-0.6B-v3 카드·parakeet-mlx 유지관리자, T4 근거와 대조, 2026-11-04~05 조회. https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3 ; https://github.com/senstella/parakeet-mlx

[17] pyannote Community-1 카드·pyannoteAI Identification, T2 근거와 대조, 2026-11-04 조회. https://huggingface.co/pyannote/speaker-diarization-community-1 ; https://www.pyannote.ai/speaker-identification

[18] Speechmatics Speaker Identification, T2 근거와 대조, 2026-11-04 조회. https://beta-docs.speechmatics.com/speech-to-text/features/speaker-identification

[19] SpeechBrain ECAPA 카드·VoxWatch 논문, T2 근거와 대조, 2026-11-04 조회. https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb ; https://arxiv.org/html/2307.00169v1

[20] OpenAI 공식 Deprecations, T2·T3 원문과 대조. T2 2026-11-04, T3 2026-11-05 보완 조회. https://developers.openai.com/api/docs/deprecations

[21] whisper.cpp 공식 README, T4 근거와 대조, 2026-11-04~05 조회. https://github.com/ggml-org/whisper.cpp

[22] Moonshine 공식 Accuracy, T4 근거와 대조, 2026-11-04~05 조회. https://raw.githubusercontent.com/moonshine-ai/moonshine/main/docs/models/accuracy.md

[23] OpenAI 공식 전사 가이드·가격, ElevenLabs 공식 API 가격, T3 근거와 대조, 2026-11-04 조회. https://developers.openai.com/api/docs/guides/speech-to-text ; https://developers.openai.com/api/docs/pricing ; https://elevenlabs.io/pricing/api

[24] Vibe download 검증·Buzz downloader·Handy 다운로드 시험 코드, T1 고정 clone·원문 메모 대조, 2026-11-04 조회. https://github.com/thewh1teagle/vibe/blob/da8c2ca53b6c7ff44f7a1314c3be862d466c3427/desktop/src-tauri/src/cmd/download.rs ; https://github.com/chidiwilliams/buzz/blob/de7484bea317ebb17dcb27da3a6e4109f9bb33e7/buzz/model_loader.py ; https://github.com/cjpais/Handy/blob/82dfab9fda18c4bc24e1f6e56d36474d38eca0bc/src-tauri/src/managers/model/download/tests.rs

[25] voyagar BuzzASR 한국어 MLX 8bit 변환 카드, 원 실험 저자의 M3 16GB 결과·한계, T4 원문 대조, 2026-11-04~05 조회. https://huggingface.co/voyagar/BuzzASR-korean-mlx-8bit

[26] 박소영·김선만 Qwen3-ASR 한국어 평가 논문(2026-09-30)·BuzzASR 원모델 카드, T4 원문 대조, 2026-11-04~05 조회. https://www.jask.or.kr/articles/xml/wJay/ ; https://huggingface.co/BuzzASR/korean

[27] sherpa-onnx 공식 저장소·화자 분리 모델 문서, T2 근거와 대조, 2026-11-04 조회. https://github.com/k2-fsa/sherpa-onnx ; https://k2-fsa.github.io/sherpa/onnx/speaker-diarization/models.html

[28] OpenRouter Nemotron 3.5 Transcribe 경로 원문, 메인이 Jina 본문을 직접 읽음, 2026-11-05 조회. https://openrouter.ai/nvidia/nemotron-3.5-transcribe

[29] NVIDIA Nemotron 3.5 Transcribe 30B-A4B 모델 카드, 메인의 Jina 본문·T4 보존 원문 대조, 2026-11-05 조회. https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B

[30] NVIDIA NeMo-Speech.cpp README, T4 보존 원문을 메인도 읽음, 2026-11-05 조회. https://github.com/NVIDIA/NeMo-Speech.cpp

[31] NVIDIA 연구 발표, 발행일 2026-10-28, 메인이 직접 열람, 2026-11-05 조회. https://research.nvidia.com/labs/nemotron/NVIDIA-Nemotron-3.5-Transcribe/

[32] Hugging Face ASR trending 첫 페이지, 2026-11-05 00:16 KST 전후 원문·30카드 스냅샷과 T4 선별표 대조. https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&sort=trending

[33] Speechmatics 공개 Pricing·HTML의 baseHourly/할인 설정, T3 원문·감사 메모 대조, 2026-11-05 조회. https://www.speechmatics.com/pricing

[34] OpenRouter Speech-to-Text 공식 가이드, T3 보존 원문을 메인도 열람, 2026-11-05 조회. https://openrouter.ai/docs/guides/overview/multimodal/stt

[35] mlx-audio native Nemotron Transcribe README·구현, commit e0833581c52963ff52b9916dc6eace8ca870aae0. T4 보존 소스의 README를 메인도 열람, 2026-11-05. https://github.com/Neywa-Labs/mlx-audio/tree/e0833581c52963ff52b9916dc6eace8ca870aae0/mlx_audio/stt/models/nemotron_transcribe

[36] FermionResearch Phonon-2·2.5-English 모델 카드, T4 확인 원문·범위 대조, 2026-11-05 조회. https://huggingface.co/FermionResearch/Phonon-2 ; https://huggingface.co/FermionResearch/Phonon-2.5-English

[37] AtomicChat Transcribe GGUF 카드, T4의 배포·조건 대조, 2026-11-05 조회. https://huggingface.co/AtomicChat/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-GGUF

[38] OpenRouter Pricing, T3 PAYG 비용·수수료 검증 원문 대조, 2026-11-05 조회. https://openrouter.ai/pricing

[39] Mistral Voxtral 3 이행 문서·공개 Realtime 모델 카드, T3·T4 원문 대조, 2026-11-04~05 조회. https://docs.mistral.ai/studio/audio/migrate-from-voxtral-2 ; https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-2602
