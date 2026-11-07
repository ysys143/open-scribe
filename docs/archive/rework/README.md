> 과거 개편 문서 목록: 아래 진행 상태는 작성 당시의 기록이다. 현재 분류는 [문서 입구](../../README.md)를 따른다.

# OpenScribe 문서 입구

[프로젝트 README](../../../README.md)로 돌아가기.

현재 사용법은 사용 안내와 현재 구조를 기준으로 읽는다. 날짜가 붙은 실험·설치·검증 기록의 수치와 판정은 해당 소스·표본에 한정된다. 옛 문서의 `최종`, `완료`, `기본값`을 현재 릴리스 상태로 해석하지 않는다.

현재 진행 상태: A의 native format adapter 동결 소스로 전체 671개 코드 검사가 통과했다. 단일 JSON fence·명시 alias를 처리하며 reason 생략은 의미 검토 상태로 남겨 자동 적용을 막는다. 기존 655·662개는 각각 이전 버전의 근거로 보존한다. E의 독립 리뷰와 실제 probe는 이번 코드 검사에 포함하지 않았으며, 사용자 지시에 따라 제품 최종 설치 보류·F 추론 중지를 유지한다.

## 현재 안내와 구조

| 문서 | 읽을 내용 |
|---|---|
| [사용 안내](../../user-guide.md) | settings.json, CLI·Telegram, 선택 기능, 출력·재개·사람 확인·로컬 자격 |
| [현재 구조](../../architecture.md) | 공통 Application·SQLite, native 키 우선 라우팅, 자원·과금·후보/확인 경계 |
| [선택 모드 통합 계약·검증](../../development/optional-modes-implementation.md) | A/B/C/D 연결·현재 limits, 버전별 655·662·671개 동결 검사·SHA, 로컬 correct format 호환·의미 검토 경계 |
| [릴리스 기록 — 담당 F](optional-modes-release.md) | 모델 준비·설치본·짧은 실제 실행·릴리스 진행. F가 갱신하는 별도 기록 |

기본 ASR·요약은 API를 사용한다. 정렬·화자 분리·임베딩·재청취·이름 후보는 기본 off다. 모델·키·개인 설정·설치본을 이 문서 정리에서 바꾸지 않았다. 설정 정본은 `settings.json`이며 인증은 환경 변수 참조다.

현재 소스에는 작업량 기본값 차이가 있다. `settings.defaults()`의 재청취 `max_windows`는 32이고 A 함수의 옵션 생략 fallback은 6이다. Application은 settings 값을 전달한다. 사용 안내의 6은 명시적 예시 제한이며, 이를 내장 기본값 변경으로 해석하지 않는다.

## 기능별 계약

| 문서 | 범위와 주의점 |
|---|---|
| [선택 모드 통합 계약](../../development/optional-modes-implementation.md) | 로컬 재청취 ASR + 소형 LLM 후보, 별도 Scribe 화자 API, 영상 이름 후보의 실제 Application 경계 |
| [별도 화자 API 모듈 계약](../../development/composite-api.md) | B adapter의 단일 요청·구간·인증·과금 계약. 모듈 입력 계약과 Application 전처리를 구분한다. 현재 Application은 24MiB 초과 원본을 변환 전 거절한다. |
| [이름 후보 계약](../../development/speaker-names.md) | 출처 검증·임시 혼합 화자 turn view·프레임 한도·미검증 표시. 후보는 인물 확인이나 음성 등록이 아니다. |
| [native 공급자 라우팅 도입 기록](native-provider-routing.md) | 같은 모델의 native 키 우선 계약과 도입 당시 시험·설치 기록. 당시 519개 수치는 최신 전체 검사가 아니다. |
| [ASR 평가 하네스](../../development/asr-evaluation.md) | manifest·평가·정답/CER 관문. 하네스 구현과 모델 선정 합격을 구분한다. |

직접 `name_speakers(..., folder=...)` 호출의 배타 sidecar와 Application이 관리하는 `speaker_names/`도 구분한다. Application의 파일 위치·모드 순서는 통합 계약을 따른다. `named/`는 사람 확인 전용이며 영상 후보가 그 manifest를 차지하지 않는다.

## 실험·수정 이력

| 문서 | 당시 기록 |
|---|---|
| [Scribe 통합 API 시험](scribe-diarization-trial.md) | 짧은 실제 API 표본의 반환 시간·화자. 전체 60분 정확도나 실명 검증이 아님 |
| [ASR 복구 구현·실행 기록](asr-reliability-implementation.md) | 당시 소스·실측 표본·설치·실패와 검수 미완 기록 |
| [settings 통합 이력](settings-unification.md) | 당시 305개 검사와 설정·인증·설치 이행 기록 |
| [API 기본 실행 전환 이력](api-defaults.md) | 당시 504개 검사와 개인 설정 전환 기록. 현재는 native 키 우선 경로와 새 선택 stage를 함께 읽음 |

실험 원본과 과거 측정값은 보존한다. 새 소스의 결과로 숫자를 덮어쓰거나 과거 표본을 현재 버전 실측으로 바꾸지 않는다. 개인 설정에 관한 과거 기술은 문서 정리에서 그 파일을 다시 조회·수정했다는 뜻이 아니다.

## 원래 계획과 옛 인수 검증

| 문서 | 보존하는 범위 |
|---|---|
| [초기 명세](spec.md) | 원래 요구와 10개 승인 기준. 당시 OpenRouter 전용·화자 기본 on·120초 가정 포함 |
| [ASR 복구 계획](asr-reliability-plan.md) | 당시 복구 목표와 관문. 실행 근거는 별도 구현 기록에 있음 |
| [초기 구현 상태](implementation-status.md) | 초기 개편 당시 구현·미완 관문 |
| [초기 검증](verification.md) | 당시 242개 검사·10개 기준·과거 실제 표본과 운영 관문 |
| [초기 독립 검토](independent-review.md) | F11/F12/F15 등 당시 집중 범위의 판정·파일 SHA |
| [원래 검증 계약](verification-contract.yaml) | 초기 승인 기준. 새 선택 모드 전체의 최신 완료 증명으로 확장하지 않음 |
| [구현 전달 영수증](worker-deliveries.json), [검토 전달 영수증](reviewer-delivery.json) | 당시 위임·전달 이력 |

## 증거를 읽는 기준

동결 소스 655개 통과는 HTTP·ML 경계를 대체한 코드 검사와 실제 SQLite·ffmpeg·프로세스 경로 검사다. 동결 manifest SHA-256은 `4ce8b3d0c5bcc8dc2348a49526112a83631baa61c08d71d7caea7ab5ff9e198b`다. 이는 실제 모델 품질 인증이나 릴리스 완료 선언이 아니다.

후속 correct prompt·실패 진단 보존 패치 이후에는 새 manifest `accbd7a7809237b7c8622e59f6a4d6d244ddbbf1206786d67fbcfcfc7afd4b77`로 전체 662개가 통과했다. 이전 655개·실측 실패 이력과 구분해 통합 기록에 추가했다. 새 코드 검사도 실제 correct 자격 성공이나 실패 원인 확정을 뜻하지 않는다.

native format adapter 이후에는 manifest `b084f1f757fdf3f1a5283313f8183eabda93483adb9c786e1d3c9dbf48ae4247`로 전체 671개가 통과했고 전후 SHA가 같았다. 형식 수용·자원 자격·의미 검토를 구분하며, reason이 없어 검토가 필요한 후보를 자동 적용하지 않는다. 별도 실제 probe·독립 리뷰·릴리스 승인과 같은 결과로 해석하지 않는다.

문서 JSON 예시의 `settings.validate` 통과는 스키마·기본값 병합의 근거다. 준비 모델 존재·의존성 설치·측정 자격·유료 API 응답을 증명하지 않는다. 실제 실행 여부와 설치·릴리스 결과는 F 기록을 따른다. 정확도·CER·화자/실명 합격은 별도 정답 대조가 필요하다.
