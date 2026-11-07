# API 기본 실행 전환 — 2026-11-05

> 역사 기록 — API 기본 실행으로 전환했던 시점의 설정 변경·504개 검사·설치 결과다. 본문의 OpenRouter 전용 설명과 `--speakers`의 로컬 전용 의미는 당시 상태다. 현재는 같은 모델의 native 키 우선 라우팅과 선택한 diarization provider를 따른다. 아래 개인 설정·백업·실측 기록은 변경하지 않았다. 현재 기본 off·선택 모드는 [사용 안내](../../user-guide.md), 문서 구분은 [문서 입구](README.md), 코드 검사는 [통합 기록](../../development/optional-modes-implementation.md), 실제 릴리스는 [담당 F 기록](optional-modes-release.md)을 따른다.

사용자 요청에 따라 새 작업의 기본 추론은 OpenRouter API만 사용한다. 전사·요약의 API 공급자와 모델은 유지하고, 아래 로컬 보조 단계의 내장 기본값과 현재 사용자 설정을 비활성화했다.

```json
{
  "stages": {
    "alignment": {"enabled": false},
    "diarization": {"enabled": false},
    "embedding": {"enabled": false}
  }
}
```

활성 설정 경로는 `~/.config/open-scribe/settings.json`이다. 비활성화 상태에서는 로컬 helper를 만들거나 모델 fingerprint를 계산하지 않는다. API가 반환한 시간·화자 정보는 보존하며, 없는 정보는 자동 로컬 추론으로 채우지 않는다. 자막 시간이나 청크 문맥의 소유권을 확정할 수 없으면 검토 필요 상태를 유지한다.

로컬 기능은 해당 stage 설정이나 명시적 로컬 선택으로 사용할 수 있다. CLI `--speakers`는 로컬 화자 분리·정렬·임베딩을 명시 활성화한다. 호환 Telegram worker는 화자 옵션을 생략하면 `settings.json`을 따르며 기본 `speakers=True`를 강제로 주입하지 않는다. 접수된 작업을 ID로 재개할 때는 기존 고정 설정을 따르므로 이 변경으로 과거 작업의 스냅샷을 수정하지 않았다.

변경 전 설정은 `~/.local/state/open-scribe/settings-backups/20261105-153549-api-default/settings.before.json`에 보존했다. 이전 설치본은 `~/.local/lib/open-scribe.backup-8awyHY`, 명령은 `~/.local/bin/scribe.backup-8awyHY`다. 설정을 되돌리려면 설정 백업을 현재 설정 경로에 복원한다. 코드도 되돌릴 때는 현재 설치 디렉터리를 별도 보관한 뒤 이전 설치본과 명령을 복원한다.

검사 근거:

- `tests.test_api_defaults` 3개는 수정 전 모두 실패했고 수정 후 통과했다. API 전사·요약 HTTP 경계는 `httpx.MockTransport`로 대체했으며 유료 요청은 보내지 않았다.
- 로컬 helper 생성 시 강제 실패시키는 검사에서도 전사·요약과 API 화자 정보 보존 경로가 완료됐다. 내장 기본값·명시적 비활성화 경로·호환 worker 설정 상속을 확인한다.
- 관련 검사 88개가 통과했다. 기존 로컬 기능 검사는 해당 기능을 fixture에서 명시 활성화해 유지했다.
- 최초 전체 503개 중 로컬 VAD의 이전 기본값을 가정한 테스트 1개가 실패했다. 해당 fixture를 명시적 로컬 사용으로 바꾸고, 기본 API 빈 응답은 로컬 VAD 없이 검토 대상으로 남는 회귀 검사도 추가해 통과시켰다. 최초 전체 실행은 합격 증거로 쓰지 않는다.
- 설치본의 `scribe config validate`는 `valid=true`였고, 변경한 제품 파일 세 개가 소스와 바이트 단위로 일치했다. 설치된 내장 기본값과 현재 사용자 파일 모두 로컬 단계 세 개가 false다.
- 설치본 Python·CLI와 현재 사용자 설정에서 데이터 경로·외부 게시만 격리한 종단 검사도 수행했다. HTTP 경계만 MockTransport로 대체했고, 실제 CLI 결과는 `completed`, 종료 코드 0, helper 생성 0회였다. 요청은 OpenRouter 전사·요약 경로 두 개뿐이었다. 증거는 `/tmp/scribe-api-defaults-installed-cli.json`이다.
- 최종 전체 회귀 결과와 소스 고정 해시는 `/tmp/scribe-api-defaults-final.log`, `/tmp/scribe-api-defaults-final-inputs.json`에 보존한다. 설치 로그는 `/tmp/scribe-api-defaults-install.log`다.

키 파일 경로·키 값·별도 제어 파일은 추가하지 않았다. 앞선 ASR 복구 기록의 로컬 활성 설정과 설정 SHA는 그 실행 당시의 이력이며, 현재 기본 설정은 이 문서의 후속 변경을 따른다.

최종 전체 회귀는 504개, 121.007초, OK였다. 실행 전후 소스 해시가 일치했으며 최종 소스와 설치본의 제품 파일도 불일치 0개다.
