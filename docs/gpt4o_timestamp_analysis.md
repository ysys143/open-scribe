# GPT-4o-mini-transcribe Timestamp Support Analysis

## Executive Summary
After deep investigation, **gpt-4o-mini-transcribe does NOT natively support timestamps** in the same way whisper-1 does with `verbose_json`. However, there are several creative workarounds to achieve timestamp functionality.

## Current State (2025)

### Model Capabilities
- **whisper-1**: Supports `verbose_json` format with segment-level timestamps
- **gpt-4o-transcribe**: Only supports `text` and `json` formats (no timestamps)  
- **gpt-4o-mini-transcribe**: Only supports `text` and `json` formats (no timestamps)

### Response Format Support Matrix

| Model | text | json | verbose_json | srt | vtt |
|-------|------|------|--------------|-----|-----|
| whisper-1 | ✅ | ✅ | ✅ | ✅ | ✅ |
| gpt-4o-transcribe | ✅ | ✅ | ❌ | ❓ | ❓ |
| gpt-4o-mini-transcribe | ✅ | ✅ | ❌ | ❓ | ❓ |

❓ = Unconfirmed, needs testing

## Potential Solutions for Timestamps with GPT-4o-mini

### Solution 1: SRT/VTT Format Parsing
**Hypothesis**: GPT-4o models might support SRT/VTT subtitle formats
```python
response = client.audio.transcriptions.create(
    model="gpt-4o-mini-transcribe",
    file=audio_file,
    response_format="srt"  # or "vtt"
)
```
**Pros**: 
- Native timestamp support if it works
- Standard subtitle format

**Cons**: 
- May not be supported
- Requires parsing subtitle format

### Solution 2: Audio Chunking with Time Tracking
**Implementation**: Split audio into fixed chunks and track offsets
```python
def transcribe_with_timestamps(audio_path, chunk_duration=10):
    chunks = split_audio_into_chunks(audio_path, chunk_duration)
    results = []
    
    for i, chunk_path in enumerate(chunks):
        start_time = i * chunk_duration
        text = transcribe_chunk(chunk_path)  # Using gpt-4o-mini
        results.append({
            'start': start_time,
            'end': start_time + chunk_duration,
            'text': text
        })
    
    return results
```
**Pros**: 
- Works with any transcription model
- Controllable timestamp granularity

**Cons**: 
- Less accurate timestamps
- More API calls (higher cost)
- Requires audio processing

### Solution 3: Hybrid Whisper + GPT-4o Approach
**Implementation**: Use whisper-1 for timestamps, gpt-4o-mini for quality
```python
def hybrid_transcribe(audio_path):
    # Get timestamps from whisper
    whisper_response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json"
    )
    timestamps = [(seg.start, seg.end) for seg in whisper_response.segments]
    
    # Get high-quality text from gpt-4o-mini
    gpt_response = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=audio_file,
        response_format="text"
    )
    
    # Align texts using dynamic programming or heuristics
    aligned_segments = align_texts(whisper_response.text, gpt_response, timestamps)
    return aligned_segments
```
**Pros**: 
- Best of both worlds (timestamps + quality)
- Single audio file processing

**Cons**: 
- Two API calls (double cost)
- Complex text alignment needed
- Potential misalignment issues

### Solution 4: Real-time WebSocket API
**Implementation**: Use the new real-time transcription API
```python
import websocket
import json

ws_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-transcribe"

def on_message(ws, message):
    data = json.loads(message)
    if data['type'] == 'transcription':
        timestamp = data.get('timestamp')  # If provided
        text = data['text']
        print(f"[{timestamp}] {text}")

ws = websocket.WebSocketApp(ws_url, on_message=on_message)
ws.run_forever()
```
**Pros**: 
- Real-time timestamps
- Low latency
- Streaming capability

**Cons**: 
- More complex implementation
- Requires WebSocket handling
- May not work with pre-recorded files

### Solution 5: Speech Activity Detection + Chunking
**Implementation**: Use VAD to detect speech segments, then transcribe
```python
import webrtcvad

def vad_transcribe(audio_path):
    vad = webrtcvad.Vad()
    segments = detect_speech_segments(audio_path, vad)
    
    results = []
    for start, end in segments:
        chunk = extract_audio_segment(audio_path, start, end)
        text = transcribe_chunk(chunk)  # Using gpt-4o-mini
        results.append({
            'start': start,
            'end': end,
            'text': text
        })
    
    return results
```
**Pros**: 
- Natural speech boundaries
- Accurate timestamps
- Efficient (only transcribes speech)

**Cons**: 
- Requires additional libraries
- More complex preprocessing
- Multiple API calls

## Recommended Approach

For the yt-trans project, I recommend **Solution 2 (Audio Chunking)** as the primary approach with **Solution 3 (Hybrid)** as a fallback option:

### Implementation Plan

1. **Detect when timestamps are requested with gpt-4o-mini**:
```python
if return_timestamps and self.model_name in ["gpt-4o-transcribe", "gpt-4o-mini-transcribe"]:
    # Use chunking approach
    return self.transcribe_with_chunked_timestamps(audio_path)
```

2. **Implement chunked transcription with timestamps**:
```python
def transcribe_with_chunked_timestamps(self, audio_path):
    # Use existing chunking infrastructure
    chunk_duration = 30  # seconds
    chunks = split_audio_into_chunks(audio_path, chunk_duration)
    
    results = []
    for i, chunk_path in enumerate(chunks):
        start_time = i * chunk_duration
        
        # Transcribe chunk
        text = self.transcribe_single_chunk(chunk_path, i)
        
        # Format with timestamp
        timestamp = format_timestamp(start_time)
        results.append(f"[{timestamp}] {text}")
    
    return '\n'.join(results)
```

3. **Add configuration option for timestamp method**:
```python
# In config.py
TIMESTAMP_METHOD = os.getenv('OPEN_SCRIBE_TIMESTAMP_METHOD', 'chunked')
# Options: 'chunked', 'hybrid', 'vad', 'none'
```

## Testing Requirements

The `test_gpt4o_timestamp.py` script will verify:
1. Which response formats are actually supported
2. Whether SRT/VTT formats work
3. Performance comparison between methods
4. Accuracy of timestamp alignment

## Conclusion

While gpt-4o-mini-transcribe doesn't natively support timestamps like whisper-1, we can achieve similar functionality through:
1. **Audio chunking** (simplest, most reliable)
2. **Hybrid approach** (best quality but higher cost)
3. **Real-time API** (for streaming scenarios)

The chunking approach leverages existing infrastructure in the codebase and provides reasonable timestamp accuracy while maintaining the superior transcription quality of gpt-4o-mini.