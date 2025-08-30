from openai import OpenAI
from dotenv import load_dotenv
import os
import subprocess
import tempfile

load_dotenv()

# OpenAI 클라이언트
client = OpenAI()

def format_timestamp(seconds):
    """Convert seconds to MM:SS or HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def timestamp_to_seconds(timestamp_str):
    """Convert timestamp string (HH:MM:SS.mmm) to seconds"""
    parts = timestamp_str.split(':')
    if len(parts) == 3:
        hours, minutes, seconds = parts
        seconds_parts = seconds.split('.')
        secs = float(seconds_parts[0])
        if len(seconds_parts) > 1:
            secs += float('0.' + seconds_parts[1])
        return int(hours) * 3600 + int(minutes) * 60 + secs
    return 0

def transcribe_with_openai(audio_path, stream=False, return_timestamps=False):
    """OpenAI API를 사용한 전사 - Whisper 모델 사용
    
    Args:
        audio_path: 오디오 파일 경로
        stream: 스트리밍 출력 여부
        return_timestamps: 타임스탬프 정보 반환 여부
    
    Returns:
        str or tuple: 텍스트만 반환하거나 (text, timestamps) 튜플 반환
    """
    print(f"[OpenAI] Processing: {audio_path}")
    
    # Progress indicator for non-streaming mode
    if not stream:
        import threading
        import itertools
        import sys
        import time
        
        stop_spinner = threading.Event()
        def show_progress():
            spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
            while not stop_spinner.is_set():
                sys.stdout.write(f'\r[OpenAI] Transcribing {next(spinner)} ')
                sys.stdout.flush()
                time.sleep(0.1)
        
        spinner_thread = threading.Thread(target=show_progress)
        spinner_thread.daemon = True
        spinner_thread.start()
    
    try:
        with open(audio_path, "rb") as audio_file:
            # OpenAI's transcription API uses whisper-1 model
            # Always get verbose_json for timestamps
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
            
            if stream:
                print("[OpenAI] Streaming transcription...")
                print("-" * 60)
                
                # If we got segments with timestamps, display them progressively
                if hasattr(transcription, 'segments') and transcription.segments:
                    full_text = []
                    timestamps = []
                    for segment in transcription.segments:
                        # Access segment attributes and stream text
                        text = segment.text if hasattr(segment, 'text') else str(segment)
                        start_time = segment.start if hasattr(segment, 'start') else 0
                        end_time = segment.end if hasattr(segment, 'end') else 0
                        
                        # Format with timestamp for display
                        timestamp_str = f"[{format_timestamp(start_time)}]"  
                        print(f"{timestamp_str} {text.strip()}", flush=True)
                        
                        full_text.append(text)
                        timestamps.append({
                            'start': start_time,
                            'end': end_time,
                            'text': text.strip()
                        })
                        # 약간의 지연을 주어 스트리밍 효과
                        import time
                        time.sleep(0.05)
                    
                    print("-" * 60)
                    print("[OpenAI] Streaming complete")
                    
                    # Format text with timestamps for regular output
                    formatted_text = []
                    for ts in timestamps:
                        formatted_text.append(f"[{format_timestamp(ts['start'])}] {ts['text']}")
                    
                    if return_timestamps:
                        # Return formatted text with timestamps included
                        return '\n'.join(formatted_text)
                    else:
                        # Return plain text without timestamps
                        return ' '.join(full_text)
                else:
                    # 세그먼트가 없으면 전체 텍스트를 단어 단위로 스트리밍
                    text = transcription.text if hasattr(transcription, 'text') else str(transcription)
                    words = text.split()
                    
                    # 단어 단위로 출력 (스트리밍 시뮬레이션)
                    current_line = []
                    for i, word in enumerate(words):
                        current_line.append(word)
                        
                        # 10단어마다 줄바꿈
                        if (i + 1) % 10 == 0:
                            print(' '.join(current_line), flush=True)
                            current_line = []
                        
                        # 스트리밍 효과를 위한 짧은 지연
                        import time
                        time.sleep(0.01)
                    
                    # 남은 단어 출력
                    if current_line:
                        print(' '.join(current_line), flush=True)
                    
                    print("-" * 60)
                    print("[OpenAI] Streaming complete")
                    return text
            else:
                # Stop progress spinner for non-streaming mode
                if not stream:
                    stop_spinner.set()
                    spinner_thread.join()
                    sys.stdout.write('\r[OpenAI] Transcription completed' + ' ' * 20 + '\n')
                    sys.stdout.flush()
                else:
                    print(f"[OpenAI] Transcription completed")
                
                # Extract text and timestamps from verbose_json
                if hasattr(transcription, 'segments') and transcription.segments:
                    timestamps = []
                    formatted_lines = []
                    for segment in transcription.segments:
                        start_time = segment.start if hasattr(segment, 'start') else 0
                        text = segment.text if hasattr(segment, 'text') else ''
                        timestamps.append({
                            'start': start_time,
                            'end': segment.end if hasattr(segment, 'end') else 0,
                            'text': text.strip()
                        })
                        formatted_lines.append(f"[{format_timestamp(start_time)}] {text.strip()}")
                    
                    # Return formatted text based on timestamp preference
                    if return_timestamps:
                        return '\n'.join(formatted_lines)
                    else:
                        # Without timestamps, return plain text
                        return ' '.join([ts['text'] for ts in timestamps])
                else:
                    # Fallback if no segments
                    text = transcription.text if hasattr(transcription, 'text') else str(transcription)
                    return text
    except Exception as e:
        if not stream and 'stop_spinner' in locals():
            stop_spinner.set()
            if 'spinner_thread' in locals():
                spinner_thread.join()
        print(f"[OpenAI] Error: {e}")
        raise

def transcribe_with_whisper_api(audio_path):
    """OpenAI Whisper API를 사용한 전사"""
    print(f"[Whisper API] Processing: {audio_path}")
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        print(f"[Whisper API] Result: {transcription}")
        return transcription

def transcribe_with_whisper_cpp(audio_path, model_path=None, language="auto", stream=False, return_timestamps=False):
    """whisper.cpp를 사용한 로컬 전사
    
    Args:
        audio_path: 전사할 오디오 파일 경로
        model_path: whisper 모델 경로 (기본값: base 모델)
        language: 언어 코드 (auto, en, ko 등)
        stream: 스트리밍 출력 여부
        return_timestamps: 타임스탬프 정보 반환 여부
    """
    # 기본 모델 경로 설정
    if model_path is None:
        model_path = "/Users/jaesolshin/Documents/GitHub/yt-trans/whisper.cpp/models/ggml-base.bin"
    
    # whisper.cpp 실행 파일 경로
    whisper_exe = "/Users/jaesolshin/Documents/GitHub/yt-trans/whisper.cpp/build/bin/whisper-cli"
    
    # MP3를 WAV로 변환 (whisper.cpp는 WAV 포맷 선호)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        wav_path = tmp_wav.name
        
    try:
        # ffmpeg로 MP3를 16kHz WAV로 변환
        convert_cmd = [
            "ffmpeg", "-i", audio_path, 
            "-ar", "16000",  # 16kHz 샘플링
            "-ac", "1",      # 모노
            "-c:a", "pcm_s16le",  # 16-bit PCM
            wav_path,
            "-y"  # 덮어쓰기
        ]
        subprocess.run(convert_cmd, check=True, capture_output=True, text=True)
        
        # whisper.cpp 명령어 구성
        cmd = [
            whisper_exe,
            "-m", model_path,
            "-f", wav_path,
        ]
        
        # 스트리밍 모드에서는 실시간 출력
        if stream:
            # 표준 출력으로 텍스트만 출력
            cmd.extend([
                "--no-prints",       # 시스템 메시지 최소화
            ])
        else:
            cmd.extend([
                "--print-colors",
                "--print-progress",
            ])
        
        # 언어 옵션 추가
        if language != "auto":
            cmd.extend(["-l", language])
        
        # 출력 형식 옵션
        cmd.extend([
            "-otxt",  # 텍스트 출력
            "-ovtt",  # VTT 자막 출력
        ])
        
        print(f"[whisper.cpp] Processing: {audio_path}")
        print(f"[whisper.cpp] Using model: {model_path}")
        
        # whisper.cpp 실행
        if stream:
            # 스트리밍 모드: 실시간으로 텍스트 출력
            import sys
            import select
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            transcription_lines = []
            print("[whisper.cpp] Streaming transcription...")
            print("-" * 60)
            
            current_text = []
            timestamps = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                    
                if output:
                    line = output.strip()
                    
                    # 시스템 메시지 필터링
                    if any(skip in line.lower() for skip in ['ggml', 'metal', 'loading', 'model', 'system', 'whisper_', 'main:']):
                        continue
                    
                    # 타임코드가 있는 라인 처리
                    if "[" in line and "-->" in line and "]" in line:
                        # 타임코드와 텍스트 추출
                        import re
                        timestamp_match = re.match(r'\[(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\]\s*(.*)', line)
                        if timestamp_match:
                            start_str, end_str, text = timestamp_match.groups()
                            # 특수 토큰 필터링
                            text = re.sub(r'\[_EOT_\]|\[BLANK_AUDIO\]|\[Music\]|\[_BEG_\]', '', text).strip()
                            if text and not text.startswith('['):
                                # Convert timestamp to seconds
                                start_seconds = timestamp_to_seconds(start_str)
                                # Format timestamp for display
                                timestamp_display = format_timestamp(start_seconds)
                                print(f"[{timestamp_display}] {text}", flush=True)
                                current_text.append(text)
                                timestamps.append({
                                    'start': start_seconds,
                                    'end': timestamp_to_seconds(end_str),
                                    'text': text
                                })
                    # 일반 텍스트 라인
                    elif line and not line.startswith("[") and not "progress" in line.lower():
                        # ANSI 색상 코드 및 특수 토큰 제거
                        import re
                        clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                        clean_line = re.sub(r'\[_EOT_\]|\[BLANK_AUDIO\]|\[Music\]|\[_BEG_\]', '', clean_line).strip()
                        # 파일 경로나 시스템 메시지 필터링
                        if clean_line and not clean_line.startswith('output_') and not '.wav' in clean_line:
                            print(clean_line, flush=True)
                            current_text.append(clean_line)
            
            process.wait()
            result = process
            transcription_lines = current_text
            print("-" * 60)
            print("[whisper.cpp] Streaming complete")
            
            # Return formatted text based on timestamp preference
            if return_timestamps and timestamps:
                # Format text with timestamps
                formatted_text = []
                for ts in timestamps:
                    formatted_text.append(f"[{format_timestamp(ts['start'])}] {ts['text']}")
                return '\n'.join(formatted_text)
            elif timestamps and not return_timestamps:
                # Without timestamp flag, return plain text even if we have timestamps
                return ' '.join(current_text) if current_text else None
            else:
                return ' '.join(current_text) if current_text else None
        else:
            # 일반 모드
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 출력 파일 읽기 (whisper.cpp는 입력 파일명.txt로 저장)
            txt_output = wav_path + ".txt"
            if os.path.exists(txt_output):
                with open(txt_output, 'r', encoding='utf-8') as f:
                    transcription = f.read().strip()
                print(f"[whisper.cpp] Result: {transcription}")
                
                # For non-streaming mode, parse VTT file for timestamps before deletion
                vtt_output = wav_path + ".vtt"
                formatted_transcription = transcription
                if return_timestamps and os.path.exists(vtt_output):
                    timestamps = []
                    with open(vtt_output, 'r', encoding='utf-8') as f:
                        vtt_content = f.read()
                        # Parse VTT timestamps
                        import re
                        pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\n(.+?)(?=\n\n|$)'
                        matches = re.findall(pattern, vtt_content, re.DOTALL)
                        for start_str, end_str, text in matches:
                            timestamps.append({
                                'start': timestamp_to_seconds(start_str),
                                'end': timestamp_to_seconds(end_str),
                                'text': text.strip()
                            })
                    
                    if timestamps:
                        # Format text with timestamps
                        formatted_text = []
                        for ts in timestamps:
                            formatted_text.append(f"[{format_timestamp(ts['start'])}] {ts['text']}")
                        formatted_transcription = '\n'.join(formatted_text)
                
                # Clean up temp files
                os.remove(txt_output)
                if os.path.exists(vtt_output):
                    os.remove(vtt_output)
                
                return formatted_transcription
            else:
                print(f"[whisper.cpp] Error: Output file not found")
                print(f"[whisper.cpp] stderr: {result.stderr}")
        else:
            print(f"[whisper.cpp] Error: {result.stderr}")
            
    finally:
        # 임시 WAV 파일 삭제
        if os.path.exists(wav_path):
            os.remove(wav_path)
    
    return None

if __name__ == "__main__":
    test_file = "/Users/jaesolshin/Documents/GitHub/yt-trans/temp_audio/Abstract vector spaces ｜ Chapter 16, Essence of linear algebra [TgKwz5Ikpc8].mp3"

    print("=== OpenAI GPT-4o-mini Transcription ===")
    transcribe_with_openai(test_file)

    print("\n=== OpenAI Whisper API Transcription ===")
    transcribe_with_whisper_api(test_file)
    
    print("\n=== whisper.cpp Local Transcription ===")
    transcribe_with_whisper_cpp(test_file)
