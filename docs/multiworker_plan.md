# Multi-Worker 병렬 처리 구현 계획

## 🎯 목표
대용량 오디오 파일의 전사 속도를 극대화하기 위한 동적 멀티워커 시스템 구현

## 💻 시스템 사양 고려사항
- **메모리**: 36GB 통합 RAM (Apple Silicon)
- **예상 워커 수**: 10+ whisper-cpp 동시 실행 가능
- **병목 지점**: 
  - whisper-cpp: CPU/GPU 사용량
  - OpenAI API: Rate limit 및 네트워크 대역폭

---

## 📊 동적 워커 할당 알고리즘

### 1. 기본 원칙
```python
def calculate_optimal_workers(duration_seconds: int, engine: str) -> int:
    """
    비디오 길이와 엔진 타입에 따른 최적 워커 수 계산
    
    Args:
        duration_seconds: 비디오 총 길이 (초)
        engine: 전사 엔진 타입
    
    Returns:
        최적 워커 수
    """
    MIN_WORKER = Config.MIN_WORKER  # 1
    MAX_WORKER = Config.MAX_WORKER  # 10
    
    # 기본 청크 크기 (초)
    CHUNK_SIZE = {
        'whisper-cpp': 300,      # 5분 청크
        'whisper-api': 600,      # 10분 청크  
        'gpt-4o': 600,          # 10분 청크
        'gpt-4o-mini': 600,     # 10분 청크
    }
    
    chunk_duration = CHUNK_SIZE.get(engine, 600)
    total_chunks = math.ceil(duration_seconds / chunk_duration)
    
    # 동적 워커 수 계산
    if total_chunks <= 2:
        return MIN_WORKER  # 짧은 비디오는 병렬화 불필요
    elif total_chunks <= 5:
        return min(3, MAX_WORKER)
    elif total_chunks <= 10:
        return min(5, MAX_WORKER)
    else:
        # 긴 비디오: 청크 수의 절반 또는 MAX_WORKER
        return min(max(total_chunks // 2, 5), MAX_WORKER)
```

### 2. 메모리 기반 조절
```python
def adjust_workers_by_memory(workers: int, engine: str) -> int:
    """
    시스템 메모리에 따른 워커 수 조정
    """
    import psutil
    
    available_memory_gb = psutil.virtual_memory().available / (1024**3)
    
    # 엔진별 예상 메모리 사용량 (GB)
    MEMORY_PER_WORKER = {
        'whisper-cpp': 2.5,      # large-v3 모델 기준
        'whisper-api': 0.1,      # API 호출, 메모리 사용 적음
        'gpt-4o': 0.1,
        'gpt-4o-mini': 0.1,
    }
    
    memory_per_worker = MEMORY_PER_WORKER.get(engine, 1.0)
    max_workers_by_memory = int(available_memory_gb * 0.7 / memory_per_worker)
    
    return min(workers, max_workers_by_memory)
```

---

## 🏗️ 구현 아키텍처

### 1. WorkerPool 클래스
```python
class WorkerPool:
    """병렬 처리를 위한 워커 풀 관리자"""
    
    def __init__(self, min_workers: int, max_workers: int):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.active_workers = 0
        self.completed_chunks = 0
        self.total_chunks = 0
        self.start_time = None
        
    def process_chunks(self, chunks: List[Path], processor_func: Callable) -> List[str]:
        """청크들을 병렬로 처리"""
        pass
        
    def monitor_progress(self):
        """실시간 진행률 모니터링"""
        pass
        
    def adjust_workers_dynamically(self):
        """처리 속도에 따른 동적 워커 조절"""
        pass
```

### 2. Engine별 구현

#### Whisper-cpp 병렬화
```python
class WhisperCppParallelTranscriber:
    """whisper-cpp 병렬 전사"""
    
    def transcribe_parallel(self, audio_path: str) -> str:
        # 1. 오디오 파일 청킹
        chunks = split_audio_into_chunks(audio_path, chunk_seconds=300)
        
        # 2. 최적 워커 수 계산
        duration = get_audio_duration(audio_path)
        optimal_workers = calculate_optimal_workers(duration, 'whisper-cpp')
        
        # 3. 병렬 처리
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            futures = []
            for i, chunk in enumerate(chunks):
                future = executor.submit(self.process_single_chunk, chunk, i)
                futures.append(future)
            
            # 4. 결과 수집
            results = []
            for future in as_completed(futures):
                chunk_index, text = future.result()
                results.append((chunk_index, text))
        
        # 5. 순서대로 병합
        results.sort(key=lambda x: x[0])
        return ' '.join([text for _, text in results])
```

#### OpenAI API 병렬화 (기존 개선)
```python
class OpenAIParallelTranscriber:
    """OpenAI API 병렬 전사 (Rate Limit 고려)"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(
            requests_per_minute=50,  # OpenAI tier별 조정
            tokens_per_minute=40000
        )
    
    def transcribe_parallel(self, audio_path: str) -> str:
        # Rate limit을 고려한 동적 워커 조절
        pass
```

---

## 📈 성능 모니터링

### 1. 실시간 진행률 표시
```python
class ParallelProgressBar:
    """병렬 처리 진행률 표시"""
    
    def __init__(self, total_chunks: int, num_workers: int):
        self.total = total_chunks
        self.workers = num_workers
        self.completed = 0
        self.in_progress = {}
        
    def display(self):
        """
        ┌─────────────────────────────────────────┐
        │ Transcribing with 5 workers            │
        ├─────────────────────────────────────────┤
        │ Worker 1: [████████░░] Chunk 3/10      │
        │ Worker 2: [██████░░░░] Chunk 7/10      │
        │ Worker 3: [█████████░] Chunk 2/10      │
        │ Worker 4: [███░░░░░░░] Chunk 9/10      │
        │ Worker 5: [███████░░░] Chunk 5/10      │
        ├─────────────────────────────────────────┤
        │ Overall: [██████░░░░] 24/50 chunks     │
        │ Speed: 3.2 chunks/min | ETA: 8m 15s    │
        └─────────────────────────────────────────┘
        """
        pass
```

### 2. 성능 메트릭
```python
class PerformanceMetrics:
    """성능 측정 및 최적화"""
    
    def __init__(self):
        self.chunk_times = []
        self.worker_efficiency = {}
        
    def calculate_optimal_chunk_size(self):
        """처리 시간 기반 최적 청크 크기 계산"""
        pass
        
    def suggest_worker_adjustment(self):
        """워커 수 조절 제안"""
        pass
```

---

## 🔧 구현 단계

### Phase 1: 기본 병렬화 (1주)
- [ ] WorkerPool 기본 클래스 구현
- [ ] whisper-cpp 병렬 처리 구현
- [ ] 기본 진행률 표시

### Phase 2: 동적 최적화 (1주)
- [ ] 메모리 기반 워커 조절
- [ ] 처리 속도 기반 동적 조절
- [ ] Rate limiting 구현 (OpenAI)

### Phase 3: 모니터링 및 최적화 (1주)
- [ ] 상세 진행률 표시 UI
- [ ] 성능 메트릭 수집
- [ ] 자동 최적화 알고리즘

---

## 🚀 예상 성능 향상

### 현재 (단일 워커)
- 1시간 비디오: ~15분 처리 시간
- 처리 속도: 4x

### 목표 (10 워커)
- 1시간 비디오: ~3분 처리 시간
- 처리 속도: 20x
- 실제 향상: 5-8배 (오버헤드 고려)

---

## ⚠️ 주의사항

### 1. 리소스 관리
- 메모리 부족 시 자동 워커 감소
- CPU 온도 모니터링
- 디스크 I/O 병목 회피

### 2. 에러 처리
- 개별 청크 실패 시 재시도
- 전체 실패 시 단일 워커로 폴백
- 청크 손실 방지

### 3. 품질 보증
- 청크 경계 부분 중복 처리
- 문장 중간 절단 방지
- 순서 보장

---

## 📝 환경 변수 설정

```bash
# .env
MIN_WORKER=1          # 최소 워커 수
MAX_WORKER=10         # 최대 워커 수
CHUNK_OVERLAP=5       # 청크 간 중복 (초)
WORKER_TIMEOUT=300    # 워커 타임아웃 (초)
AUTO_ADJUST=true      # 동적 조절 활성화
```

---

## 🔄 향후 개선 사항

1. **GPU 가속 활용**
   - Metal Performance Shaders 최적화
   - 멀티 GPU 지원

2. **분산 처리**
   - 네트워크 상의 다른 머신 활용
   - 클라우드 워커 통합

3. **스마트 청킹**
   - 무음 구간 기반 분할
   - 문장 경계 인식 분할

4. **캐싱 시스템**
   - 처리된 청크 캐싱
   - 중복 작업 방지