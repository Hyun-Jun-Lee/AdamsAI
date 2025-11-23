# 동영상 요약 서비스 개발 명세서 (DSL) - 함수형 스타일

## 프로젝트 개요
- **프로젝트명**: AdamsAI
- **목적**: 동영상을 업로드하거나 링크로 다운로드하여 음성을 텍스트로 변환하고 AI로 요약하는 웹 서비스
- **기술 스택**: Python, FastAPI, SQLite, moviepy, yt-dlp, OpenAI Whisper, OpenRouter API
- **코딩 스타일**: 함수형 프로그래밍 (클래스 최소화, 순수 함수 중심)

## 시스템 아키텍처
```
[웹 UI] 
   ↓
[FastAPI 라우터]
   ↓
[서비스 함수들]
   ├─ video_service.py
   ├─ audio_service.py
   ├─ stt_service.py
   └─ summary_service.py
   ↓
[데이터 접근 함수들]
   ├─ video_repository.py
   ├─ audio_repository.py
   ├─ transcript_repository.py
   └─ summary_repository.py
   ↓
[SQLite DB + 파일 스토리지]
```

## 디렉토리 구조
```
AdamsAI/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── videos.py
│   │   ├── audios.py
│   │   ├── transcripts.py
│   │   └── summaries.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── video_service.py
│   │   ├── audio_service.py
│   │   ├── stt_service.py
│   │   └── summary_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── video_repository.py
│   │   ├── audio_repository.py
│   │   ├── transcript_repository.py
│   │   └── summary_repository.py
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       ├── video_utils.py
│       ├── audio_utils.py
│       ├── downloader.py
│       └── validators.py
├── storage/
│   ├── videos/
│   ├── audios/
│   ├── transcripts/
│   └── summaries/
├── static/
├── templates/
│   └── index.html
├── tests/
├── .env
├── requirements.txt
└── README.md
```

## 데이터베이스 스키마

### videos 테이블
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT,
    file_size INTEGER,
    duration REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'uploaded'
);
```

### audios 테이블
```sql
CREATE TABLE audios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    file_size INTEGER,
    duration REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'extracted',
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);
```

### transcripts 테이블
```sql
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    language TEXT DEFAULT 'ko',
    model TEXT DEFAULT 'whisper-1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_id) REFERENCES audios(id) ON DELETE CASCADE
);
```

### summaries 테이블
```sql
CREATE TABLE summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id INTEGER NOT NULL,
    summary_text TEXT NOT NULL,
    model_name TEXT NOT NULL,
    prompt_template TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id) ON DELETE CASCADE
);
```

## API 엔드포인트 명세

### 1. 동영상 업로드
```
POST /api/videos/upload
Content-Type: multipart/form-data

Request:
  - file: 동영상 파일

Response: 201 Created
{
  "id": 1,
  "filename": "부동산영상.mp4",
  "filepath": "storage/videos/uuid-부동산영상.mp4",
  "source_type": "upload",
  "file_size": 52428800,
  "status": "uploaded",
  "created_at": "2025-11-17T10:30:00"
}
```

### 2. 동영상 링크 다운로드 (m3u8 지원)
```
POST /api/videos/download
Content-Type: application/json

Request:
{
  "url": "https://example.com/video.m3u8",
  "title": "부동산 분석 영상"
}

Response: 202 Accepted
{
  "id": 2,
  "status": "downloading",
  "message": "동영상 다운로드가 시작되었습니다."
}
```

### 3. 동영상 목록 조회
```
GET /api/videos?status=uploaded&limit=10&offset=0

Response: 200 OK
{
  "total": 25,
  "items": [...]
}
```

### 4. 오디오 추출
```
POST /api/audios/extract
Content-Type: application/json

Request:
{
  "video_id": 1
}

Response: 201 Created
{
  "id": 1,
  "video_id": 1,
  "filename": "audio-1.mp3",
  "filepath": "storage/audios/audio-1.mp3",
  "status": "extracted"
}
```

### 5. 오디오 목록 조회
```
GET /api/audios?video_id=1

Response: 200 OK
{
  "total": 1,
  "items": [...]
}
```

### 6. STT 처리 (Whisper)
```
POST /api/transcripts/create
Content-Type: application/json

Request:
{
  "audio_id": 1,
  "language": "ko"
}

Response: 202 Accepted
{
  "id": 1,
  "audio_id": 1,
  "status": "processing"
}
```

### 7. 전사 텍스트 목록 조회
```
GET /api/transcripts?audio_id=1

Response: 200 OK
{
  "total": 1,
  "items": [...]
}
```

### 8. 요약 생성 (OpenRouter LLM)
```
POST /api/summaries/create
Content-Type: application/json

Request:
{
  "transcript_id": 1,
  "model_name": "anthropic/claude-3.5-sonnet",
  "prompt_template": "default"
}

Response: 201 Created
{
  "id": 1,
  "transcript_id": 1,
  "status": "generating"
}
```

### 9. 요약 목록 조회
```
GET /api/summaries?transcript_id=1

Response: 200 OK
{
  "total": 2,
  "items": [...]
}
```

## 함수 인터페이스 명세

### config.py
```python
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openrouter_api_key: str
    database_url: str = "sqlite:///./storage/app.db"
    storage_root: Path = Path("./storage")
    videos_dir: Path = Path("./storage/videos")
    audios_dir: Path = Path("./storage/audios")
    max_video_size_mb: int = 500
    max_upload_size_mb: int = 500
    default_audio_bitrate: str = "192k"
    default_llm_model: str = "anthropic/claude-3.5-sonnet"
    default_language: str = "ko"
    
    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    """설정 객체 반환"""
    pass
```

### database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

def get_db() -> Generator[Session, None, None]:
    """DB 세션 의존성 (FastAPI 의존성 주입용)"""
    pass

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """DB 세션 컨텍스트 매니저"""
    pass

def init_db() -> None:
    """데이터베이스 초기화"""
    pass
```

### repositories/video_repository.py
```python
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Video
from app.schemas import VideoCreate

def create_video(db: Session, video_data: VideoCreate) -> Video:
    """동영상 레코드 생성"""
    pass

def get_video_by_id(db: Session, video_id: int) -> Optional[Video]:
    """ID로 동영상 조회"""
    pass

def get_videos(db: Session, status: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Video]:
    """동영상 목록 조회"""
    pass

def count_videos(db: Session, status: Optional[str] = None) -> int:
    """동영상 개수 조회"""
    pass

def update_video_status(db: Session, video_id: int, status: str) -> Optional[Video]:
    """동영상 상태 업데이트"""
    pass

def delete_video(db: Session, video_id: int) -> bool:
    """동영상 삭제"""
    pass
```

### repositories/audio_repository.py
```python
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Audio
from app.schemas import AudioCreate

def create_audio(db: Session, audio_data: AudioCreate) -> Audio:
    """오디오 레코드 생성"""
    pass

def get_audio_by_id(db: Session, audio_id: int) -> Optional[Audio]:
    """ID로 오디오 조회"""
    pass

def get_audios_by_video_id(db: Session, video_id: int) -> List[Audio]:
    """특정 동영상의 오디오 목록 조회"""
    pass

def update_audio_status(db: Session, audio_id: int, status: str) -> Optional[Audio]:
    """오디오 상태 업데이트"""
    pass
```

### repositories/transcript_repository.py
```python
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Transcript
from app.schemas import TranscriptCreate

def create_transcript(db: Session, transcript_data: TranscriptCreate) -> Transcript:
    """전사 텍스트 레코드 생성"""
    pass

def get_transcript_by_id(db: Session, transcript_id: int) -> Optional[Transcript]:
    """ID로 전사 텍스트 조회"""
    pass

def get_transcripts_by_audio_id(db: Session, audio_id: int) -> List[Transcript]:
    """특정 오디오의 전사 텍스트 목록 조회"""
    pass
```

### repositories/summary_repository.py
```python
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Summary
from app.schemas import SummaryCreate

def create_summary(db: Session, summary_data: SummaryCreate) -> Summary:
    """요약 레코드 생성"""
    pass

def get_summary_by_id(db: Session, summary_id: int) -> Optional[Summary]:
    """ID로 요약 조회"""
    pass

def get_summaries_by_transcript_id(db: Session, transcript_id: int) -> List[Summary]:
    """특정 전사 텍스트의 요약 목록 조회"""
    pass
```

### utils/file_utils.py
```python
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile

def generate_unique_filename(original_filename: str) -> str:
    """UUID 기반 고유 파일명 생성"""
    pass

def get_file_size_mb(filepath: Path) -> float:
    """파일 크기를 MB 단위로 반환"""
    pass

async def save_upload_file(file: UploadFile, destination: Path) -> Tuple[str, int]:
    """업로드된 파일을 저장. Returns: (filename, file_size_bytes)"""
    pass

def ensure_directory_exists(directory: Path) -> None:
    """디렉토리가 없으면 생성"""
    pass

def delete_file_safe(filepath: Path) -> bool:
    """파일을 안전하게 삭제"""
    pass
```

### utils/validators.py
```python
from typing import List

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """파일 확장자 검증"""
    pass

def validate_video_file(filename: str) -> bool:
    """동영상 파일 확장자 검증"""
    pass

def validate_audio_file(filename: str) -> bool:
    """오디오 파일 확장자 검증"""
    pass

def validate_file_size(file_size_bytes: int, max_size_mb: int) -> bool:
    """파일 크기 검증"""
    pass

def is_m3u8_url(url: str) -> bool:
    """URL이 m3u8 형식인지 확인"""
    pass
```

### utils/video_utils.py
```python
from pathlib import Path
from typing import Optional

def get_video_duration(video_path: Path) -> Optional[float]:
    """동영상 길이 추출 (초 단위)"""
    pass

def has_audio_track(video_path: Path) -> bool:
    """동영상에 오디오 트랙이 있는지 확인"""
    pass
```

### utils/audio_utils.py
```python
from pathlib import Path
from typing import Tuple, Optional

def extract_audio_from_video(video_path: Path, output_path: Path, bitrate: str = "192k") -> Tuple[bool, Optional[float]]:
    """동영상에서 오디오 추출. Returns: (success, duration)"""
    pass

def get_audio_duration(audio_path: Path) -> Optional[float]:
    """오디오 파일의 길이 추출 (초 단위)"""
    pass
```

### utils/downloader.py
```python
from pathlib import Path
from typing import Optional, Dict, Any

def download_video_from_url(url: str, output_dir: Path, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """URL에서 동영상 다운로드 (m3u8 지원). Returns: {'filepath': Path, 'title': str, 'duration': float, 'filesize': int}"""
    pass

def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """다운로드하지 않고 동영상 정보만 추출"""
    pass
```

### services/video_service.py
```python
from sqlalchemy.orm import Session
from fastapi import UploadFile
from typing import Dict, Any
from app.schemas import VideoResponse

async def handle_video_upload(db: Session, file: UploadFile) -> VideoResponse:
    """동영상 파일 업로드 처리"""
    pass

async def handle_video_download(db: Session, url: str, title: str = None) -> VideoResponse:
    """URL에서 동영상 다운로드 처리"""
    pass

def get_video_list(db: Session, status: str = None, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """동영상 목록 조회"""
    pass

def get_video_by_id(db: Session, video_id: int) -> VideoResponse:
    """특정 동영상 조회"""
    pass
```

### services/audio_service.py
```python
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.schemas import AudioResponse

async def handle_audio_extraction(db: Session, video_id: int) -> AudioResponse:
    """동영상에서 오디오 추출"""
    pass

def get_audio_list(db: Session, video_id: int = None) -> Dict[str, Any]:
    """오디오 목록 조회"""
    pass

def get_audio_by_id(db: Session, audio_id: int) -> AudioResponse:
    """특정 오디오 조회"""
    pass
```

### services/stt_service.py
```python
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.schemas import TranscriptResponse

async def handle_transcription(db: Session, audio_id: int, language: str = "ko") -> TranscriptResponse:
    """Whisper API로 음성 인식 처리"""
    pass

def get_transcript_list(db: Session, audio_id: int = None) -> Dict[str, Any]:
    """전사 텍스트 목록 조회"""
    pass

def get_transcript_by_id(db: Session, transcript_id: int) -> TranscriptResponse:
    """특정 전사 텍스트 조회"""
    pass
```

### services/summary_service.py
```python
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.schemas import SummaryResponse

# 프롬프트 템플릿들
PROMPT_TEMPLATES = {
    "default": """부동산 영상 전사 내용입니다. 다음 형식으로 요약해주세요:

## 📋 주제
[영상의 메인 주제]

## 🔑 핵심 내용
[3-5개의 주요 포인트]

## 💡 결론 및 시사점
[투자자/관심자에게 중요한 인사이트]

---
전사 내용:
{transcript}""",
    
    "detailed": "...",
    "brief": "..."
}

def get_prompt_template(template_name: str) -> str:
    """프롬프트 템플릿 가져오기"""
    pass

async def call_openrouter_api(prompt: str, model_name: str) -> str:
    """OpenRouter API 호출"""
    pass

async def handle_summary_generation(db: Session, transcript_id: int, model_name: str = None, prompt_template: str = "default") -> SummaryResponse:
    """요약 생성 처리"""
    pass

def get_summary_list(db: Session, transcript_id: int = None) -> Dict[str, Any]:
    """요약 목록 조회"""
    pass

def get_summary_by_id(db: Session, summary_id: int) -> SummaryResponse:
    """특정 요약 조회"""
    pass
```

### routers/videos.py
```python
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas import VideoResponse, VideoDownloadRequest
from app.services import video_service

router = APIRouter(prefix="/api/videos", tags=["videos"])

@router.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """동영상 파일 업로드"""
    pass

@router.post("/download", response_model=VideoResponse, status_code=202)
async def download_video(request: VideoDownloadRequest, db: Session = Depends(get_db)):
    """URL에서 동영상 다운로드"""
    pass

@router.get("", response_model=dict)
def list_videos(status: Optional[str] = None, limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    """동영상 목록 조회"""
    pass

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)):
    """특정 동영상 조회"""
    pass
```

### routers/audios.py
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas import AudioResponse, AudioExtractRequest
from app.services import audio_service

router = APIRouter(prefix="/api/audios", tags=["audios"])

@router.post("/extract", response_model=AudioResponse, status_code=201)
async def extract_audio(request: AudioExtractRequest, db: Session = Depends(get_db)):
    """동영상에서 오디오 추출"""
    pass

@router.get("", response_model=dict)
def list_audios(video_id: Optional[int] = None, db: Session = Depends(get_db)):
    """오디오 목록 조회"""
    pass

@router.get("/{audio_id}", response_model=AudioResponse)
def get_audio(audio_id: int, db: Session = Depends(get_db)):
    """특정 오디오 조회"""
    pass
```

### routers/transcripts.py
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas import TranscriptResponse, TranscriptCreateRequest
from app.services import stt_service

router = APIRouter(prefix="/api/transcripts", tags=["transcripts"])

@router.post("/create", response_model=TranscriptResponse, status_code=202)
async def create_transcript(request: TranscriptCreateRequest, db: Session = Depends(get_db)):
    """STT 처리"""
    pass

@router.get("", response_model=dict)
def list_transcripts(audio_id: Optional[int] = None, db: Session = Depends(get_db)):
    """전사 텍스트 목록 조회"""
    pass

@router.get("/{transcript_id}", response_model=TranscriptResponse)
def get_transcript(transcript_id: int, db: Session = Depends(get_db)):
    """특정 전사 텍스트 조회"""
    pass
```

### routers/summaries.py
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas import SummaryResponse, SummaryCreateRequest
from app.services import summary_service

router = APIRouter(prefix="/api/summaries", tags=["summaries"])

@router.post("/create", response_model=SummaryResponse, status_code=201)
async def create_summary(request: SummaryCreateRequest, db: Session = Depends(get_db)):
    """요약 생성"""
    pass

@router.get("", response_model=dict)
def list_summaries(transcript_id: Optional[int] = None, db: Session = Depends(get_db)):
    """요약 목록 조회"""
    pass

@router.get("/{summary_id}", response_model=SummaryResponse)
def get_summary(summary_id: int, db: Session = Depends(get_db)):
    """특정 요약 조회"""
    pass
```

### main.py
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.config import get_settings
from app.routers import videos, audios, transcripts, summaries

settings = get_settings()
app = FastAPI(title="Video Summarizer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)
app.include_router(audios.router)
app.include_router(transcripts.router)
app.include_router(summaries.router)

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    pass

@app.get("/")
async def root():
    """루트 엔드포인트"""
    pass

@app.get("/health")
async def health_check():
    """헬스 체크"""
    pass
```

## 환경 변수 (.env)
```
OPENAI_API_KEY=your-openai-key
OPENROUTER_API_KEY=your-openrouter-key
DATABASE_URL=sqlite:///./storage/app.db
STORAGE_ROOT=./storage
VIDEOS_DIR=./storage/videos
AUDIOS_DIR=./storage/audios
MAX_VIDEO_SIZE_MB=500
MAX_UPLOAD_SIZE_MB=500
DEFAULT_AUDIO_BITRATE=192k
DEFAULT_LLM_MODEL=anthropic/claude-3.5-sonnet
DEFAULT_LANGUAGE=ko
```

## requirements.txt
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
aiofiles==23.2.1
python-dotenv==1.0.0
moviepy==1.0.3
yt-dlp==2024.1.1
pydub==0.25.1
openai==1.10.0
httpx==0.26.0
```

## 개발 단계별 구현 순서

### Phase 1: 기본 인프라
1. 프로젝트 구조 생성
2. config.py, database.py 구현
3. models.py, schemas.py 정의

### Phase 2: 유틸리티 함수
1. file_utils.py
2. validators.py
3. video_utils.py
4. audio_utils.py
5. downloader.py

### Phase 3: 데이터 접근 레이어
1. video_repository.py
2. audio_repository.py
3. transcript_repository.py
4. summary_repository.py

### Phase 4: 비즈니스 로직
1. video_service.py
2. audio_service.py
3. stt_service.py
4. summary_service.py

### Phase 5: API 라우터
1. videos.py
2. audios.py
3. transcripts.py
4. summaries.py

### Phase 6: 앱 통합
1. main.py
2. 테스트

## 실행 명령어
```bash
uvicorn app.main:app --reload --port 8000
```

## 핵심 원칙
1. 순수 함수 우선
2. 단일 책임
3. 의존성 주입
4. 타입 힌팅
5. 명확한 에러 처리