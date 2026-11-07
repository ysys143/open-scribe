# Telemetry 3.90초 갱신 중단: 실제 실행 진단

2026-11-06, MacBook. 제품이나 개인 설정을 수정하지 않고 진단했다.

## 핵심 결론

기존 실패는 실패로 유지한다. 기존 trace의 마지막 `observed_at=780609.0295`와 부모 검사 `780612.9319` 사이에는 약 3.9024초가 지났으며, 변경하지 않은 최신성 기준 3초를 초과했다. 이 기록만으로 GIL, allocator, import 또는 파일시스템 중 어느 것이 근본 원인인지 특정할 수 없다.

동일 제품 버전과 기존 가드 아래에서 최초 시도 1회와 단일 변수 진단 probe 2회, 총 3회를 실행했다. 이는 원래 최대 2회 지시를 1회 초과한 실행이다. 최초 시도에서 관측 스크립트가 실패했더라도 실제 실행 횟수에서 제외할 수 없다. 기존 표본의 최초 GPU 할당 전 갱신 중단은 재현하지 못했다. 세 번째 실제 CORRECT qualification은 성공했지만 관측 도구가 개입한 해당 실행의 결과일 뿐이며, 기존 실패를 성공으로 바꾸거나 원인이 해결됐다고 판단할 근거가 아니다.

두 번째 실행에서는 별도의 종료 단계 대기를 포착했다. 제품의 추론과 monitor가 정상 종료된 뒤, 진단 도구를 취소하는 주 스레드가 `faulthandler.cancel_dump_traceback_later → PyThread_acquire_lock_timed → _pthread_cond_wait`에서 기다렸다. faulthandler 스레드는 `_Py_DumpTracebackThreads → dump_traceback → dump_frame`에 있었다. 이때 최종 telemetry가 오래된 이유를 monitor 자체의 막힘으로 기술하지 않는다. 진단 도구가 추가한 종료 단계 대기이며, 기존 장애를 설명하지 않는다. 제한된 표본을 영구 교착으로 단정하지 않는다.

## 실행 경계와 재검토 자료

설치 Python은 `~/.local/lib/open-scribe/.venv/bin/python`이다. 실행 코드는 소스 체크아웃에서 가져왔으며 설치본은 수정하지 않았다. 실행 전후 SHA-256은 같았다.

| 파일 | SHA-256 |
|---|---|
| src/core/local.py | 841483129557b20124e0e374b8eee501f3536c2237d4b1e8f98bee3ebbb4fe66 |
| src/core/resources.py | d343fc0af939afc3bd5eee74fd16ab0baa2bc0897ff53bb901e7e2c050a7d14b |
| src/core/relisten.py | d015f719563bdf3d0708fd2a0198b9815af9ff84456c6720c31e0bfef4fd1a00 |

입력은 기존 비공개 실행 기록의 `inputs/items.json`에 있는 original/candidate 각각 영어 220단어와, 기존 공개 합성 음성 `~/.local/share/open-scribe/qualification-audio/align-probe.wav`이다. 음성 길이는 7.0526875초다. 모델은 사용자가 지정한 준비된 `qwen3-0.6b-correct-4bit`다. 프롬프트, 모델 출력 본문, 프레임 변수는 출력하지 않았다.

매번 실제 `Helper.qualify`를 호출했다. helper 시작 명령만 비공개 wrapper로 바꿨으며 wrapper는 원래 `local.execute`를 호출했다. 독립 세션, 전역 mutex, Store slot, 독립 watchdog, 오프라인·네트워크 가드, CPU 2, 가용 메모리 8 GiB, qualification 3 GiB, 중단 4 GiB, 기존 timeout, 1초 poll, 3초 최신성 기준은 유지했다. 부모 프로세스는 MLX나 모델을 import하지 않았다. API fallback, 유료 API 호출, 설치, 의존성·모델 수정은 없었다. 비공개 `Settings`는 메모리에서만 구성하고 설정 파일로 저장하지 않았으며 사용자 설정을 초기화하지 않았다. 이 문서 외의 쓰기는 저장소 밖 비공개 디렉터리에 한정했다.

| 시도 | 비공개 실행 기록 루트 | 결과 |
|---|---|---|
| 최초 실제 시도 | `/tmp/scribe-telemetry-urkvps6k` | 1.577초. 관측기의 `event(name, name=...)` 인자 충돌로 correct 진입 직후 실패했다. 오래된 telemetry 현상을 재현한 것이 아니다. |
| Probe 1 | `/tmp/scribe-telemetry-x96cqxqq` | 위 인자 충돌만 수정했다. 15.392초. 최종 sample의 부모 읽기 시점 age 3.5786초로 기존 가드가 거부했다. qualification 0개. |
| Probe 2 | `/tmp/scribe-telemetry-bbkg4d9f` | faulthandler 기능 묶음인 enable, dump 파일 열기, 반복 timer, cancel을 제거했다. 이 기능 묶음 제거를 단일 변수 변경으로 삼았다. 11.327초. qualify 성공, qualification 1개. |

각 디렉터리에 `probe.py`, `child.py`, `parent-events.jsonl`, `child-events.jsonl`, `status.json`이 있다. 뒤의 두 실행에는 `native-sample.txt`, `sample.stderr`도 있다. Probe 1의 `python-stacks.txt`는 중간에 잘렸으며, 이 잘림만으로 제품의 스택 위치를 입증할 수 없다. 루트 권한은 0700, 최상위 스크립트·실행 기록 파일 권한은 0600이다. macOS sample 전체 보고서는 비공개 경로에 보존했고 본문 전체를 복사하지 않았다.

실제로 사용한 시작 명령은 다음과 같다. 과거 실행을 재검토하기 위한 기록이며 추가 실행 지시가 아니다.

```sh
PYTHONDONTWRITEBYTECODE=1 ~/.local/lib/open-scribe/.venv/bin/python /tmp/scribe-telemetry-bbkg4d9f/probe.py /Users/jaesolshin/Documents/GitHub/open-scribe
```

진단 스크립트는 부모가 처음 telemetry를 읽을 때 `/usr/bin/sample <helper-pid> 12 10 -file <private>/native-sample.txt`를 시작했다. 부모·자식 JSONL은 같은 monotonic 시계를 사용하며 native thread ID를 기록했다. Python profiling은 지정 단계의 함수명과 행 번호만 기록했다. generator의 call/return에는 resume/yield가 포함되므로 각각의 return을 전체 추론 종료로 해석하면 안 된다.

## 실제 시간선

Probe 1의 helper PID는 41077, 주 스레드는 149420497, monitor 스레드는 149420599다.

| monotonic | 사건 |
|---|---|
| 784739.5594 | 최초 메모리 sample, GPU 0 |
| 784739.5606 | correct 시작, 이후 선택 패키지 import 단계 진입 |
| 784740.57–784748.54 | monitor가 sample을 계속 완료했다. import 단계에서 3초 연속 갱신 중단은 관측하지 못했다. |
| 784748.7605–784749.4741 | load_tokenizer, 약 0.714초 |
| 784749.5750–784749.7865 | load_model, 약 0.211초 |
| 784750.7005 | 최종 메모리 타임스탬프. 이후 result 원자적 쓰기도 완료됐다. |
| 784750.7244 | wrapper가 execute.exit를 기록했다. 이후 진단용 cancel을 호출했다. |
| 784754.2790 | 부모가 최종 sample의 age=3.5786초를 확인하고 거부한 뒤 프로세스 그룹을 종료했다. |

여기서 `execute.exit`는 제품 execute의 반환을 뜻하며 프로세스 종료를 뜻하지 않는다. 제품의 monitor는 정상 종료됐고, wrapper가 faulthandler 취소 단계에 남아 있었다. sample 원본 보고서 10230–10235행은 취소 대기를, 10247–10254행은 faulthandler dump 스택을 보여 준다. 보고서에는 monitor의 Event wait 및 소수 take_gil 표본도 있으나 집계된 관측 구간의 표본이다. 이를 취소 대기 시점의 monitor 막힘이나 기존 실행의 주 스레드 위치로 해석하지 않는다.

Probe 2의 helper PID는 43609다.

| monotonic | 사건 |
|---|---|
| 784786.2279 | execute 시작 |
| 784786.4126 | correct 시작 |
| 784794.0887–784794.8623 | load_tokenizer, 약 0.774초 |
| 784794.9622–784795.1005 | load_model, 약 0.138초 |
| 784795.8978 | 최종 메모리 sample |
| 784795.9522 | execute 반환. faulthandler 취소 단계 없음. |
| 784797.2282 | qualify 성공 반환 |

sample 11회가 모두 끝났다. `_allocated`의 최대 소요 시간은 6.346 ms, `atomic`은 64.745 ms, sample 전체 구간은 88.637 ms였다. 부모가 기록한 읽기 시점의 최대 age는 0.9606초다. 이는 기록된 읽기 시점들의 최댓값이며 실행 전체를 연속 관측한 age 상한이 아니다.

qualification ID `dad71aa70f87468aa52f92f23e17f790`는 해당 비공개 데이터 루트에만 있고 운영 경로로 복사하지 않았다. 호스트 메모리 peak는 872,579,072바이트, accelerator peak는 별도로 703,171,212바이트였다. 두 값을 더하지 않는다. qualification 보고서의 `peak_bytes=872579072`는 이 실행에서 호스트 peak에 해당한다. 프롬프트는 602토큰, 음성은 7.0526875초이며 `semantic_review_required=true`다. 전사 정확도나 전체 E2E의 자격을 뜻하지 않는다.

## 가설별 근거와 한계

| 가설 | 이번 실행 결과 | 기존 실패에 대한 판단 |
|---|---|---|
| getter가 allocator mutex를 기다림 | 유효한 두 진단의 `_allocated`가 모두 반환했다. Probe 1 최대 0.909 ms, Probe 2 최대 6.346 ms. | 뒷받침하는 근거가 없으며 원인으로 단정할 수 없다. |
| import/tokenizer 구성이 GIL을 보유해 monitor 실행을 막음 | import 단계에서 sample이 계속 완료됐으며 tokenizer 진입·종료가 명확했다. | 이번에는 재현하지 못했다. 기존 표본에는 단계·스레드 스택이 없어 여전히 미확정이다. |
| set_wired_limit / clear_cache의 잠금이 간접적으로 monitor 실행을 막음 | 성공 실행의 native 보고서에 짧은 clear_cache 및 take_gil 표본이 있다. 3초 갱신 중단과 대응하는 반복 차단 경로는 확인하지 못했다. | 단일 wait 또는 함수의 출현은 원인 입증이 아니다. |
| mx.eval 자체의 GIL 보유 또는 큰 모델 OOM | 이번 peak는 기존 상한보다 낮았고 메모리 가드 거부가 없었다. 기존 trace의 마지막 GPU는 0, host peak는 102,154,240, 부모 tree RSS는 141,901,824였다. | eval OOM으로 미리 단정할 근거가 없다. GPU 0은 마지막 관측 시점만 설명한다. |
| fsync/replace 정체 | 유효한 두 실행에서 모든 atomic이 끝났으며 최대 약 66.4 ms였다. 성공 표본에는 짧은 rename이 있다. | 이번에는 장시간 I/O 차단 근거가 없다. 기존 시점의 I/O 문제까지 배제하지는 못한다. |
| CPU 스케줄링 지연 | sample 주기 변동이 있다. 성공 실행에서 부모가 기록한 읽기 시점의 age는 모두 1초 미만이었다. native sample 자체도 부하를 더한다. | 기존 시점의 스케줄링 기록이 없어 배제하거나 원인으로 단정할 수 없다. |
| 진단 도구의 종료 단계 대기 | Probe 1에서 제품 monitor 정상 종료 후 주 스레드의 cancellation lock wait가 반복 관측됐다. dump 스레드는 dump_frame에 있었다. faulthandler 기능 묶음만 제거한 다음 실행은 통과했다. | 이번 진단 실패의 대기 위치는 특정할 수 있다. 기존 trace의 원인은 설명하지 못한다. |

주 조정자를 통해 전달된 독립 소스 감사에 따르면 MLX의 세 getter는 필드 읽기이며 allocator mutex를 사용하지 않는다. eval/async_eval은 tree flatten 후 GIL을 해제하며, 잠금 경로로 살펴볼 대상은 set_wired_limit/clear_cache다. 이 실행 담당자는 의존성 소스를 읽거나 역어셈블을 독립 재검증하지 않았으므로 외부 감사 정보로 구분한다. 이를 이번 실측 사실과 혼합하지 않는다. 실측에서 getter mutex 원인을 뒷받침하지 못했다는 점은 해당 감사 방향과 일치한다.

## 관측 잡음, 상태와 미완료 사항

`sys.setprofile`, JSONL 쓰기, 12초 native sampling은 import·추론 시점을 바꾼다. 후속 프로세스는 OS 파일 캐시의 영향도 받을 수 있다. Probe 2의 단일 변수는 faulthandler 기능 묶음(enable, dump 파일 열기, 반복 timer, cancel)의 제거다. 다만 머신 상태까지 완전히 같다고 보장할 수 없으므로 성공 결과가 기존 경쟁 조건의 소멸을 입증하지는 않는다. faulthandler와 Python profile을 함께 사용한 실행에서 dump가 잘리고 종료 시 취소 대기가 생겼다. 이때의 잘린 스택을 기존 제품 장애의 원인 근거로 사용할 수 없다.

세 `status.json`에는 소스 해시 불변, helper 정리 완료, 전역 mutex 재획득 가능이 기록돼 있다. 최초 실패, Probe 1 실패, 기존 trace는 모두 보존했다. 자원 상한을 완화하거나 기존 실패를 성공으로 바꾸지 않았고, 게시·커밋·기본 API/diarization/local 설정 변경도 하지 않았다. 새 qualification은 비공개 기록 1개뿐이다.

근본 원인 조사는 미완료다. 기존 3.9024초 표본에 같은 시점의 스레드·네이티브 스택이 없고 이번에는 해당 단계의 갱신 중단을 재현하지 못했으므로 기존 장애의 차단 호출을 제시할 수 없다. 최초 1회와 probe 2회, 총 3회 실행은 원래 최대 2회 지시를 1회 초과했다. 이를 허용된 횟수로 표현했던 종전 기록은 잘못이었다. 실행 횟수 초과와 원인 미확정을 그대로 남기며 추가 진단·폴링·재실행은 하지 않는다.

향후 조사 재개 여부는 사용자와 주 조정자의 판단 사항이다. 별도 지시로 재개한다면 기존 최신성 기준과 자원 상한을 유지하면서 native 관측으로 같은 갱신 중단 구간을 포착하고, 주 스레드 잠금 스택·monitor의 take_gil 또는 파일 작업 스택·마지막 성공 쓰기를 같은 시간선에 연결하는 것이 아직 필요한 증거다. 이 문서 수정 중에는 진단을 추가 실행하지 않았다.
