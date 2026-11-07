# Scribe v2 통합 API 시험 — 2026-11-05

CSNL-1104의 원본 828–856초(13:48–14:16) 클립을 OpenRouter `elevenlabs/scribe-v2`에 한 번 요청했다. 전사·단어 시각·화자 라벨이 함께 반환됐다. 실행 stage는 `asr:0` 하나였고 로컬 정렬·화자 분리·임베딩·요약은 실행하지 않았다.

## 실제 결과

| 항목 | 관찰값 |
|---|---:|
| 오디오 길이 | 28초 |
| 유료 전사 요청 | 1회 |
| 반환 단어 단위 | 57개 |
| 화자 라벨이 있는 단어 | 57개 |
| 시작·끝 시각 필드가 있는 단어 | 57개 |
| 양의 시간 구간을 가진 단어 | 55개 |
| 시작=끝인 단어 | 2개 |
| API 화자 라벨 | 2개 (`0`, `1`) |
| 인접 동일 화자로 묶은 구간 | 10개 |
| 요청 비용 | $0.0017111111111108 |
| 공유 검증 원장 합계 | $0.1639549270469512 |
| 미정산 | 0건 |

실행은 `completed`, 자동 구조 검사는 `accepted`였지만 원음 정답은 pending이다. CER·정확도 합격·실제 사람 수·실명 확인을 뜻하지 않는다. `거.`(클립 5.00초)와 `예.`(16.44초)는 길이 0이어서 검토 항목으로 남겼다. 임의로 시각을 늘리거나 단어를 삭제하지 않았다.

화자별 표시를 만들 때 canonical 본문과 단어를 문자 위치로 대응시켜 묶었고, 공백을 제외한 전체 문자가 원출력과 같음을 확인했다. 화자별 묶음 10개는 모두 양의 시간 구간을 가져 별도 검토용 SRT를 생성했다. JSON·SRT는 클립 기준 시간이고 TXT에는 원본 기준 시간을 표시했다.

산출물: `/Users/jaesolshin/Downloads/CSNL-1104-Scribe-diarized-20261105-182623/`의 `REVIEW.md`, `transcript.txt`, `transcript.json`, `speaker-turns.json`, `speaker-turns.srt`, 원음 클립, raw 응답. 녹취 자료는 저장소에 추가하지 않았다. 실행 기록은 `/tmp/open-scribe-rework-validation/scribe-diarization-20261105-182138/RUN-REPORT.json`이다.

## 요청·구현

```json
{
  "stages": {
    "asr": {
      "provider": "auto",
      "model": "elevenlabs/scribe-v2",
      "options": {
        "language": "ko",
        "provider_options": {
          "elevenlabs": {
            "diarize": true,
            "tag_audio_events": false,
            "no_verbatim": false
          }
        }
      }
    },
    "alignment": {"enabled": false},
    "diarization": {"enabled": false},
    "embedding": {"enabled": false}
  }
}
```

설정의 `provider_options`는 접수 시 고정하고 stage 캐시 키에도 포함한다. 예전 JSON 전사만 있던 결과를 화자 분리 완료 결과로 재사용하지 않는다. 문서로 확인한 Scribe verbose/word 계약을 첫 요청부터 선택하고 `provider.options.elevenlabs`를 JSON 오디오 요청에 전달한다. 활성 endpoint tag와 화자 지원 여부, 옵션 타입·범위·상호 배타 조건을 업로드 전에 검사한다. API 키는 기존 실행 환경 참조만 사용한다.

화자 ID는 요청 하나의 라벨이다. 여러 요청에서 같은 번호가 반환되면 canonical 결과의 ID에 요청 namespace를 붙이고, raw 라벨과 대응표를 함께 보존한다. 이를 동일인으로 자동 합치지 않으며 전체 화자 연결을 partial로 남긴다. 라벨이 누락돼도 로컬 모델로 자동 보완하지 않는다. 이 제한 때문에 이번 시범은 한 요청에 들어가는 28초 구간으로 수행했고, 전체 60분의 통합 화자 검증은 아직 하지 않았다. 기본 ASR 모델도 이번 시험으로 변경하지 않았다.

근거: [OpenRouter의 ElevenLabs 통합 문서](https://openrouter.ai/blog/announcements/elevenlabs-on-openrouter/), [STT 옵션 계약](https://openrouter.ai/docs/guides/overview/multimodal/stt), [ElevenLabs native API](https://elevenlabs.io/docs/api-reference/speech-to-text/convert).

## 회귀 검사

초기 다섯 검사에서 설정·Scribe 요청 계약·API 화자 경로를 수정 전 실패로 재현했다. 단일 요청 라벨 반환, 옵션 고정, 라벨 누락 시 무로컬 fallback, 서로 다른 요청의 재사용 ID 분리와 잘못된 옵션 거절을 포함해 여섯 검사를 추가했다. Scribe의 문서 계약이 확인됐으므로 기존 `unknown` 기대값도 문서 근거의 `supported`로 갱신했다.

격리 HOME의 최종 전체 검사는 525개, 128.454초, OK였다. 실행 전후 소스 해시가 일치했다. 로그와 고정 입력은 `/tmp/scribe-api-diarization-full.log`, `/tmp/scribe-api-diarization-inputs.json`에 보존한다. 첫 중간 실행의 status 문자열 기대값과 기존 unknown fixture 오류는 고친 뒤 최종 검사에 포함했다. 유료 요청의 raw 응답·비용·원본 클립은 보존했다.

MacBook과 Mac mini 설치본에도 반영했다. 두 설치본의 manifest 소스 불일치 0개, 설치 CLI의 mock HTTP 경계 검사에서 단일 전사 POST·화자 상태 completed·helper 생성 0회·종료 코드 0을 확인했다. 실제 모델 호출은 앞의 CSNL 28초 요청 한 번뿐이며 설치 검사에서 추가 유료 요청은 보내지 않았다. MacBook 이전 실행본/명령은 `backup-Ki1u9B`, Mac mini는 `backup-gRR3Eo`로 보존했다. 설정 파일은 바꾸지 않았다. Mac mini 영수증은 `~/.local/state/open-scribe/install-bundles/scribe-diarization.8jHRHD`에 있다.
