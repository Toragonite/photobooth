# 인생네컷 포토부스 프로젝트 최종 정리 (v2)

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **목적** | 아프리카 선교지에서 사용할 인생네컷 포토부스 |
| **환경** | On-premise (인터넷 없음), 무전원 가능 |
| **핵심 요구사항** | 저예산, 간단한 구성, 유지보수 용이, 자동 인쇄 |

---

## 2. 시스템 구성

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   iPad Air (보유)                        Raspberry Pi 4         │
│  ┌───────────────┐                      ┌───────────────────┐  │
│  │               │                      │      Docker       │  │
│  │   Safari      │        Wi-Fi         │ ┌───────────────┐ │  │
│  │   (웹앱)      │◄────────────────────►│ │   Frontend    │ │  │
│  │               │       HTTPS          │ │  (React+Vite) │ │  │
│  │  ┌─────────┐  │                      │ ├───────────────┤ │  │
│  │  │ 카메라  │  │                      │ │   Backend     │ │  │
│  │  └─────────┘  │                      │ │  (FastAPI)    │ │  │
│  │               │                      │ │      │        │ │  │
│  │  [ UI 표시 ]  │                      │ │    CUPS       │ │  │
│  │  [터치 입력]  │                      │ └───────┬───────┘ │  │
│  │  [ 사진촬영 ] │                      └─────────┼─────────┘  │
│  │               │                                │ USB        │
│  └───────────────┘                         ┌──────▼──────┐     │
│                                            │Canon Selphy │     │
│       자체 배터리                           │  CP1500     │     │
│                                            │ (NB-CP2LI)  │     │
│   PD 보조배터리 ─────────────► Pi          └─────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 인쇄 흐름 상세

### 전체 시퀀스 다이어그램

```
┌────────┐         ┌────────┐         ┌────────┐         ┌────────┐
│  iPad  │         │Frontend│         │Backend │         │ CUPS/  │
│(카메라)│         │(React) │         │(FastAPI)│        │ Selphy │
└───┬────┘         └───┬────┘         └───┬────┘         └───┬────┘
    │                  │                  │                  │
    │  1. 촬영 시작    │                  │                  │
    │─────────────────►│                  │                  │
    │                  │                  │                  │
    │  2. 4장 촬영     │                  │                  │
    │  (카운트다운)    │                  │                  │
    │◄─────────────────│                  │                  │
    │                  │                  │                  │
    │  3. Base64 이미지│                  │                  │
    │─────────────────►│                  │                  │
    │                  │                  │                  │
    │                  │ 4. POST /api/print                  │
    │                  │  (images[4])     │                  │
    │                  │─────────────────►│                  │
    │                  │                  │                  │
    │                  │                  │ 5. 이미지 합성   │
    │                  │                  │ (4컷 레이아웃)   │
    │                  │                  │                  │
    │                  │                  │ 6. CUPS 인쇄 요청│
    │                  │                  │─────────────────►│
    │                  │                  │                  │
    │                  │                  │ 7. Job ID 반환   │
    │                  │                  │◄─────────────────│
    │                  │                  │                  │
    │                  │ 8. 상태: printing│                  │
    │                  │◄─────────────────│                  │
    │                  │                  │                  │
    │                  │                  │ 9. 폴링: 상태확인│
    │                  │                  │─────────────────►│
    │                  │                  │                  │
    │                  │                  │    (반복)        │
    │                  │                  │◄─────────────────│
    │                  │                  │                  │
    │                  │                  │ 10. 완료 감지    │
    │                  │                  │◄─────────────────│
    │                  │                  │                  │
    │                  │ 11. 상태: completed                 │
    │                  │◄─────────────────│                  │
    │                  │                  │                  │
    │ 12. 완료 화면    │                  │                  │
    │◄─────────────────│                  │                  │
    │                  │                  │                  │
    │ 13. 홈으로 이동  │                  │                  │
    │◄─────────────────│                  │                  │
    │                  │                  │                  │
```

---

## 4. 프로젝트 구조

```
photobooth/
├── docker-compose.yml
├── nginx.conf
├── certs/
│   ├── cert.pem
│   └── key.pem
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── types/
│       │   └── index.ts
│       ├── pages/
│       │   ├── HomePage.tsx
│       │   ├── CameraPage.tsx
│       │   ├── PreviewPage.tsx
│       │   └── CompletePage.tsx
│       ├── components/
│       │   ├── Countdown.tsx
│       │   ├── Thumbnail.tsx
│       │   ├── CameraPreview.tsx
│       │   └── PrintProgress.tsx
│       ├── hooks/
│       │   ├── useCamera.ts
│       │   └── usePrintStatus.ts
│       ├── services/
│       │   └── api.ts
│       └── styles/
│           └── global.css
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── image_processor.py
│   │   │   └── printer_service.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       └── print_router.py
│   └── output/
│
└── setup/
    ├── install.sh
    ├── setup_hotspot.sh
    └── setup_cups.sh
```

---

## 5. 백엔드 상세 코드

### backend/app/config.py

```python
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 경로
    BASE_DIR: Path = Path(__file__).parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "output"
    
    # 프린터
    PRINTER_NAME: str = "Canon_CP1500"
    PRINT_COPIES: int = 2
    
    # 이미지
    OUTPUT_WIDTH: int = 1200   # 4 inch * 300 DPI
    OUTPUT_HEIGHT: int = 1800  # 6 inch * 300 DPI
    PHOTO_PADDING: int = 30
    JPEG_QUALITY: int = 95
    
    # 폴링
    PRINT_STATUS_POLL_INTERVAL: float = 1.0  # 초
    PRINT_TIMEOUT: int = 120  # 초
    
    class Config:
        env_file = ".env"

settings = Settings()
settings.OUTPUT_DIR.mkdir(exist_ok=True)
```

### backend/app/models/schemas.py

```python
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from datetime import datetime

class PrintStatus(str, Enum):
    PROCESSING = "processing"      # 이미지 합성 중
    SENDING = "sending"            # 프린터로 전송 중
    PRINTING = "printing"          # 인쇄 중
    COMPLETED = "completed"        # 완료
    ERROR = "error"                # 오류

class PrintRequest(BaseModel):
    images: List[str]  # Base64 encoded images
    copies: int = 2

class PrintJob(BaseModel):
    job_id: str
    cups_job_id: Optional[int] = None
    status: PrintStatus
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_image: Optional[str] = None  # Base64 (미리보기용)

class PrintStatusResponse(BaseModel):
    job_id: str
    status: PrintStatus
    message: str
    progress: int  # 0-100
    can_go_home: bool  # 홈으로 이동 가능 여부

class PrinterInfo(BaseModel):
    name: str
    is_available: bool
    status: str
```

### backend/app/services/printer_service.py

```python
"""CUPS 기반 프린터 서비스 - Selphy USB 자동 인쇄"""
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading

try:
    import cups
    CUPS_AVAILABLE = True
except ImportError:
    CUPS_AVAILABLE = False

from app.config import settings
from app.models.schemas import PrintStatus


@dataclass
class PrintJobInfo:
    """인쇄 작업 정보"""
    job_id: str
    cups_job_id: Optional[int] = None
    status: PrintStatus = PrintStatus.PROCESSING
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    file_path: Optional[Path] = None


class PrinterService:
    """CUPS를 통한 Selphy USB 자동 인쇄"""
    
    def __init__(self):
        self.conn: Optional[cups.Connection] = None
        self.jobs: Dict[str, PrintJobInfo] = {}
        self._lock = threading.Lock()
        
        if CUPS_AVAILABLE:
            try:
                self.conn = cups.Connection()
            except Exception as e:
                print(f"CUPS 연결 실패: {e}")
    
    def get_printer_status(self) -> Tuple[bool, str]:
        """프린터 상태 확인"""
        if not self.conn:
            return False, "CUPS 연결 안됨"
        
        try:
            printers = self.conn.getPrinters()
            printer_name = settings.PRINTER_NAME
            
            if printer_name not in printers:
                # 사용 가능한 프린터 찾기
                available = list(printers.keys())
                if available:
                    return True, f"기본 프린터: {available[0]}"
                return False, "연결된 프린터 없음"
            
            printer_info = printers[printer_name]
            state = printer_info.get('printer-state', 0)
            
            # CUPS 프린터 상태 코드
            # 3 = idle, 4 = printing, 5 = stopped
            if state == 3:
                return True, "대기 중"
            elif state == 4:
                return True, "인쇄 중"
            elif state == 5:
                return False, "프린터 중지됨"
            else:
                return True, f"상태: {state}"
                
        except Exception as e:
            return False, f"상태 확인 오류: {e}"
    
    def get_available_printer(self) -> Optional[str]:
        """사용 가능한 프린터 이름 반환"""
        if not self.conn:
            return None
        
        try:
            printers = self.conn.getPrinters()
            
            # 설정된 프린터 확인
            if settings.PRINTER_NAME in printers:
                return settings.PRINTER_NAME
            
            # Canon/Selphy 프린터 찾기
            for name in printers:
                if 'canon' in name.lower() or 'selphy' in name.lower() or 'cp1500' in name.lower():
                    return name
            
            # 아무 프린터나 반환
            if printers:
                return list(printers.keys())[0]
            
            return None
        except:
            return None
    
    def print_image(
        self,
        image_path: Path,
        job_id: str,
        copies: int = 2
    ) -> PrintJobInfo:
        """이미지 인쇄 (자동, 다이얼로그 없음)"""
        
        job_info = PrintJobInfo(
            job_id=job_id,
            file_path=image_path,
            status=PrintStatus.SENDING,
            message="프린터로 전송 중..."
        )
        
        with self._lock:
            self.jobs[job_id] = job_info
        
        printer_name = self.get_available_printer()
        
        if not printer_name:
            job_info.status = PrintStatus.ERROR
            job_info.message = "프린터를 찾을 수 없습니다"
            return job_info
        
        if not image_path.exists():
            job_info.status = PrintStatus.ERROR
            job_info.message = f"파일이 없습니다: {image_path}"
            return job_info
        
        try:
            # 방법 1: pycups 사용
            if self.conn:
                cups_job_id = self.conn.printFile(
                    printer_name,
                    str(image_path),
                    f"PhotoBooth_{job_id}",
                    {
                        "copies": str(copies),
                        "media": "4x6",              # 4x6 인치
                        "fit-to-page": "true",      # 페이지에 맞춤
                        "print-quality": "5",       # 최고 품질
                    }
                )
                
                job_info.cups_job_id = cups_job_id
                job_info.status = PrintStatus.PRINTING
                job_info.message = f"인쇄 중... (Job #{cups_job_id})"
                
                # 비동기로 상태 모니터링 시작
                threading.Thread(
                    target=self._monitor_job,
                    args=(job_id,),
                    daemon=True
                ).start()
                
                return job_info
            
            # 방법 2: lp 명령어 (백업)
            cmd = [
                "lp",
                "-d", printer_name,
                "-n", str(copies),
                "-o", "media=4x6",
                "-o", "fit-to-page",
                "-o", "print-quality=5",
                str(image_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # request id 파싱: "request id is Canon_CP1500-123 (1 file(s))"
                output = result.stdout
                if "request id is" in output:
                    parts = output.split("request id is")[1].split()[0]
                    cups_job_id = int(parts.split("-")[-1])
                    job_info.cups_job_id = cups_job_id
                
                job_info.status = PrintStatus.PRINTING
                job_info.message = "인쇄 중..."
                
                threading.Thread(
                    target=self._monitor_job,
                    args=(job_id,),
                    daemon=True
                ).start()
            else:
                job_info.status = PrintStatus.ERROR
                job_info.message = f"인쇄 실패: {result.stderr}"
            
            return job_info
            
        except Exception as e:
            job_info.status = PrintStatus.ERROR
            job_info.message = f"인쇄 오류: {str(e)}"
            return job_info
    
    def _monitor_job(self, job_id: str):
        """인쇄 작업 상태 모니터링 (백그라운드 스레드)"""
        start_time = time.time()
        
        while True:
            with self._lock:
                job_info = self.jobs.get(job_id)
                if not job_info:
                    return
                
                if job_info.status in [PrintStatus.COMPLETED, PrintStatus.ERROR]:
                    return
            
            # 타임아웃 체크
            if time.time() - start_time > settings.PRINT_TIMEOUT:
                with self._lock:
                    job_info.status = PrintStatus.ERROR
                    job_info.message = "인쇄 시간 초과"
                return
            
            # CUPS 작업 상태 확인
            cups_status = self._get_cups_job_status(job_info.cups_job_id)
            
            with self._lock:
                if cups_status == "completed":
                    job_info.status = PrintStatus.COMPLETED
                    job_info.message = "인쇄 완료!"
                    job_info.completed_at = datetime.now()
                    return
                elif cups_status == "error":
                    job_info.status = PrintStatus.ERROR
                    job_info.message = "프린터 오류 발생"
                    return
                elif cups_status == "printing":
                    job_info.message = "인쇄 중..."
            
            time.sleep(settings.PRINT_STATUS_POLL_INTERVAL)
    
    def _get_cups_job_status(self, cups_job_id: Optional[int]) -> str:
        """CUPS 작업 상태 조회"""
        if not cups_job_id or not self.conn:
            return "unknown"
        
        try:
            # 활성 작업 확인
            jobs = self.conn.getJobs()
            
            if cups_job_id in jobs:
                job = jobs[cups_job_id]
                state = job.get('job-state', 0)
                
                # CUPS job states:
                # 3 = pending, 4 = held, 5 = processing, 
                # 6 = stopped, 7 = canceled, 8 = aborted, 9 = completed
                if state == 5:
                    return "printing"
                elif state == 9:
                    return "completed"
                elif state in [7, 8]:
                    return "error"
                else:
                    return "pending"
            
            # 작업이 목록에 없으면 완료된 것
            return "completed"
            
        except Exception as e:
            print(f"CUPS 상태 조회 오류: {e}")
            return "unknown"
    
    def get_job_status(self, job_id: str) -> Optional[PrintJobInfo]:
        """작업 상태 조회"""
        with self._lock:
            return self.jobs.get(job_id)
    
    def can_go_home(self, job_id: str) -> bool:
        """홈으로 이동 가능 여부 (인쇄 완료 또는 오류)"""
        job_info = self.get_job_status(job_id)
        if not job_info:
            return True
        return job_info.status in [PrintStatus.COMPLETED, PrintStatus.ERROR]


# 싱글톤 인스턴스
printer_service = PrinterService()
```

### backend/app/services/image_processor.py

```python
"""이미지 합성 서비스"""
import base64
import io
from pathlib import Path
from typing import List
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from app.config import settings


class ImageProcessor:
    """4컷 레이아웃 이미지 합성"""
    
    def create_four_cut_layout(
        self,
        base64_images: List[str],
        job_id: str,
        add_date: bool = True
    ) -> Path:
        """4장의 Base64 이미지를 인생네컷 레이아웃으로 합성"""
        
        if len(base64_images) != 4:
            raise ValueError(f"4장의 사진이 필요합니다. 현재: {len(base64_images)}장")
        
        # 캔버스 생성 (흰색 배경)
        canvas = Image.new(
            'RGB',
            (settings.OUTPUT_WIDTH, settings.OUTPUT_HEIGHT),
            'white'
        )
        
        # 각 사진 크기 계산
        padding = settings.PHOTO_PADDING
        photo_width = (settings.OUTPUT_WIDTH - padding * 3) // 2
        photo_height = (settings.OUTPUT_HEIGHT - padding * 3) // 2
        
        # 4장 배치 위치
        positions = [
            (padding, padding),
            (padding * 2 + photo_width, padding),
            (padding, padding * 2 + photo_height),
            (padding * 2 + photo_width, padding * 2 + photo_height),
        ]
        
        # 각 사진 배치
        for i, img_base64 in enumerate(base64_images):
            # Base64 디코딩
            if ',' in img_base64:
                img_base64 = img_base64.split(',')[1]
            
            img_data = base64.b64decode(img_base64)
            photo = Image.open(io.BytesIO(img_data))
            
            # RGB 변환
            if photo.mode != 'RGB':
                photo = photo.convert('RGB')
            
            # 비율 유지하며 리사이즈 & 크롭
            photo = self._resize_and_crop(photo, photo_width, photo_height)
            
            # 캔버스에 붙이기
            canvas.paste(photo, positions[i])
        
        # 날짜 스탬프 추가
        if add_date:
            self._add_date_stamp(canvas)
        
        # 저장
        output_path = settings.OUTPUT_DIR / f"fourcut_{job_id}.jpg"
        canvas.save(output_path, 'JPEG', quality=settings.JPEG_QUALITY)
        
        return output_path
    
    def _resize_and_crop(
        self,
        image: Image.Image,
        target_width: int,
        target_height: int
    ) -> Image.Image:
        """비율 유지하며 중앙 크롭"""
        
        target_ratio = target_width / target_height
        current_ratio = image.width / image.height
        
        if current_ratio > target_ratio:
            # 가로가 더 넓음 -> 좌우 크롭
            new_width = int(image.height * target_ratio)
            left = (image.width - new_width) // 2
            image = image.crop((left, 0, left + new_width, image.height))
        else:
            # 세로가 더 넓음 -> 상하 크롭
            new_height = int(image.width / target_ratio)
            top = (image.height - new_height) // 2
            image = image.crop((0, top, image.width, top + new_height))
        
        return image.resize((target_width, target_height), Image.LANCZOS)
    
    def _add_date_stamp(self, canvas: Image.Image):
        """날짜 스탬프 추가"""
        draw = ImageDraw.Draw(canvas)
        
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                28
            )
        except:
            font = ImageFont.load_default()
        
        date_text = datetime.now().strftime("%Y.%m.%d")
        
        bbox = draw.textbbox((0, 0), date_text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (canvas.width - text_width) // 2
        y = canvas.height - 60
        
        # 그림자 효과
        draw.text((x + 2, y + 2), date_text, fill='gray', font=font)
        draw.text((x, y), date_text, fill='black', font=font)
    
    def image_to_base64(self, image_path: Path) -> str:
        """이미지를 Base64로 변환"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')


# 싱글톤 인스턴스
image_processor = ImageProcessor()
```

### backend/app/routers/print_router.py

```python
"""인쇄 관련 API 라우터"""
import uuid
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    PrintRequest, 
    PrintJob, 
    PrintStatusResponse, 
    PrintStatus,
    PrinterInfo
)
from app.services.image_processor import image_processor
from app.services.printer_service import printer_service

router = APIRouter(prefix="/api", tags=["print"])


@router.get("/status")
async def get_system_status():
    """시스템 상태 확인"""
    is_available, printer_status = printer_service.get_printer_status()
    printer_name = printer_service.get_available_printer()
    
    return {
        "online": True,
        "printer": PrinterInfo(
            name=printer_name or "없음",
            is_available=is_available,
            status=printer_status
        )
    }


@router.post("/print", response_model=PrintJob)
async def process_and_print(request: PrintRequest):
    """
    이미지 합성 + 인쇄 시작
    
    1. 4장의 Base64 이미지를 받음
    2. 4컷 레이아웃으로 합성
    3. CUPS로 자동 인쇄 시작
    4. Job ID 반환 (상태 폴링용)
    """
    if len(request.images) != 4:
        raise HTTPException(
            status_code=400, 
            detail="4장의 사진이 필요합니다"
        )
    
    job_id = str(uuid.uuid4())[:8]
    
    try:
        # 1. 이미지 합성
        result_path = image_processor.create_four_cut_layout(
            request.images,
            job_id
        )
        
        # 2. 인쇄 시작
        job_info = printer_service.print_image(
            result_path,
            job_id,
            copies=request.copies
        )
        
        # 3. 미리보기용 Base64
        result_base64 = image_processor.image_to_base64(result_path)
        
        return PrintJob(
            job_id=job_id,
            cups_job_id=job_info.cups_job_id,
            status=job_info.status,
            message=job_info.message,
            created_at=job_info.created_at,
            result_image=result_base64
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/print/{job_id}/status", response_model=PrintStatusResponse)
async def get_print_status(job_id: str):
    """
    인쇄 상태 조회 (폴링용)
    
    Frontend에서 주기적으로 호출하여 상태 확인
    can_go_home이 True가 되면 홈으로 이동 가능
    """
    job_info = printer_service.get_job_status(job_id)
    
    if not job_info:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
    
    # 진행률 계산
    progress = {
        PrintStatus.PROCESSING: 25,
        PrintStatus.SENDING: 50,
        PrintStatus.PRINTING: 75,
        PrintStatus.COMPLETED: 100,
        PrintStatus.ERROR: 0
    }.get(job_info.status, 0)
    
    return PrintStatusResponse(
        job_id=job_id,
        status=job_info.status,
        message=job_info.message,
        progress=progress,
        can_go_home=printer_service.can_go_home(job_id)
    )
```

### backend/app/main.py

```python
"""FastAPI 메인 앱"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import print_router

app = FastAPI(
    title="PhotoBooth API",
    description="인생네컷 포토부스 백엔드",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(print_router.router)

# 정적 파일 서빙 (빌드된 React 앱)
FRONTEND_DIR = Path("/app/static")
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

## 6. 프론트엔드 상세 코드

### frontend/src/types/index.ts

```typescript
export type PrintStatus = 
  | 'processing' 
  | 'sending' 
  | 'printing' 
  | 'completed' 
  | 'error';

export interface PrintJob {
  job_id: string;
  cups_job_id?: number;
  status: PrintStatus;
  message: string;
  created_at: string;
  completed_at?: string;
  result_image?: string;
}

export interface PrintStatusResponse {
  job_id: string;
  status: PrintStatus;
  message: string;
  progress: number;
  can_go_home: boolean;
}

export interface PrinterInfo {
  name: string;
  is_available: boolean;
  status: string;
}
```

### frontend/src/services/api.ts

```typescript
import { PrintJob, PrintStatusResponse } from '../types';

const API_BASE = '';

export async function printImages(
  images: string[],
  copies: number = 2
): Promise<PrintJob> {
  const response = await fetch(`${API_BASE}/api/print`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ images, copies }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '인쇄 요청 실패');
  }

  return response.json();
}

export async function getPrintStatus(
  jobId: string
): Promise<PrintStatusResponse> {
  const response = await fetch(`${API_BASE}/api/print/${jobId}/status`);

  if (!response.ok) {
    throw new Error('상태 조회 실패');
  }

  return response.json();
}

export async function getSystemStatus(): Promise<{
  online: boolean;
  printer: PrinterInfo;
}> {
  const response = await fetch(`${API_BASE}/api/status`);
  return response.json();
}
```

### frontend/src/hooks/usePrintStatus.ts

```typescript
import { useState, useEffect, useCallback } from 'react';
import { PrintStatusResponse } from '../types';
import { getPrintStatus } from '../services/api';

interface UsePrintStatusOptions {
  jobId: string | null;
  pollingInterval?: number;
  onComplete?: () => void;
  onError?: (message: string) => void;
}

export function usePrintStatus({
  jobId,
  pollingInterval = 1000,
  onComplete,
  onError,
}: UsePrintStatusOptions) {
  const [status, setStatus] = useState<PrintStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const pollStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const response = await getPrintStatus(jobId);
      setStatus(response);

      if (response.can_go_home) {
        setIsPolling(false);
        
        if (response.status === 'completed') {
          onComplete?.();
        } else if (response.status === 'error') {
          onError?.(response.message);
        }
      }
    } catch (error) {
      console.error('상태 조회 오류:', error);
    }
  }, [jobId, onComplete, onError]);

  useEffect(() => {
    if (!jobId) return;

    setIsPolling(true);

    const interval = setInterval(() => {
      if (isPolling) {
        pollStatus();
      }
    }, pollingInterval);

    // 즉시 첫 조회
    pollStatus();

    return () => clearInterval(interval);
  }, [jobId, pollingInterval, isPolling, pollStatus]);

  return {
    status,
    isPolling,
    canGoHome: status?.can_go_home ?? false,
  };
}
```

### frontend/src/pages/PreviewPage.tsx

```typescript
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { printImages } from '../services/api';
import { usePrintStatus } from '../hooks/usePrintStatus';
import { PrintJob } from '../types';
import PrintProgress from '../components/PrintProgress';

export default function PreviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const photos: string[] = location.state?.photos || [];

  const [printJob, setPrintJob] = useState<PrintJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPrinting, setIsPrinting] = useState(false);

  // 인쇄 상태 폴링
  const { status, canGoHome } = usePrintStatus({
    jobId: printJob?.job_id || null,
    pollingInterval: 1000,
    onComplete: () => {
      // 완료 시 3초 후 완료 페이지로
      setTimeout(() => {
        navigate('/complete');
      }, 3000);
    },
    onError: (message) => {
      setError(message);
      setIsPrinting(false);
    },
  });

  // 사진이 없으면 홈으로
  useEffect(() => {
    if (photos.length !== 4) {
      navigate('/');
    }
  }, [photos, navigate]);

  const handlePrint = async () => {
    if (isPrinting) return;

    setIsPrinting(true);
    setError(null);

    try {
      const job = await printImages(photos, 2);
      setPrintJob(job);
    } catch (e) {
      setError(e instanceof Error ? e.message : '인쇄 요청 실패');
      setIsPrinting(false);
    }
  };

  const handleRetry = () => {
    navigate('/camera');
  };

  const handleGoHome = () => {
    if (canGoHome || !isPrinting) {
      navigate('/');
    }
  };

  return (
    <div className="page preview-page">
      {/* 상태 표시 */}
      {status && <PrintProgress status={status} />}

      {/* 에러 메시지 */}
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {/* 미리보기 이미지 */}
      <div className="result-container">
        {printJob?.result_image ? (
          <img
            src={`data:image/jpeg;base64,${printJob.result_image}`}
            alt="합성 결과"
            className="result-image"
          />
        ) : (
          <div className="preview-grid">
            {photos.map((photo, index) => (
              <img 
                key={index} 
                src={photo} 
                alt={`Photo ${index + 1}`} 
              />
            ))}
          </div>
        )}
      </div>

      {/* 버튼 */}
      <div className="button-row">
        {!isPrinting && (
          <button 
            className="btn-secondary" 
            onClick={handleRetry}
          >
            다시 촬영
          </button>
        )}

        {!printJob ? (
          <button
            className="btn-primary"
            onClick={handlePrint}
            disabled={isPrinting}
          >
            🖨️ 인쇄하기 (2장)
          </button>
        ) : (
          <button
            className="btn-primary"
            onClick={handleGoHome}
            disabled={!canGoHome}
          >
            {canGoHome ? '처음으로' : '인쇄 중...'}
          </button>
        )}
      </div>
    </div>
  );
}
```

### frontend/src/components/PrintProgress.tsx

```typescript
import { PrintStatusResponse } from '../types';

interface PrintProgressProps {
  status: PrintStatusResponse;
}

export default function PrintProgress({ status }: PrintProgressProps) {
  const getStatusColor = () => {
    switch (status.status) {
      case 'processing':
        return '#3498db';
      case 'sending':
        return '#9b59b6';
      case 'printing':
        return '#f39c12';
      case 'completed':
        return '#27ae60';
      case 'error':
        return '#e74c3c';
      default:
        return '#95a5a6';
    }
  };

  const getStatusIcon = () => {
    switch (status.status) {
      case 'processing':
        return '⚙️';
      case 'sending':
        return '📤';
      case 'printing':
        return '🖨️';
      case 'completed':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '⏳';
    }
  };

  return (
    <div className="print-progress">
      <div className="progress-header">
        <span className="status-icon">{getStatusIcon()}</span>
        <span className="status-message">{status.message}</span>
      </div>

      <div className="progress-bar-container">
        <div
          className="progress-bar"
          style={{
            width: `${status.progress}%`,
            backgroundColor: getStatusColor(),
          }}
        />
      </div>

      <div className="progress-percentage">
        {status.progress}%
      </div>
    </div>
  );
}
```

---

## 7. Docker 구성

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    privileged: true
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./backend/output:/app/output
      - ./certs:/app/certs:ro
      - /var/run/cups:/var/run/cups
      - /dev/bus/usb:/dev/bus/usb
    environment:
      - PRINTER_NAME=${PRINTER_NAME:-Canon_CP1500}
    depends_on:
      - cups

  cups:
    image: olbat/cupsd:latest
    restart: unless-stopped
    privileged: true
    ports:
      - "631:631"
    volumes:
      - /dev/bus/usb:/dev/bus/usb
      - cups_data:/etc/cups
    environment:
      - CUPS_ADMIN_USER=admin
      - CUPS_ADMIN_PASSWORD=admin

volumes:
  cups_data:
```

### Dockerfile (통합)

```dockerfile
# Stage 1: Frontend 빌드
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + Nginx
FROM python:3.11-slim

# 시스템 패키지
RUN apt-get update && apt-get install -y \
    nginx \
    cups-client \
    libcups2-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend 복사
COPY backend/app ./app

# Frontend 빌드 결과물 복사
COPY --from=frontend-builder /app/frontend/dist /app/static

# Nginx 설정
COPY nginx.conf /etc/nginx/nginx.conf

# 시작 스크립트
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80 443

CMD ["/start.sh"]
```

### nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl;
        server_name _;

        ssl_certificate     /app/certs/cert.pem;
        ssl_certificate_key /app/certs/key.pem;

        # Frontend (React)
        location / {
            root /app/static;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # Backend API
        location /api {
            proxy_pass http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Health check
        location /health {
            proxy_pass http://127.0.0.1:8000;
        }
    }
}
```

### start.sh

```bash
#!/bin/bash

# SSL 인증서 생성 (없으면)
if [ ! -f /app/certs/cert.pem ]; then
    mkdir -p /app/certs
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /app/certs/key.pem \
        -out /app/certs/cert.pem \
        -subj "/CN=photobooth.local"
fi

# Nginx 시작
nginx

# FastAPI 시작
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 8. CUPS 프린터 설정

### setup/setup_cups.sh

```bash
#!/bin/bash
# Selphy USB 프린터 설정

echo "=== CUPS 프린터 설정 ==="

# USB 장치 확인
echo "연결된 USB 장치:"
lsusb | grep -i canon

# 프린터 추가 (Canon Selphy)
# Vendor ID: 04a9 (Canon)
sudo lpadmin -p Canon_CP1500 \
    -E \
    -v usb://Canon/SELPHY%20CP1500 \
    -m everywhere \
    -o media=4x6 \
    -o print-quality=5

# 기본 프린터 설정
sudo lpoptions -d Canon_CP1500

# 테스트
echo ""
echo "프린터 상태:"
lpstat -p -d

echo ""
echo "테스트 인쇄를 하려면:"
echo "  lp -d Canon_CP1500 test.jpg"
```

---

## 9. 최종 예산

| 항목 | 가격 |
|------|------|
| Raspberry Pi 4 (4GB) | 7만원 |
| SD카드 32GB | 1만원 |
| USB-C PD 보조배터리 (65W, 20000mAh) | 5만원 |
| Canon Selphy CP1500 | 15만원 |
| Selphy 배터리 (NB-CP2LI 또는 호환) | 3~10만원 |
| 인화지 108매 (KP-108IN) | 4만원 |
| iPad Air (보유) | 0원 |
| **합계** | **~35~42만원** |

---

## 10. 핵심 포인트 요약

### 인쇄 완료 감지 로직

```
1. POST /api/print → job_id 반환
2. Frontend가 1초마다 GET /api/print/{job_id}/status 폴링
3. Backend가 CUPS 작업 상태 모니터링
4. can_go_home: true 될 때까지 홈 버튼 비활성화
5. completed 상태 → 완료 화면 → 홈으로
```

### 홈 이동 제어

```typescript
// 인쇄 중에는 홈 이동 차단
<button 
  disabled={!canGoHome}
  onClick={handleGoHome}
>
  {canGoHome ? '처음으로' : '인쇄 중...'}
</button>
```

### USB 자동 인쇄

```python
# CUPS를 통해 다이얼로그 없이 자동 인쇄
self.conn.printFile(
    printer_name,
    str(image_path),
    "PhotoBooth",
    {"copies": "2", "media": "4x6"}
)
```

---

추가로 수정하거나 더 자세히 설명이 필요한 부분 있으면 말씀해 주세요!