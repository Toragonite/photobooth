# PhotoBooth Scripts Directory

PhotoBooth 시스템 관리를 위한 스크립트 모음입니다.

---

## Directory Structure

```
scripts/
├── photobooth-manager.sh     # 메인 관리 인터페이스 (Interactive Menu)
├── photobooth-ctl.sh         # CLI 제어 도구
├── setup.sh                  # 초기 설치 스크립트
├── quick-setup.sh            # 빠른 설치
│
├── printer/                  # 프린터 관련 스크립트
│   ├── printer-troubleshoot.sh       # 프린터 문제 진단/복구
│   └── TROUBLESHOOTING_CHECKLIST.md  # 문제 해결 체크리스트
│
├── network/                  # 네트워크 관련 스크립트
│   ├── auto-network-mode.sh  # 자동 네트워크 모드 전환
│   ├── setup-network.sh      # 네트워크 초기 설정
│   ├── reset-network.sh      # 네트워크 리셋
│   └── test-network.sh       # 네트워크 테스트
│
├── maintenance/              # 유지보수 스크립트
│   ├── backup.sh             # 백업 (symlink)
│   ├── restore.sh            # 복원 (symlink)
│   └── watchdog.sh           # 워치독 (symlink)
│
├── setup-phases/             # 설치 단계별 스크립트
│   ├── 01-system.sh          # 시스템 패키지 설치
│   ├── 02-docker.sh          # Docker 설치
│   ├── 03-cups.sh            # CUPS 프린팅 시스템
│   ├── 04-wifi-ap.sh         # Wi-Fi AP 설정
│   ├── 05-printer.sh         # 프린터 설정
│   ├── 06-deploy.sh          # 애플리케이션 배포
│   ├── 07-services.sh        # Systemd 서비스 설정
│   ├── 08-security.sh        # 보안 설정
│   └── 09-verify.sh          # 설치 검증
│
├── systemd/                  # Systemd 유닛 파일
│   ├── photobooth.service
│   ├── photobooth-watchdog.service
│   ├── photobooth-watchdog.timer
│   ├── photobooth-backup.service
│   ├── photobooth-backup.timer
│   ├── photobooth-network.service
│   └── photobooth-welcome-print.service
│
└── utils/                    # 유틸리티 스크립트
    ├── generate-ssl.sh       # SSL 인증서 생성
    ├── configure-watchdog.sh # 하드웨어 워치독 설정
    └── configure-sd-protection.sh  # SD 카드 보호 설정
```

---

## Main Scripts

### photobooth-manager.sh (권장)
스마트폰 SSH로 쉽게 사용할 수 있는 인터랙티브 메뉴입니다.

```bash
./scripts/photobooth-manager.sh
```

기능:
- 서비스 관리 (시작/중지/재시작)
- 네트워크 관리 (AP/Client 모드 전환)
- **프린터 관리 (멀티 프린터 지원)**
- 시스템 정보 확인
- 유지보수 도구
- 빠른 조치

### photobooth-ctl.sh
CLI 기반 제어 도구입니다.

```bash
./scripts/photobooth-ctl.sh [command]

Commands:
  start       서비스 시작
  stop        서비스 중지
  restart     서비스 재시작
  status      상태 확인
  logs        로그 보기
```

---

## Printer Scripts

### printer/printer-troubleshoot.sh
프린터 문제를 진단하고 자동으로 복구합니다.

```bash
# 진단만 실행
./scripts/printer/printer-troubleshoot.sh

# 자동 복구 포함
./scripts/printer/printer-troubleshoot.sh --auto-fix

# 인터랙티브 메뉴
./scripts/printer/printer-troubleshoot.sh --menu

# 특정 프린터만 확인
./scripts/printer/printer-troubleshoot.sh --printer SelphyCP1500-2
```

기능:
- USB 프린터 감지
- ipp-usb 충돌 해결
- CUPS 서비스 상태 확인
- 프린터 등록/재등록
- 인쇄 대기열 관리
- 멀티 프린터 지원

---

## Network Scripts

### network/auto-network-mode.sh
네트워크 모드를 자동 또는 수동으로 전환합니다.

```bash
# 자동 감지
./scripts/network/auto-network-mode.sh --auto

# AP 모드 강제
./scripts/network/auto-network-mode.sh --force-ap

# Client 모드 강제
./scripts/network/auto-network-mode.sh --force-client
```

---

## Setup Scripts

초기 설치 시 사용합니다.

```bash
# 전체 설치
sudo ./scripts/setup.sh

# 빠른 설치
sudo ./scripts/quick-setup.sh

# 개별 단계 실행
sudo ./scripts/setup-phases/05-printer.sh
```

---

## Maintenance

### 백업
```bash
./scripts/backup.sh
```

### 복원
```bash
./scripts/restore.sh [backup-file]
```

### 리셋 및 재시작
```bash
./scripts/reset-and-restart.sh
```

---

## Troubleshooting Quick Reference

### 프린터가 인식되지 않음
```bash
# 1. USB 확인
lsusb | grep -i canon

# 2. ipp-usb 비활성화
sudo systemctl stop ipp-usb
sudo pkill -9 ipp-usb

# 3. usblp 모듈 로드
sudo modprobe usblp

# 4. 자동 복구 실행
./scripts/printer/printer-troubleshoot.sh --auto-fix
```

### 서비스가 시작되지 않음
```bash
# 1. 상태 확인
systemctl status photobooth.service

# 2. 로그 확인
journalctl -u photobooth.service -n 50

# 3. 재시작
sudo systemctl restart photobooth.service
```

### 네트워크 문제
```bash
# 1. 상태 확인
nmcli device status

# 2. AP 모드로 리셋
./scripts/network/auto-network-mode.sh --force-ap
```

---

## File Permissions

스크립트 실행 권한이 필요합니다:

```bash
chmod +x scripts/*.sh
chmod +x scripts/**/*.sh
```
