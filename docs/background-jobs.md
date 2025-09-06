# Background Jobs Architecture (TUI Queue + Worker Daemon)

본 문서는 TUI에서 생성된 작업을 백엔드 워커가 비동기로 처리하고, 모니터링 화면에서 상태를 추적할 수 있도록 하는 아키텍처를 정의합니다. 구현은 최소 침투 방식으로, 기존 CLI/DB를 재사용합니다.

## 목표
- TUI 종료와 무관하게 안정적인 백그라운드 전사 처리
- 동시 실행 개수 제한, 재시도/실패 처리, 로깅 일원화
- 모니터링 화면에서 상태/진행률 조회 및 관리

## 전체 흐름
1) TUI(Producer): 사용자가 Background 옵션으로 Run → 큐 엔큐 + DB 상태 `queued` 저장
2) Worker(Consumer): 큐 폴링 → 작업 잠금 → `main.py` 서브프로세스 실행 → 로그/상태 업데이트
3) Monitor: DB와 로그를 조회해 진행률/상태 표시, 취소/재시작 트리거 제공(후속 구현)

## 디렉터리 및 파일
- `queue/`: 대기 작업 JSON 파일 저장
- `logs/`: 각 작업 실행 로그 저장
- `transcript/`, `audio/`, `video/`: 기존 결과물 저장 경로

## 큐 파일 포맷(JSON)
```json
{
  "job_id": 123,
  "video_id": "Dm1V-ODwb1Q",
  "url": "https://youtu.be/Dm1V-ODwb1Q",
  "title": "Video title",
  "engine": "gpt-4o-mini-transcribe",
  "force": false,
  "timestamp": "2025-09-05T18:33:00"
}
```

## DB 상태 전이(State Machine)
- `queued` → `running` → `completed` | `failed` | `cancelled`
- 보조 플래그: `download_completed`, `transcription_completed`, `summary_completed`, `srt_completed`, `translation_completed`
- 재시도: 실패 시 `retry_count`(DB 확장 고려) 증가, 정책 기반 재큐잉

## 워커 데몬(worker.py) 개요
- 책임: `queue/` 폴링 → 잠금 → 실행 → 상태/로그 업데이트 → 종료 처리
- 실행: `.venv` 활성화 + `uv` 환경 전제(프로세스 외부에서 보장)
- 동시성: `--concurrency N` (기본 2~3 권장)
- 폴링 간격: `--interval SEC` (기본 2s)
- 안전성: 락 파일(`.lock`) 사용으로 중복 실행 방지

### 워커 동작 단계
1) 큐 스캔: `queue/*.json` 정렬(생성시간) → 여유 슬롯만큼 픽업
2) 락: 동일 basename으로 `.lock` 생성 성공 시 획득, 실패 시 skip
3) DB 업데이트: `status=running`, `updated_at=NOW()`
4) 프로세스 실행: `python main.py <url> --engine <engine> [--force] ...`
   - 로그 파일: `logs/job-<job_id>-<ts>.log` (stdout/stderr tee)
   - `OPEN_SCRIBE_TUI_LOG` 환경변수로 경로 전달(선택)
5) 종료 처리:
   - rc==0 → `status=completed`, transcript_path/summary 등 DB 필드 갱신
   - rc!=0 → `status=failed`, 에러 메시지 기록(가능 시)
6) 정리: 락 해제, 큐 파일 이동(archive/ 또는 삭제)

### 프로세스 호출 규약
- 기본: `sys.executable main.py <url> --engine <engine>`
- 옵션 매핑: timestamps/summary/translate/srt/video/force → 동일 CLI 플래그 사용
- CWD: 프로젝트 루트

## 로깅
- TUI 측: `logs/tui-run-YYYYMMDD-HHMMSS.log` (이미 구현)
- 워커 측: `logs/job-<job_id>-YYYYMMDD-HHMMSS.log`
- 모니터링: 최근 N라인 tail 노출, 전체 보기/다운로드 제공(후속)

## 모니터링 연동(Phase 4)
- 데이터 소스: SQLite(`transcription_jobs`) + `logs/`
- 목록: `queued/running/completed/failed` 필터, 검색(제목/URL)
- 상세: 상태/진행률, 로그 tail, 파일 경로, 실행 시간, 엔진 정보
- 제어: 취소(cancel), 재시작(requeue), 강제 완료(mark) 등 액션 버튼

## 동시성/리소스 정책
- `--concurrency N`: 동시 실행 개수 제한(기본 2)
- 엔진별 리소스 가이드(참고): `whisper-cpp`는 고메모리(≥4GB/worker), GPT/YouTube API는 경량
- WorkerPool와 별도: 워커는 “작업 단위(영상)” 병렬, 내부 전사는 기존 병렬(청크) 로직 사용

## 재시도 정책
- 기본 3회, 지수 백오프(예: 5s, 15s, 45s)
- 오류 분류: 네트워크/한도/인증/자원부족/영구오류
- 영구오류는 재시도 금지, 메시지 표기

## 확장 포인트
- playlist 지원: 큐에 다수 영상 분해 enqueue
- 우선순위(priority): JSON에 `priority` 추가(낮은 숫자 우선)
- 예약 실행(scheduled_at): 특정 시간에만 픽업
- 취소/정지: `.cancel` 마커 파일 또는 DB 플래그로 워커에 신호 전달

## 보안/안전성
- 절대경로만 사용, 경로 정규화
- 민감정보 로그 금지(API 키 마스킹)
- 파일 권한 제한(0640)

## 구현 계획
1) worker.py 추가
   - 큐 스캐너, 락, 실행, 상태 업데이트, 로깅, 재시도
2) TUI
   - Background 체크 시 `_enqueue_background_job()`(구현됨)만 호출
   - Monitoring 화면: DB/로그 뷰어(테이블+tail) 추가
3) 문서화
   - 본 문서 유지보수, 운영 가이드 별도 문서화

## 예시: 워커 스켈레톤(요약)
```python
# worker.py (요약)
import os, json, time, subprocess
from pathlib import Path
from datetime import datetime
from src.config import Config
from src.database import TranscriptionDatabase

class QueueWorker:
    def __init__(self, queue_dir: Path, concurrency: int = 2, interval: float = 2.0):
        self.queue_dir = queue_dir
        self.concurrency = concurrency
        self.interval = interval

    def run(self):
        while True:
            running = self._count_running()
            slots = max(0, self.concurrency - running)
            for q in self._next_jobs(slots):
                self._start_job(q)
            time.sleep(self.interval)
```

본 문서를 바탕으로 Phase 4에서 워커와 모니터링을 단계적으로 구현합니다.

