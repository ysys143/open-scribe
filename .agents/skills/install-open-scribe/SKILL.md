---
name: install-open-scribe
description: open-scribe의 소스 설치와 설치 경로·명령 해석을 진단한다.
---

README.md와 scripts/install.sh의 현재 계약을 읽는다. 공개 CLI는 `scribe INPUT`이다.
`ls [n]`, `config show`, `config validate`를 지원한다. `transcribe`, `auth`, `review`, `dashboard`, `--json`, `--quiet`는 없다.

`bash scripts/install.sh --python python3.11` 또는 준비된 환경을 재사용하는 `--venv DIR`를 사용한다.
기존 대상 교체에는 `--upgrade`가 필요하다. `OPEN_SCRIBE_HOME`·`OPEN_SCRIBE_BIN_DIR`로 경로를 고른다.
활성 전사 프로세스가 있는 설치 경로는 바꾸지 않고 별도 runtime으로 설치해 새 호출만 전환한다.
설정·키·DB·실행 중 작업은 설치 과정에서 수정하지 않는다. rc와 다른 명령을 임의로 바꾸지 않는다.

모델 설정은 settings.json의 stages 모델·options, 인증은 providers의 api_key_file·api_key_env를 사용한다.
일반 설정은 모두 settings.json이다. .env를 자동 로드하지 않고 일반 환경변수로 덮어쓰지 않는다. copy_to_path는 복사 위치이며 null이면 비활성화한다. 키 파일에서 지정한 인증 변수만 읽고 키 값은 출력·복사하지 않는다.
Keychain 등록·전역 export를 인증 해결로 사용하지 않는다. 선택한 파일의 소유자와 권한 600을 확인한다.
실제 셸의 `scribe`·`scr` 경로와 `--help`를 확인한다. 유료 호출은 설치 검증에 포함하지 않는다.
