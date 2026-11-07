# OpenScribe rework specification

> 역사 기록 — 초기 개편 명세와 원래 승인 기준이다. 아래 OpenRouter 전용·화자 기본 활성·120초 청크 가정은 당시 설계이며 현재 기본값이 아니다. 본문과 당시 기준은 보존했다. 현재 설정·구조·655개 코드 검증은 [문서 입구](README.md), [사용 안내](../../user-guide.md), [현재 구조](../../architecture.md), [통합 기록](../../development/optional-modes-implementation.md)을 따른다. 실제 릴리스는 [담당 F 기록](optional-modes-release.md)에서 구분한다.

## User stories
Users submit YouTube, playlists or audio from CLI or Telegram, obtain transcripts with speakers and summaries, and resume failed stages without losing completed work or deleting source audio.

## Decisions
User authorized implementation of the conversational plan on 2026-11-05. Remote inference uses OpenRouter. CLI remains primary. Telegram moves to the Mac core using polling; operational webhook changes require separate approval. Default speaker separation is enabled, permanent enrollment requires explicit confirmation. Local 30B models are excluded. Local helpers may fail without losing remote results. GPU is allowed; memory is the primary admission criterion.

## Shape
CLI and Telegram call one Application service backed by SQLite and immutable JSON artifacts. A frozen JobRequest is captured at submission; Transcript segments and words retain timing provenance. Provider clients and isolated local subprocesses implement the same stage result contracts. This replaces duplicated orchestration rather than maintaining two execution cores. Existing adapters may supply local inference, not another application pipeline.

## Acceptance criteria
- CORE-01: CLI and Telegram use the same job service and output schema.
- DATA-01: Existing job records and user inputs survive migration, success, failure and cancellation.
- JOB-01: Failed chunks prevent full completion; restart reuses completed chunks and stages.
- REMOTE-01: OpenRouter response capabilities, truncation, retryable errors and uncertain billing are recorded.
- SPEAKER-01: Speaker attribution preserves overlap and unknowns; identity confirmation is explicit.
- RESOURCE-01: Unqualified helpers, memory pressure, missing telemetry, OOM and timeout cannot destroy remote output.
- RESOURCE-02: Only one local helper runs across processes; children and model memory are reclaimed.
- OUTPUT-01: TXT/JSON/SRT/VTT/Notion render the same structured result; transformations preserve segment IDs.
- BOT-01: Telegram updates are persisted before acknowledgment and deduplicated; owner data is isolated.
- BUDGET-01: Verification reserves and settles usage against a shared $10 ceiling; unknown outcomes remain reserved.

## Constraints
Local helpers: one process, two CPU threads; GPU allowed. Require >=8GiB available memory, normal pressure, qualified <=3GiB measured peak. Stop at 4GiB or system pressure. Allocation APIs are advisory, not absolute caps. Poll every second. Timeout max(120s, duration*0.5), capped at 900s. No automatic model downloads or helper retry. No deployment, webhook switch, messages to others, or paid calls beyond the authorized cap.

## Edge cases
Partial network responses; process death during API call; owner collisions; duplicate Telegram update; same basename different audio; repeated migration; expired execution lease; missing timing; overlap; zero-length words; truncated LLM output; low memory; malformed provider response; unavailable local models; original input versus generated cache ownership.

## Assumptions
Defaults are configurable: remote concurrency two, helper concurrency one, audio chunks 120s, generated audio retention seven days. User originals are never cleanup targets. Voice vectors persist until explicit deletion; source clips are not retained by default. Measured backend qualification precedes automatic helper execution. Real quality and resource qualification remain release gates, not facts inferred from unit tests.

## Verification and rollout
First build executable integration/RED checks, then initialize the v2 verification contract using existing commands. Each vertical slice must run its entry-to-storage path. Migrate with backup and transaction; do not mutate historic model/timing provenance. Before switching Telegram polling, inspect webhook state and prepare rollback; obtain operational approval. API and model tests use separate opt-in runners; mock tests cannot certify real model support.
