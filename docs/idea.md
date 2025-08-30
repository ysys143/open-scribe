
명령어 입력.

```sh
trans [url] 
```
### 옵션
- 옵션으로 'gpt-4o-transcribe' 'gpt-4o-mini-transcribe' 'whisper' 'youtube-transcript-api' 중 하나를 스크롤로 선택할 수 있음. 디폴트 값은 'gpt-4o-mini-transcribe'. 'gpt-4o-transcribe'에는 'high', 'gpt-4o-mini-transcribe'에는 'medium', 'whishper'에는 'low', 'youtube-transcript-api'는 'youtube'라는 alias가 있음.

- 옵션으로 stream 여부를 선택할 수 있음. 디폴트는 True.
- 옵션으로 downloads 폴더 익스포트 여부를 선택할 수 있음. 디폴트는 True.
- 옵션으로 summary 여부를 선택할 수 있음. verbose 옵션으로 summary 수준을 조절할 수 있음.
- 옵션으로 audio 다운로드 여부를 선택할 수 있음.
- 옵션으로 video 다운로드 여부를 선택할 수 있음.
- 옵션으로 srt 자막 생성 여부를 선택할 수 있음.
- 옵션으로 한국어 번역 자막 생성 여부를 선택할 수 있음.
- help 포함


## 'youtube-transcript-api' 가 선택된 경우

pypi에 등록된 youtube-transcript-api를 이용해 전사한다. 
audio, video, srt 모두 False를 디폴트로 한다.

## 'youtube-transcript-api' 가 선택되지 않은 경우
- audio는 True가 강제된다.
- yt-dlp를 실행하여 mp3를 "~/Documents/GitHub/yt-trans/audio" 위치에 다운.


```sh
yt-dlp [url] -t mp3 
```

- OpenAI API를 통해 해당 음원 파일을 전사함.

- stream=True 라면 전사하는 과정에서 stream을 출력함.

- 전사한 결과물은 '~/Documents/GitHub/yt-trans/transcript'에 .txt　형식으로 저장.
  
- downloads=True 일 경우, '~/Downloads'에도 동일한 .txt　파일을 저장.

- summary=True일 경우, gpt-5로 요약한 결과물을 출력. 
  요약내용은 verbose=True일 경우, 1) 3줄 이내의 요약 2) 시간대별 내용 정리 2) 내용에 대한 자세한 정리와 비판적 의견제시를 모두 포함해야 함. verbose = False일 경우, 3줄 이내의 요약만 포함. 기본값은 True.

# 비디오 다운로드
- video=True 시 비디오 다운로드
- srt=True 시 타임코드에 맞춰 srt 자막 생성.
- video=True 시 srt=True가 기본설정. 
- srt=True 시 translate=True가 기본설정이 된다.
- 언어가 한국어로 인식된 경우, translate=False로 강제전환.
  

# 주의사항
- 작은 in-file db를 이용해 'id, 요청 url, 제목, 엔진, 작업 진행상태, 주제분류, 키워드, 요약'을 관리한다.
이중에서 '요청 url, 제목, 엔진, 작업 진행상태' 필드는 NOT NULL.

- url이 재생목록인 경우, 재생목록을 전사하는 것이 맞는지 확인 요청. 20초 이상 응답이 없으면 더이상 대기하지 말고 종료. 진행승인이 나면, 재생목록에 포함된 요청을 안전하게 리스트업하여 대기목록에 추가되도록 한다.

- 이미 전사가 끝났거나 진행 중인 경우, 다시 진행하는게 맞는지 확인 요청. -force 옵션으로 강제.