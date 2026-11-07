# 공급자 API 키 우선 호출 — 2026-11-05

지원 모델에 해당 공급자 키가 실행 환경에 있으면 native API를 먼저 선택하고, 없으면 같은 모델 ID로 OpenRouter를 사용한다. 기본 ASR 모델은 교체하지 않았고 로컬 보조 단계도 비활성화 상태를 유지했다.

| 공통 모델 ID | 직접 API의 모델 ID | 우선 인증 환경 변수 |
|---|---|---|
| `openai/gpt-6-luna` | `gpt-6-luna` | `OPENAI_API_KEY` |
| `anthropic/claude-haiku-5.5` | `claude-haiku-5-5` | `ANTHROPIC_API_KEY` |
| `openai/gpt-transcribe` | `gpt-transcribe` | `OPENAI_API_KEY` |
| 그 밖의 지원 모델 | 같은 OpenRouter 모델 ID | `OPENROUTER_API_KEY` |

native API에 동일 모델이 없는 `openai/whisper-large-v3-turbo`는 OpenRouter를 유지한다. 읽기 전용 OpenAI 모델 조회에서 `gpt-6-luna`·`whisper-1`은 HTTP 200, `whisper-large-v3-turbo`는 404였다. Whisper Turbo를 `whisper-1`이나 다른 모델로 자동 치환하지 않는다. `gpt-transcribe`는 실제 native 전사 호출로도 확인했다.

## 설정·실행 경로

설정은 기존 `settings.json` 하나다. `providers.openai`, `providers.anthropic`, `providers.openrouter`에 `api_key_env`와 공식 `base_url`을 둔다. 환경 변수 이름을 바꿔 사용할 수 있으며, 접수한 작업의 고정 설정을 재개와 단계별 Router에도 전달한다. 키 값·개인 키 파일 경로는 설정이나 코드에 넣지 않는다. 앱·wrapper는 키 파일을 읽거나 source하지 않는다.

원격 stage의 기본 `provider`는 `auto`다. 기존 `openrouter` 값은 원격 profile의 호환 값이며 같은 키 우선순위를 따른다. `--profile remote`도 auto를 사용한다. `scribe doctor`는 인증 값 없이 공급자별 키 존재 여부와 선택 경로를 보여준다. 호환 worker에서도 설정 모델을 기본 모델로 덮어쓰는 분기를 제거했다.

직접 요청의 실패·인증 오류·제한 응답·timeout 뒤 OpenRouter로 자동 재요청하지 않는다. 요청 전 키가 없는 경우의 경로 선택과 이미 시작한 요청의 재호출을 구분한다. 공급자별 raw 응답은 그대로 보존하고, 선택 경로는 별도 `provider_routes_v3`에 기록한다. 이 테이블에는 공급자·요청 모델·native ID·환경 변수 이름·선택 이유만 들어간다.

## 요청·과금 계약

- OpenAI 텍스트는 Chat Completions의 `max_completion_tokens`, `reasoning_effort`, 명시적 Standard tier를 사용한다. 출력 상한에는 reasoning도 포함된다. 공개 prompt cache 계약에 맞춰 explicit/30m를 지정하고 cache read/write도 usage 계산에 포함한다.
- Anthropic은 Messages API, adaptive thinking, `output_config.effort`를 사용한다. 번역·교정의 JSON schema는 `output_config.format`으로 전달한다. 응답의 segment ID·개수·숫자·부정 보존은 기존 후검사로 다시 확인한다. 공급자 grammar에 의존하지 않는 배열 개수 제한은 앱이 검사한다.
- native `gpt-transcribe`는 multipart `languages[]`와 duration usage를 사용한다. 단일 `language`를 그대로 전달하지 않으며, 응답의 `languages`를 언어 출처와 함께 보존한다. 시간·화자 정보를 만들어내지 않는다.
- 모든 경로가 같은 예약 원장·원격 동시 실행 상한·실행 소유권 문맥을 사용한다. native 호출에는 OpenRouter의 요금을 빌려 쓰지 않는다. 2026-11-05 확인한 공식 Standard/global 요금과 실제 native usage로 USD를 계산하고 `cost_source=calculated_from_native_usage`를 기록한다. 이는 공급자가 반환한 청구서 USD라는 뜻이 아니다.
- 장문 구간·캐시 쓰기를 포함한 보수적 상한을 먼저 예약한다. usage 누락·잘못된 계수·알 수 없는 tier·지역·속도·추가 도구 과금은 미확정으로 남기고 후속 유료 호출을 막는다. output이 잘려도 확인된 사용량 정산과 raw 응답은 보존한다.

근거: [GPT-6 Luna와 요금](https://developers.openai.com/api/docs/models/gpt-6-luna), [OpenAI 캐시 usage](https://developers.openai.com/api/docs/guides/prompt-caching), [Claude Haiku 5.5와 요금](https://platform.claude.com/docs/en/models/haiku-5-5/overview), [Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort), [구조화 출력](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [GPT-Transcribe](https://developers.openai.com/api/docs/models/gpt-transcribe).

## 검증

새 라우팅 검사 세 개는 원래 코드에서 오류로 재현됐고, OpenRouter 유지 사례는 원래부터 통과했다. 이후 직접/대체 경로·native 키만 있는 실행·custom/frozen 환경 변수 참조·HTTP 오류/timeout 무재호출·캐시/장문 계산·구조화 출력·잘린 출력·native 전사·중첩 usage 오류를 포함한 15개 검사로 확장했다.

최종 전체 검사는 격리 HOME에서 `python -B -m unittest discover -s tests -v`로 519개, 123.318초, OK였다. 실행 전후 코드 해시도 일치했다. 로그와 고정 입력은 `/tmp/scribe-native-routing-final.log`, `/tmp/scribe-native-routing-final-inputs.json`이다. 중간 custom-env CLI fixture에서 PATH를 비워 ffprobe를 찾지 못한 오류를 고쳤고, 그 중간 실행을 최종 합격으로 사용하지 않았다.

실제 API 검사에는 영어 합성 음성 약 7초를 사용했다. native 전사 1건, 두 모델의 요약 2건, 두 모델의 구조화 교정 2건이 모두 완료됐다. 후속 세 작업은 전사 캐시를 재사용했다. 서버가 반환한 전사 사용량은 8초였고, 다섯 요청의 계산 비용 합계는 $0.0009412였다. 기존 검증을 포함한 공유 원장의 합계는 $0.1622438159358404, 미정산 0건, 상한 $10다. 실제 보고서는 `/tmp/open-scribe-rework-validation/native-provider-live-check.json`과 `native-structured-live-check.json`에 있다. 이 검사는 CSNL 한국어 정확도나 모델 선정 합격이 아니다.

## 설치·되돌리기

MacBook 설정 백업은 `~/.local/state/open-scribe/settings-backups/20261105-170836-native-routing/settings.before.json`, 이전 실행본/명령은 `~/.local/lib/open-scribe.backup-r3x43z`와 `~/.local/bin/scribe.backup-r3x43z`다.

Mac mini의 설치 영수증은 `~/.local/state/open-scribe/install-bundles/native-routing.4TMVDy`에 있다. `settings.before.json`이 설정 백업이며, 이전 실행본/명령은 `~/.local/lib/open-scribe.backup-tdpncB`와 `~/.local/bin/scribe.backup-tdpncB`다. 되돌릴 때 현재 실행본을 별도 보관하고 설정·실행본·명령을 함께 복원한다. 머신 간에는 실행 패키지와 설정 변경만 배포했고 프로젝트 저장소나 대화 세션의 동기화는 수행하지 않았다.

## Whisper Turbo와 상용 모델 비교의 한계

Whisper Turbo는 large-v3의 decoder를 줄여 속도를 높이고 정확도를 일부 양보한 공개 모델이다. 현재 OpenAI가 파일 전사에 권장하는 상용 모델은 `gpt-transcribe`다. 기존 CSNL 선정 표본에 이 상용 모델이 빠졌으므로 기존 비교를 OpenAI 상용 모델까지 포함한 선정 결과로 간주할 수 없다. 원음 검수 정답도 없어 한국어 회의에서 어느 모델이 더 정확한지는 미판정이다. 이번 라우팅 작업에서 기본 ASR을 임의로 바꾸지 않았다.

근거: [Whisper Turbo 공식 모델 카드](https://huggingface.co/openai/whisper-large-v3-turbo), [OpenAI 파일 전사 권장 모델](https://developers.openai.com/api/docs/guides/speech-to-text).

최종 설치 후 두 머신 모두 manifest와 실행본의 소스 불일치 0개를 확인했다. 각 머신에서 OpenAI의 Luna·GPT-Transcribe, Anthropic의 Haiku 모델 조회가 모두 HTTP 200이었다. 설치된 CLI의 HTTP 경계만 대체한 요약 검사 두 건도 각각 `completed`, 종료 코드 0, helper 생성 0회였다. 이 설치 검사 자체는 유료 추론을 보내지 않았다. Mac mini의 첫 격리 검증은 zsh -f 환경에 Homebrew PATH가 없어 실패했고, 실제 실행 환경과 같은 PATH를 지정한 재실행으로 통과했다. 설정 검증과 scribe/scr 진입점도 확인했다.

MacBook 설치 검증은 `/tmp/scribe-native-routing-installed-verification.json`, Mac mini 검증은 위 영수증 디렉터리의 `verification.json`에 있다.
