# Homebrew Tap 저장소 설정 가이드

## 개요

`homebrew-open-scribe` Tap 저장소를 생성하여 사용자들이 `brew install open-scribe`로 간편하게 설치할 수 있도록 합니다.

## 필요한 작업

### 1. GitHub에 새로운 저장소 생성

- **저장소명**: `homebrew-open-scribe`
- **설명**: "Homebrew Tap for Open-Scribe"
- **공개/비공개**: 공개
- **Template**: 기존 저장소 사용 안 함

```bash
# GitHub에서 수동으로 생성하거나 gh CLI 사용
gh repo create jaesolshin/homebrew-open-scribe --public --description "Homebrew Tap for Open-Scribe"
```

### 2. Tap 저장소 구조 설정

```
homebrew-open-scribe/
├── Formula/
│   └── open-scribe.rb        # ← Formula 파일 (open-scribe 저장소에서 복사)
├── README.md
└── .github/
    └── workflows/            # 선택사항: CI/CD
```

### 3. Formula 파일 준비

`open-scribe` 저장소의 `Formula/open-scribe.rb`를 복사:

```bash
# homebrew-open-scribe 저장소에서
mkdir -p Formula
cp ../open-scribe/Formula/open-scribe.rb Formula/

git add Formula/open-scribe.rb
git commit -m "Add open-scribe formula"
git push
```

### 4. README 작성

`homebrew-open-scribe/README.md`:

```markdown
# Homebrew Tap for Open-Scribe

Homebrew Tap providing Open-Scribe formula.

## Installation

```bash
brew tap jaesolshin/homebrew-open-scribe
brew install open-scribe
```

## Usage

```bash
scribe "https://www.youtube.com/watch?v=VIDEO_ID"
scribe "URL" --engine whisper-api --summary
```

## Update

```bash
brew upgrade open-scribe
```

## Uninstall

```bash
brew uninstall open-scribe
brew untap jaesolshin/homebrew-open-scribe
```

## About

This is the official Homebrew Tap for [Open-Scribe](https://github.com/jaesolshin/open-scribe).
```

### 5. 버전 업데이트 프로세스

새 버전 릴리스 시:

1. **open-scribe 저장소에서**
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   # GitHub Release 생성
   ```

2. **새 sha256 계산**
   ```bash
   git archive --format=tar.gz --prefix=open-scribe-0.2.0/ \
     --output=/tmp/open-scribe-v0.2.0.tar.gz 0.2.0
   shasum -a 256 /tmp/open-scribe-v0.2.0.tar.gz
   ```

3. **Tap 저장소의 Formula 업데이트**
   ```bash
   # Formula/open-scribe.rb
   version "0.2.0"
   url "...archive/refs/tags/0.2.0.tar.gz"
   sha256 "NEW_SHA256_HERE"

   git add Formula/open-scribe.rb
   git commit -m "Update formula to v0.2.0"
   git push
   ```

## 최종 사용자 입장

```bash
# 설치
brew tap jaesolshin/homebrew-open-scribe
brew install open-scribe

# 사용
scribe "https://youtube.com/watch?v=..."

# 업데이트
brew upgrade open-scribe

# 제거
brew uninstall open-scribe
brew untap jaesolshin/homebrew-open-scribe
```

## 주의사항

- Formula의 URL은 항상 **공개된 GitHub Release**를 가리켜야 함
- sha256 값은 각 버전마다 정확하게 계산해야 함
- `depends_on` 명시된 도구들은 자동으로 설치됨
  - `python@3.11`: Python 설치
  - `uv`: 의존성 관리
