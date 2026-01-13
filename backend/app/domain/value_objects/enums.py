"""Enumeration value objects."""

from enum import Enum


class Language(str, Enum):
    """Supported languages."""

    KOREAN = "ko"
    ENGLISH = "en"

    @property
    def display_name(self) -> str:
        return {
            self.KOREAN: "한국어",
            self.ENGLISH: "English",
        }[self]


class SessionStatus(str, Enum):
    """Photo session status."""

    ACTIVE = "active"
    COMPLETE = "complete"
    PRINTED = "printed"
    ABANDONED = "abandoned"


class PrintStatus(str, Enum):
    """Print job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY_PENDING = "retry_pending"

    @property
    def is_terminal(self) -> bool:
        return self in (self.COMPLETED, self.FAILED, self.CANCELLED)

    @property
    def is_error(self) -> bool:
        return self in (self.FAILED,)

    @property
    def display_name(self) -> str:
        return {
            self.PENDING: "Pending",
            self.PROCESSING: "Processing",
            self.PRINTING: "Printing",
            self.COMPLETED: "Completed",
            self.FAILED: "Failed",
            self.CANCELLED: "Cancelled",
            self.RETRY_PENDING: "Retrying",
        }[self]

    @property
    def display_name_ko(self) -> str:
        return {
            self.PENDING: "대기 중",
            self.PROCESSING: "처리 중",
            self.PRINTING: "인쇄 중",
            self.COMPLETED: "완료",
            self.FAILED: "실패",
            self.CANCELLED: "취소됨",
            self.RETRY_PENDING: "재시도 중",
        }[self]


class ErrorCode(str, Enum):
    """Error codes for print jobs."""

    # Printer errors (retryable)
    PRINTER_OFFLINE = "printer_offline"
    PRINTER_BUSY = "printer_busy"
    PRINTER_PAPER_EMPTY = "paper_empty"
    PRINTER_INK_EMPTY = "ink_empty"
    PRINTER_DOOR_OPEN = "door_open"
    PRINTER_PAPER_JAM = "paper_jam"

    # CUPS errors (retryable)
    CUPS_UNAVAILABLE = "cups_unavailable"
    CUPS_REJECTED = "cups_rejected"

    # Processing errors (not retryable)
    PROCESSING_ERROR = "processing_error"
    INVALID_IMAGE = "invalid_image"
    STORAGE_FULL = "storage_full"
    TIMEOUT = "timeout"

    @property
    def is_retryable(self) -> bool:
        return self in {
            self.PRINTER_OFFLINE,
            self.PRINTER_BUSY,
            self.PRINTER_PAPER_EMPTY,
            self.PRINTER_INK_EMPTY,
            self.CUPS_UNAVAILABLE,
            self.CUPS_REJECTED,
        }

    @property
    def user_message(self) -> str:
        messages = {
            self.PRINTER_OFFLINE: "Printer is offline. Please check the connection.",
            self.PRINTER_BUSY: "Printer is busy. Please wait.",
            self.PRINTER_PAPER_EMPTY: "Please add paper to the printer.",
            self.PRINTER_INK_EMPTY: "Please replace the ink cartridge.",
            self.PRINTER_DOOR_OPEN: "Please close the printer door.",
            self.PRINTER_PAPER_JAM: "Paper jam detected. Please remove jammed paper.",
            self.CUPS_UNAVAILABLE: "Print service unavailable. Retrying...",
            self.CUPS_REJECTED: "Print job rejected. Retrying...",
            self.PROCESSING_ERROR: "Failed to process images.",
            self.INVALID_IMAGE: "Invalid image data.",
            self.STORAGE_FULL: "Storage full. Contact administrator.",
            self.TIMEOUT: "Print job timed out.",
        }
        return messages.get(self, "An error occurred.")

    @property
    def user_message_ko(self) -> str:
        messages = {
            self.PRINTER_OFFLINE: "프린터가 오프라인입니다. 연결을 확인하세요.",
            self.PRINTER_BUSY: "프린터가 사용 중입니다. 잠시 기다려주세요.",
            self.PRINTER_PAPER_EMPTY: "용지를 넣어주세요.",
            self.PRINTER_INK_EMPTY: "잉크 카트리지를 교체해주세요.",
            self.PRINTER_DOOR_OPEN: "프린터 문을 닫아주세요.",
            self.PRINTER_PAPER_JAM: "용지 걸림이 발생했습니다. 걸린 용지를 제거해주세요.",
            self.CUPS_UNAVAILABLE: "인쇄 서비스를 사용할 수 없습니다. 재시도 중...",
            self.CUPS_REJECTED: "인쇄 작업이 거부되었습니다. 재시도 중...",
            self.PROCESSING_ERROR: "이미지 처리에 실패했습니다.",
            self.INVALID_IMAGE: "잘못된 이미지 데이터입니다.",
            self.STORAGE_FULL: "저장 공간이 부족합니다. 관리자에게 문의하세요.",
            self.TIMEOUT: "인쇄 작업 시간이 초과되었습니다.",
        }
        return messages.get(self, "오류가 발생했습니다.")
