#!/bin/zsh
# Open-Scribe: YouTube Video Transcription Tool
# Author: 재솔님

# 프로젝트 경로 설정 (필요시 수정)
OPEN_SCRIBE_PATH="/Users/jaesolshin/Documents/GitHub/yt-trans"

# 가상환경 활성화 함수
function activate_open_scribe() {
    if [[ -f "$OPEN_SCRIBE_PATH/.venv/bin/activate" ]]; then
        source "$OPEN_SCRIBE_PATH/.venv/bin/activate"
    else
        echo "❌ 가상환경을 찾을 수 없습니다: $OPEN_SCRIBE_PATH/.venv"
        return 1
    fi
}

# 메인 전사 함수
function scribe() {
    # 도움말 표시
    if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        echo "🎥 scribe: YouTube 비디오를 전사하는 도구"
        echo ""
        echo "사용법:"
        echo "  scribe <YouTube_URL> [옵션들...]"
        echo ""
        echo "전사 엔진 옵션:"
        echo "  --engine <엔진>        전사 엔진 선택 [기본값: gpt-4o-mini-transcribe]"
        echo "                         gpt-4o-transcribe, gpt-4o-mini-transcribe,"
        echo "                         whisper-api, whisper-cpp, youtube-transcript-api"
        echo ""
        echo "기능 옵션:"
        echo "  --summary              AI 요약 생성 (GPT-4o-mini)"
        echo "  --verbose              상세 요약 출력"
        echo "  --video                비디오 파일 다운로드"
        echo "  --audio                오디오 파일 보관"
        echo "  --srt                  SRT 자막 파일 생성"
        echo "  --translate            한국어로 번역"
        echo "  --timestamp            타임코드 포함"
        echo "  --progress             진행상황 표시"
        echo ""
        echo "출력 옵션:"
        echo "  --stream               실시간 출력 [기본값]"
        echo "  --no-stream            실시간 출력 비활성화"
        echo "  --downloads            Downloads 폴더에 복사 [기본값]"
        echo "  --no-downloads         Downloads 폴더 복사 비활성화"
        echo "  --filename <이름>      저장 파일명 지정"
        echo ""
        echo "기타 옵션:"
        echo "  --force                기존 파일 덮어쓰기"
        echo ""
        echo "예시들:"
        echo "  scribe 'https://youtu.be/VIDEO_ID'"
        echo "  scribe 'https://youtu.be/VIDEO_ID' --engine whisper-cpp --summary --srt"
        echo "  scribe 'https://youtu.be/VIDEO_ID' --video --translate --progress"
        echo "  scribe 'https://youtu.be/VIDEO_ID' --engine youtube --filename my_video"
        return 0
    fi

    # 입력 URL 확인
    if [[ -z "$1" ]]; then
        echo "❌ 오류: YouTube URL을 지정해주세요."
        echo "사용법: scribe <YouTube_URL> [옵션들...]"
        return 1
    fi

    local youtube_url="$1"
    shift

    # URL 유효성 기본 확인
    if [[ ! "$youtube_url" =~ ^https?://(www\.)?(youtube\.com|youtu\.be)/ ]]; then
        echo "❌ 오류: 유효한 YouTube URL이 아닙니다: $youtube_url"
        return 1
    fi

    # 옵션 파싱
    local engine="gpt-4o-mini-transcribe"
    local summary=false
    local verbose=false
    local video=false
    local audio=false
    local srt=false
    local translate=false
    local timestamp=false
    local progress=false
    local stream=true
    local downloads=true
    local filename=""
    local force=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --engine)
                engine="$2"
                shift 2
                ;;
            --summary)
                summary=true
                shift
                ;;
            --verbose)
                verbose=true
                shift
                ;;
            --video)
                video=true
                shift
                ;;
            --audio)
                audio=true
                shift
                ;;
            --srt)
                srt=true
                shift
                ;;
            --translate)
                translate=true
                shift
                ;;
            --timestamp)
                timestamp=true
                shift
                ;;
            --progress)
                progress=true
                shift
                ;;
            --stream)
                stream=true
                shift
                ;;
            --no-stream)
                stream=false
                shift
                ;;
            --downloads)
                downloads=true
                shift
                ;;
            --no-downloads)
                downloads=false
                shift
                ;;
            --filename)
                filename="$2"
                shift 2
                ;;
            --force)
                force=true
                shift
                ;;
            *)
                echo "❌ 오류: 알 수 없는 옵션: $1"
                echo "도움말: scribe --help"
                return 1
                ;;
        esac
    done

    # 가상환경 활성화
    activate_open_scribe
    if [[ $? -ne 0 ]]; then
        return 1
    fi

    # 작업 디렉토리 변경
    local original_dir=$(pwd)
    cd "$OPEN_SCRIBE_PATH"

    # 명령어 구성
    local cmd="python main.py \"$youtube_url\" --engine $engine"

    # 기능 옵션들
    if [[ "$summary" == true ]]; then
        cmd="$cmd --summary"
    fi

    if [[ "$verbose" == true ]]; then
        cmd="$cmd --verbose"
    fi

    if [[ "$video" == true ]]; then
        cmd="$cmd --video"
    fi

    if [[ "$audio" == true ]]; then
        cmd="$cmd --audio"
    fi

    if [[ "$srt" == true ]]; then
        cmd="$cmd --srt"
    fi

    if [[ "$translate" == true ]]; then
        cmd="$cmd --translate"
    fi

    if [[ "$timestamp" == true ]]; then
        cmd="$cmd --timestamp"
    fi

    if [[ "$progress" == true ]]; then
        cmd="$cmd --progress"
    fi

    if [[ "$stream" == false ]]; then
        cmd="$cmd --no-stream"
    fi

    if [[ "$downloads" == false ]]; then
        cmd="$cmd --no-downloads"
    fi

    if [[ -n "$filename" ]]; then
        cmd="$cmd --filename \"$filename\""
    fi

    if [[ "$force" == true ]]; then
        cmd="$cmd --force"
    fi

    # 명령어 실행
    echo "🎥 전사 시작: $youtube_url"
    echo "엔진: $engine"
    eval $cmd

    local result=$?

    # 작업 디렉토리 복원
    cd "$original_dir"

    if [[ $result -eq 0 ]]; then
        echo "✅ 전사 완료!"

        # 생성된 파일 정보 표시
        local transcript_dir="$HOME/Documents/open-scribe/transcript"
        if [[ -d "$transcript_dir" ]]; then
            echo "📝 전사 결과가 저장된 디렉토리: $transcript_dir"
            local latest_file=$(ls -t "$transcript_dir"/*.txt 2>/dev/null | head -1)
            if [[ -n "$latest_file" ]]; then
                echo "📄 최근 전사 파일: $(basename "$latest_file") ($(stat -f%z "$latest_file" 2>/dev/null || stat -c%s "$latest_file" 2>/dev/null || echo "크기 확인 불가") bytes)"
            fi
        fi
    else
        echo "❌ 전사 실패"
    fi

    return $result
}

# 별칭 등록 (선택사항)
alias scribe-yt="scribe"
alias scribe-transcribe="scribe"

# 자동 완성 함수 (선택사항)
function _scribe_complete() {
    local -a engines
    engines=('gpt-4o-transcribe' 'gpt-4o-mini-transcribe' 'whisper-api' 'whisper-cpp' 'youtube-transcript-api')

    _arguments \
        '1:YouTube URL: ' \
        '--engine[전사 엔진 선택]:엔진:('${engines[@]}')' \
        '--summary[AI 요약 생성]' \
        '--verbose[상세 요약 출력]' \
        '--video[비디오 파일 다운로드]' \
        '--audio[오디오 파일 보관]' \
        '--srt[SRT 자막 파일 생성]' \
        '--translate[한국어로 번역]' \
        '--timestamp[타임코드 포함]' \
        '--progress[진행상황 표시]' \
        '--stream[실시간 출력]' \
        '--no-stream[실시간 출력 비활성화]' \
        '--downloads[Downloads 폴더에 복사]' \
        '--no-downloads[Downloads 폴더 복사 비활성화]' \
        '--filename[저장 파일명 지정]:파일명:' \
        '--force[기존 파일 덮어쓰기]' \
        '--help[도움말 표시]'
}

# 자동 완성 등록 (zsh에서만 작동)
if [[ -n "$ZSH_VERSION" ]]; then
    compdef _scribe_complete scribe
fi

# 함수 내보내기
export -f scribe activate_open_scribe
