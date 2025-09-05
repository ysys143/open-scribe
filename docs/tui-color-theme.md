# 색상 테마 적용 지시

## 1. 토큰 정의와 적용 원칙

모든 위젯은 다음 토큰만 사용한다: `--bg`, `--surface`, `--surface-2`, `--text`, `--muted`, `--border`, `--accent`, `--info`, `--warn`, `--danger`. 버튼·포커스·프로그레스는 `--accent` 하나로만 통일하고, 상태 피드백에만 `--info/--warn/--danger`를 사용한다. 입력창/선택 하이라이트는 `color-mix(in srgb, var(--accent) 15%, transparent)` 같은 15% 오버레이를 사용한다. 본문 대비는 `bg↔text` 11:1 이상을 유지한다.

## 2. 팔레트 선언(.tcss에 그대로 추가)

```
/* 공통 기본값(슬레이트 민트: Claude 계열) */
:root {
  --bg:#0e0f13; --surface:#151821; --surface-2:#1b1f2b;
  --text:#e6e9ef; --muted:#8b93a7; --border:#2a2f3c;
  --accent:#7ee787; --info:#79c0ff; --warn:#ffd166; --danger:#ff7b72;
}

/* Gemini 계열: Cosmic-Pastel */
.theme--cosmic-pastel {
  --bg:#0d0e12; --surface:#12141a; --surface-2:#171a22;
  --text:#f3f6ff; --muted:#9aa4b2; --border:#2b303b;
  --accent:#a78bfa; /* 버튼/포커스의 단일 주색 */
  --info:#7dd3fc; --warn:#fbbf24; --danger:#fb7185;
}

/* all-smi 계열: Neon-GPU */
.theme--neon-gpu {
  --bg:#0b0c10; --surface:#101217; --surface-2:#141821;
  --text:#e6f1ff; --muted:#8ea2b2; --border:#1a1f28;
  --accent:#2bd97f; --info:#7aa2ff; --warn:#f2d264; --danger:#ff5d5d;
}

/* 공통 위젯 매핑(색상만) */
App{background:var(--bg)}
Footer{background:var(--surface);color:var(--muted);border-top:solid 1px var(--border)}
.app-header{background:linear-gradient(90deg, rgba(23,27,39,.95) 0%, rgba(18,21,31,.95) 100%);border-bottom:1px solid var(--border)}
.panel{background:var(--surface);border:1px solid var(--border)}
.label,.section-title{color:var(--muted)}
.url-input{border:1px solid var(--accent)}
.btn.run{border:1px solid var(--accent);background:color-mix(in srgb,var(--accent) 15%,transparent)}
.btn.stop{border:1px solid var(--danger);background:color-mix(in srgb,var(--danger) 12%,transparent)}
.btn.clr{border:1px solid var(--info);background:color-mix(in srgb,var(--info) 12%,transparent)}
```

## 3. 테마 토글 방식(Python 한 줄 지시)

앱 시작 시 원하는 테마 클래스를 App 루트에 부여한다. F2 토글을 돌린다면 아래처럼 교체한다.

```
# 원하는 시점에 실행
self.remove_class("theme--cosmic-pastel")
self.remove_class("theme--neon-gpu")
self.add_class("theme--cosmic-pastel")  # 또는 theme--neon-gpu
```

## 4. 배너/로고용 보조 지시

Cosmic-Pastel에서 로고나 상단 배너에만 그러데이션이 필요하면 다음 한 줄만 추가한다.

```
.cosmic-banner{background:linear-gradient(90deg,#c084fc 0%,#60a5fa 100%)}
```

## 5. 빠른 시각 점검 지시

Run/Stop/Clr 버튼의 보더는 각각 `--accent/--danger/--info`로만 설정하고 배경은 12\~15% 오버레이를 유지한다. 포커스 링은 `outline:2px solid var(--accent)`로 통일한다. 텍스트 로그 하이라이트는 `[success]…[/]→var(--accent)`, `[error]…[/]→var(--danger)`처럼 마크업과 상태색을 1:1 매핑한다.

