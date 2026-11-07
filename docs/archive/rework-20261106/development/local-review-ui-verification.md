# 로컬 검토 UI 구현·검증 기록

작성: 2026-11-06T19:11:43

## 판정

소스 구현과 warm-browser 실행·저장·종료 검증은 완료했다. **콜드 브라우저 시작 시간 측정은 미완**이다. 현재 사용자의 기본 브라우저는 Google Chrome이며 실제 열려 있던 사용자 탭을 임의 종료하지 않았다. 다른 브라우저와 다른 OS의 종료 호환성은 확인하지 않았다.

기존 작업 트리의 변경·삭제와 재구성은 유지했다. 이번 구현은 `src/core/review/`, `ui/`, Pen 문서와 검토 테스트를 추가하고 CLI·설치·컨테이너 허용 목록·사용 안내·공용 scribe 스킬을 연결한 것이다. 기본 설치본을 직접 교체하지 않고 임시 prefix에서 설치를 검증했다.

## 완료 기준과 근거

- [x] CLI·설치·기존 화자·신규 검토 회귀 검사 136개 통과.
  - 명령: `.venv/bin/python -B tests/run_credentials_isolated.py tests.cli.test_cli tests.install.test_install tests.speakers.test_identity tests.review.test_state tests.review.test_server`
  - 출력: `Ran 136 tests`, `OK`; 격리 스냅샷 실행 전후 SHA-256 동일.
  - 실행 후 추가된 서버의 저장 질문 사전 검증은 신규 검토 검사 34개와 실제 설치본 20회 실행으로 확인했다.
- [x] TypeScript 검사·UI 행동 검사 15개·배포 번들 빌드 통과.
  - 명령: `npm run --prefix ui check`, `npm test --prefix ui`, `npm run --prefix ui build`.
  - 출력: tsc exit 0, `pass 15`, `fail 0`, Vite build exit 0.
  - 필수 재생 요소가 숨겨지거나 실제 렌더링되지 않는 두 결함을 실패로 먼저 재현한 뒤 차단했다.
- [x] 원문·revision 보호 검사 유효성 확인.
  - 분리 복사본에서 source-hash guard와 revision guard를 제거했다. 정상본 exit 0, 두 변이 모두 exit 1로 검출했다.
  - 대표 음성 등록 시 원음 교체와 기존 정렬의 수동 시간 재사용 결함도 실패로 재현한 뒤 차단했다.
- [x] 실제 기본 브라우저의 질문 저장·종료 모달·탭 종료·포트 해제.
  - 시스템 기본 브라우저로 localhost를 열었다. 사용자 클릭을 모의해 저장하고 ‘예’를 누른 뒤 검증 탭이 사라짐을 native UI에서 확인했다.
  - 질문 4종, 사용자 보충, 원본 변경 재검토, 시각 없는 원음의 범위 지정, 등록 화자 상세·음성 재생을 실행했다.
  - 6개 구간의 일괄 등록을 UI에서 수행하고, DB 인물 수 1개 및 6개 구간의 person ID가 같음을 읽기 전용으로 확인했다.
  - 확인한 수동 검증 포트는 모두 해제됐다. 새 상주 서비스는 등록하지 않았다.
- [x] Pen 디자인 작성 및 확인.
  - `designs/open-scribe-review.pen`: 핵심 8화면, 공통 상태 5개, 좁은 창 예시, 공통 플레이어·버튼.
  - Pen의 Get bounds/problems 조회와 화면별 TakeScreenshot으로 잘림·정렬·대비를 확인했다. 기존 다른 프로젝트 문서는 수정하지 않았다.
- [x] Node 없는 설치·실행 검증.
  - `scripts/install.sh --prefix TEMP_PREFIX --skip-deps --venv PREPARED_VENV --python PYTHON`으로 설치했다.
  - PATH에서 Node를 찾을 수 없는 환경에서 catalog 및 실제 화자 관리 UI를 실행했다. 정보 수정 후 저장·탭 종료도 확인했다.
  - 현재 소스와 설치본의 review Python 파일·정적 번들·주요 진입점이 바이트 단위로 같음을 확인했다.
  - 번들이 없는 소스는 설치에서 거절하고, 유효 번들은 manifest로 검증한다.
- [x] 공용 스킬 적용.
  - `~/.agents/skills/scribe` 정본 및 Claude 관리 복사본 3곳의 내용 일치. quick_validate: `Skill is valid!`.
  - Codex는 공용 정본을 직접 검색한다. 모델용 음성 임베딩이나 유료 추가 요약은 이 UI가 실행하지 않는다.
- [x] 의존성 및 변경 형식 검사.
  - `npm audit --prefix ui --omit=dev`: `found 0 vulnerabilities`.
  - `git diff --check -- .gitignore .dockerignore scripts/install.sh README.md`: exit 0.

## 최종 설치본 성능

- 기준: **이미 실행 중인 Chrome**, 합성 WAV와 가상 전사, Node가 없는 PATH, 실제 설치된 main.py를 공개 CLI 인자로 실행.
- 측정: subprocess 호출 직전부터 검토 데이터 렌더링 후 두 animation frame까지. 첫 소리의 재생 지연·실제 회의 정확도 지표는 아니다.
- 반복: 20회. p95: **357.62 ms**, 목표 1000 ms 이내 통과.
- 측정 중 Python source·번들 버전이 바뀌지 않았음을 검사했다. 아래 기록의 source 해시가 현재 저장소와 일치함도 확인했다.
- 설치본: `/var/folders/hw/9m3g7fvn4_l3rp2y473km9sm0000gn/T/scribe-installed-ui-bugxx1tp/acceptance-1793959601/lib/open-scribe`
- 원시 측정: `/var/folders/hw/9m3g7fvn4_l3rp2y473km9sm0000gn/T/scribe-ui-demo-xcjcobef/performance.json`
- UI manifest SHA-256: `3885dd4bb61384ae92516452190ca676c7f47a0ff5fab2f2f7ad57740906e865`

## 남은 검증

| 항목 | 담당·일자 | 미실행 이유 | 재검토 조건 | 상태 |
|---|---|---|---|---|
| 브라우저가 꺼진 상태의 전체 시작 시간 | 현재 구현 에이전트 · 2026-11-06 | 기존 사용자 Chrome을 임의로 종료하지 않음 | 사용자의 브라우저 종료·재실행 지시 또는 브라우저가 이미 꺼진 환경 | 사용자 승인 없음 · 미완 |

실제 사용자 녹음·신원 데이터, 유료 전사 API, GPU·모델 추론은 검증에 사용하지 않았다. 합성 자료와 계약·경로 검증이며 실제 음성 전사 정확도나 겹침 복원 성능을 입증하지 않는다.
