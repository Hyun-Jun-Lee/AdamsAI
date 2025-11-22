# AdamsAI - 동영상 요약 서비스

동영상을 업로드하거나 링크로 다운로드하여 음성을 텍스트로 변환하고 AI로 요약하는 웹 서비스입니다.

## 🎯 주요 기능

- **동영상 입력**: 파일 업로드 또는 URL 다운로드 (m3u8 HLS 스트림 지원)
- **오디오 추출**: moviepy를 사용한 고품질 오디오 분리
- **음성 인식**: OpenAI Whisper API를 통한 정확한 STT 처리
- **AI 요약**: OpenRouter API (Claude 3.5 Sonnet 등)를 통한 지능형 요약

## 🏗️ 기술 스택

- **Backend**: Python 3.11+, FastAPI
- **Database**: SQLite (production에서는 PostgreSQL 권장)
- **Video/Audio**: moviepy, yt-dlp, pydub
- **AI Services**: OpenAI Whisper (STT), OpenRouter API (요약)

## 📂 프로젝트 구조

```
AdamsAI/
├── app/
│   ├── __init__.py
│   ├── config.py          # 환경 설정
│   ├── database.py        # DB 연결 및 세션 관리
│   ├── models.py          # SQLAlchemy ORM 모델
│   ├── schemas.py         # Pydantic 스키마
│   ├── routers/           # FastAPI 라우터
│   ├── services/          # 비즈니스 로직
│   ├── repositories/      # 데이터 접근 레이어
│   └── utils/             # 유틸리티 함수
├── storage/               # 파일 저장소
│   ├── videos/
│   ├── audios/
│   ├── transcripts/
│   └── summaries/
├── static/                # 정적 파일
├── templates/             # HTML 템플릿
└── tests/                 # 테스트 코드
```

## 🚀 시작하기

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/yourusername/AdamsAI.git
cd AdamsAI

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 등을 입력하세요
```

### 2. 필수 API 키 설정

`.env` 파일에 다음 API 키를 설정해야 합니다:

- `OPENAI_API_KEY`: OpenAI API 키 (Whisper STT용)
- `OPENROUTER_API_KEY`: OpenRouter API 키 (LLM 요약용)

### 3. 데이터베이스 초기화

```bash
# Python 인터프리터에서 실행
python -c "from app.database import init_db; init_db()"
```

### 4. 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

서버가 실행되면 http://localhost:8000 에서 접속 가능합니다.

## 📖 API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔄 개발 진행 상황

### ✅ Phase 1: 기본 인프라 (완료)
- [x] 프로젝트 구조 생성
- [x] config.py - 환경 설정
- [x] database.py - DB 연결 관리
- [x] models.py - ORM 모델 정의
- [x] schemas.py - Pydantic 스키마

### 📋 Phase 2: 유틸리티 함수 (예정)
- [ ] file_utils.py
- [ ] validators.py
- [ ] video_utils.py
- [ ] audio_utils.py
- [ ] downloader.py

### 📋 Phase 3-6 (예정)
- [ ] Phase 3: 데이터 접근 레이어 (repositories)
- [ ] Phase 4: 비즈니스 로직 (services)
- [ ] Phase 5: API 라우터 (routers)
- [ ] Phase 6: 앱 통합 및 테스트

## 🧪 테스트

```bash
pytest
```

## 📝 라이선스

MIT License

## 🤝 기여

기여는 언제나 환영합니다! Pull Request를 보내주세요.

---

**현재 상태**: Phase 1 완료 - 기본 인프라 구축 완료
