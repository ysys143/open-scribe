# OpenScribe 구현 상태

> 역사 기록 — 2026-11-05 초기 개편 당시 구현 상태다. 아래 242개 검사·과금·데이터 표본·미완 관문은 당시 증거로 보존하며 현재 소스나 설치 상태로 갱신하지 않았다. 현재 안내와 655개 동결 코드 검증은 [문서 입구](README.md)와 [통합 기록](../../development/optional-modes-implementation.md), 실제 준비·설치·릴리스 진행은 [담당 F 기록](optional-modes-release.md)을 따른다.

2026-11-05 KST. 공통 core와 CLI·Telegram polling, 화자 확인/등록/삭제, 실패를 격리하는 로컬 helper, 출력·비용 원장·설치 경로를 구현했다. 최종 동결 소스의 전체 242개 검사가 통과했고, 독립 검토는 코드 범위 PASS다. 실제 로컬 모델/GPU 자격과 운영 전환이 남아 있으므로 전체 개편을 완료로 판정하지 않는다.

구현과 참고 레포 설계 대응은 [아키텍처](../../architecture.md), 사용 명령은 [사용 안내](../../user-guide.md), 관측한 결과와 미완 관문은 [검증 보고서](verification.md), 검토자가 직접 재현한 지적과 수정 검증은 [독립 검토](independent-review.md)에 기록한다.

## 실행한 범위

- OpenRouter 실제 검증은 사용자 승인 10달러 원장 안에서 수행했다. 현재 읽기 전용 집계는 8회, $0.001239447, 미정산 예약 0이다.
- 원격 서비스는 외부 HTTP를 대체한 통합 검사와 별도 실제 호출로 구분한다. 실제 로컬 모델은 설치·다운로드·실측하지 않았다.
- 기존 DB는 읽기 전용으로 열어 임시 복사본에 migration을 검사했다. 최신 표본의 legacy ID 74개 전부를 보존했고 반복 개방 전체 행 수는 75개로 같았다. 원본에는 이미 v3 테이블이 있었다.
- 실제 Telegram/Notion 메시지·webhook 변경·배포·운영 설치·push·커밋은 수행하지 않았다. 기존 `.agents/` 및 설치 스킬 변경은 사용자 작업으로 보존했다.

## 위임과 검증 이력

사용자가 native 서브에이전트 병렬 사용을 승인했다. 같은 workspace에서 identity, resources/local, Telegram/packaging의 쓰기 경계를 나눴으며 별도 worktree·Orca는 사용하지 않았다. 독립 검토자는 코드 수정 없이 별도 snapshot과 임시 HOME에서 검사했다.

`open-scribe-rework-2026-11` 작업 기록과 v2 실행 계약은 같은 승인 기준 10개를 사용한다. v2 계약·preflight·brief는 구현 후 최종 증거를 정리하는 과정에서 생성했다. 사전 위임 절차가 실행됐다는 증거로 소급하지 않는다. `.jstack/tasks/open-scribe-rework-2026-11/`는 실행 영수증이며 사용자 승인 증명이나 실제 모델 품질 증명이 아니다.

임시 실행 자료는 `/tmp/open-scribe-rework-execution`, 실제 과금 원장은 `/tmp/open-scribe-rework-validation/transcription_jobs.db`다. 중간 실패와 병렬 작성 중의 통과 수치를 최종 통합 결과로 전용하지 않는다.
