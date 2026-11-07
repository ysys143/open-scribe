# 배포 계획 및 고려사항

## 1. 현재 상태 분석

### 1.1 하드코딩 문제점
- **scribe.zsh**: 경로가 하드코딩됨 (`/Users/jaesolshin/Documents/GitHub/yt-trans`)
- **배포 불가능**: 다른 사용자 환경에서 작동하지 않음
- **유지보수 어려움**: 경로 변경 시 코드 수정 필요

### 1.2 프로젝트 이름 혼재
현재 여러 이름이 혼재되어 사용되고 있음:
- **디렉토리명**: `yt-trans`
- **프로젝트명**: `Open-Scribe`
- **CLI 명령어**: `scribe`
- **설정 디렉토리**: `~/Documents/open-scribe/`
- **가상환경**: `.venv` (yt-trans)

## 2. 배포 전략 옵션

### 옵션 1: Homebrew 패키지
```bash
brew tap open-scribe/tap
brew install open-scribe
```
**장점**: 
- macOS 사용자에게 친숙
- 의존성 자동 관리
- 업데이트 간편

**단점**:
- macOS 전용
- Formula 작성 및 관리 필요

### 옵션 2: pip 패키지 (PyPI)
```bash
pip install open-scribe
```
**장점**:
- 크로스 플랫폼
- Python 생태계 표준
- 의존성 자동 설치

**단점**:
- Python 환경 필요
- 버전 충돌 가능성

### 옵션 3: 독립 실행 파일
```bash
# PyInstaller 또는 Nuitka 사용
./open-scribe-macos
./open-scribe-linux
./open-scribe.exe
```
**장점**:
- Python 설치 불필요
- 단일 파일 배포

**단점**:
- 파일 크기 큼
- 플랫폼별 빌드 필요

### 옵션 4: Docker 컨테이너
```bash
docker run -v ~/Downloads:/downloads open-scribe/cli [URL]
```
**장점**:
- 완전한 환경 격리
- 일관된 실행 환경

**단점**:
- Docker 설치 필요
- 리소스 오버헤드

## 3. 경로 문제 해결 방안

### 3.1 스크립트 위치 자동 감지
```bash
# scribe.zsh 수정안
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/main.py" ]]; then
    OPEN_SCRIBE_PATH="$SCRIPT_DIR"
else
    # 다른 위치 탐색
fi
```

### 3.2 환경 변수 활용
```bash
# .zshrc 또는 .bashrc에 추가
export OPEN_SCRIBE_HOME="$HOME/.local/share/open-scribe"
```

### 3.3 설정 파일
```yaml
# ~/.config/open-scribe/config.yaml
install_path: /usr/local/lib/open-scribe
data_path: ~/Documents/open-scribe
temp_path: /tmp/open-scribe
```

## 4. 프로젝트 이름 통일 계획

### 4.1 제안하는 명명 규칙
- **공식 프로젝트명**: Open-Scribe
- **패키지명**: `open-scribe` (pip, npm 등)
- **디렉토리명**: `open-scribe`
- **CLI 명령어**: `scribe` (짧고 간편)
- **Python 모듈명**: `open_scribe` (Python 규칙)
- **설정 디렉토리**: `~/.config/open-scribe/`
- **데이터 디렉토리**: `~/.local/share/open-scribe/`

### 4.2 변경 필요 항목
1. GitHub 저장소명: `yt-trans` → `open-scribe`
2. 디렉토리 구조 정리
3. import 경로 수정
4. 설정 파일 경로 수정
5. 문서 업데이트

## 5. 단계별 실행 계획

### Phase 1: 준비 (1주)
- [ ] 프로젝트 이름 최종 결정
- [ ] 디렉토리 구조 재설계
- [ ] 의존성 정리 (requirements.txt → pyproject.toml)

### Phase 2: 리팩토링 (2주)
- [ ] 하드코딩된 경로 제거
- [ ] 설정 시스템 구현 (config.yaml)
- [ ] 모듈 이름 통일
- [ ] 테스트 작성

### Phase 3: 패키징 (1주)
- [ ] setup.py 또는 pyproject.toml 작성
- [ ] CLI 엔트리포인트 설정
- [ ] 패키지 메타데이터 작성
- [ ] 로컬 테스트

### Phase 4: 배포 준비 (1주)
- [ ] CI/CD 파이프라인 구성
- [ ] 문서 작성 (설치 가이드)
- [ ] 버전 관리 전략 수립
- [ ] 라이선스 확정

### Phase 5: 배포 (1주)
- [ ] PyPI 등록 (옵션 2 선택 시)
- [ ] Homebrew Formula 작성 (옵션 1 선택 시)
- [ ] GitHub Releases 설정
- [ ] 사용자 피드백 수집

## 6. 설정 마이그레이션 계획

### 현재 설정 위치
```
~/Documents/open-scribe/
├── audio/
├── video/
├── transcript/
├── temp_audio/
└── transcription_jobs.db
```

### 제안하는 새 구조
```
~/.config/open-scribe/
├── config.yaml
└── credentials.json

~/.local/share/open-scribe/
├── models/
├── cache/
└── data/
    ├── audio/
    ├── video/
    ├── transcripts/
    └── database.db

~/.cache/open-scribe/
└── temp/
```

## 7. 호환성 유지 전략

### 7.1 점진적 마이그레이션
1. 새 경로 시스템 구현
2. 기존 경로 폴백 지원
3. 마이그레이션 도구 제공
4. 충분한 전환 기간 제공
5. 기존 경로 지원 종료

### 7.2 버전 관리
- **v1.x**: 현재 구조 유지 (yt-trans)
- **v2.0**: 새 구조 도입 (open-scribe), 하위 호환성 유지
- **v3.0**: 기존 구조 지원 종료

## 8. 위험 요소 및 대응 방안

### 8.1 위험 요소
- 기존 사용자 워크플로우 중단
- 데이터 손실 가능성
- 의존성 충돌
- 플랫폼별 호환성 문제

### 8.2 대응 방안
- 자동 백업 기능 구현
- 마이그레이션 가이드 제공
- 롤백 기능 제공
- 베타 테스트 프로그램 운영

## 9. 성공 지표

- [ ] 3개 이상 플랫폼 지원 (macOS, Linux, Windows)
- [ ] 설치 시간 5분 이내
- [ ] 기존 사용자 100% 마이그레이션 성공
- [ ] 월간 활성 사용자 100명 이상
- [ ] 커뮤니티 기여자 5명 이상

## 10. 참고 자료

- [Python Packaging User Guide](https://packaging.python.org/)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Semantic Versioning](https://semver.org/)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)