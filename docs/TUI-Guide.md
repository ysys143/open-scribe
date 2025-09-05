# TUI 개발 가이드

## 개요

YouTube 전사 도구에 TUI(Text User Interface) 기능을 추가하는 통합 가이드입니다.

## 현재 상태 (2025-09-03)

### ✅ 완료된 기능
- **Phase 1**: 기본 프레임워크 (메인 메뉴, 기본 구조)
- **Phase 2**: API 키 관리, 데이터베이스 관리 화면

### 🔧 실행 방법
```bash
# TUI 실행
python tui.py

# 가상환경 사용 시
source .venv/bin/activate && python tui.py
```

### 📁 파일 구조
```
src/tui/
├── __init__.py              # TUI 패키지 초기화
├── app.py                   # 메인 애플리케이션
├── screens/                 # 화면 모듈들
│   ├── __init__.py
│   ├── base.py             # 기본 화면 클래스
│   ├── main_menu.py        # 메인 메뉴
│   ├── api_keys.py         # API 키 관리
│   └── database.py         # 데이터베이스 관리
├── utils/                   # 유틸리티 모듈들
│   ├── __init__.py
│   ├── config_manager.py   # 설정 관리
│   └── db_manager.py       # 데이터베이스 관리
├── widgets/                 # 커스텀 위젯들 (미래 확장)
│   └── __init__.py
└── themes/                  # 테마 파일들 (미래 확장)
    └── __init__.py

tui.py                       # TUI 진입점
```

## 사용 가능한 기능

### 1. 메인 메뉴
- **키보드 단축키**: Ctrl+C (종료), F1 (도움말), F2 (테마 변경), ESC (뒤로가기)
- **메뉴 항목**: 전사 작업, 데이터베이스 관리, API 키 관리, 설정, 모니터링, 도움말, 종료

### 2. API 키 관리 
- **기능**: OpenAI API 키 조회, 추가, 편집, 검증
- **특징**: 키 마스킹 표시, .env 파일 자동 업데이트, 비동기 키 검증
- **사용법**: 메인 메뉴에서 "🔑 API 키 관리" 선택

### 3. 데이터베이스 관리
- **기능**: 전사 히스토리 조회, 검색, 필터링, CSV 내보내기
- **탭 구성**: 히스토리, 통계, 관리
- **특징**: 실시간 통계, 오래된 작업 정리
- **사용법**: 메인 메뉴에서 "📊 데이터베이스 관리" 선택

## 개발 정보

### 기술 스택
- **UI 프레임워크**: Textual (최신 Python TUI)
- **스타일링**: 인라인 CSS (다크 테마)
- **비동기 처리**: `@work` 데코레이터
- **데이터**: 기존 SQLite DB, .env 파일 연동

### 핵심 클래스
1. **YouTubeTranscriberTUI**: 메인 앱 클래스
2. **ConfigManager**: .env 기반 설정 관리
3. **DatabaseManager**: 데이터베이스 작업 관리
4. **각 Screen 클래스**: 화면별 UI 및 로직

### 설정 파일 연동
- **.env 파일**: API 키 및 환경변수 관리 (기존 프로젝트와 호환)
- **tui_config.json**: TUI 전용 메타데이터 (자동 생성)

## 다음 단계 (Phase 3)

### 우선순위
1. **전사 작업 화면**: URL 입력, 엔진 선택, 옵션 설정
2. **CLI 통합**: 기존 전사 로직과 TUI 연동
3. **진행률 표시**: 실시간 다운로드/전사 진행률
4. **로그 스트리밍**: 실시간 로그 출력

### 예상 작업
```python
# 구현 예정 파일들
src/tui/screens/transcribe.py     # 전사 화면
src/tui/widgets/progress.py       # 진행률 위젯
src/tui/screens/settings.py       # 설정 화면
src/tui/screens/monitor.py        # 모니터링 화면
```

## 문제 해결

### 패키지 설치 오류
```bash
# 가상환경 확인
source .venv/bin/activate
uv pip install textual rich

# 패키지 확인
python -c "import textual; print('OK')"
```

### 실행 오류
```bash
# 경로 확인
pwd  # /path/to/yt-trans 이어야 함

# Python 경로 확인
which python
```

### 화면 깨짐
- 터미널 크기를 충분히 크게 설정 (최소 80x24)
- ESC 키로 이전 화면으로 이동
- Ctrl+C로 안전 종료

## 개발 참고사항

### 코딩 규칙
- **Screen 클래스**: 각 화면은 별도 파일로 분리
- **CSS**: 인라인 CSS 사용 (배포 단순화)
- **비동기**: 긴 작업은 `@work` 데코레이터 사용
- **에러 처리**: `show_error()`, `show_success()` 메서드 활용

### 테스트
```bash
# 기본 실행 테스트
python tui.py

# 개발 모드 (CSS 자동 재로드) - textual-dev 설치 후
textual run --dev src.tui.app:YouTubeTranscriberTUI
```

---

이 가이드는 TUI 개발의 모든 정보를 통합한 단일 참고 문서입니다.