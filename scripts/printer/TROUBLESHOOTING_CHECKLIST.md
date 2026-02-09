# Canon Selphy CP1500 Troubleshooting Checklist

PhotoBooth 프린터 문제 해결을 위한 체크리스트입니다.
네트워크 없이 오프라인 환경에서 사용할 수 있습니다.

---

## Quick Reference Commands

```bash
# USB 프린터 확인
lsusb | grep -i canon

# CUPS 프린터 상태
lpstat -p -d

# 프린터 URI 확인
lpstat -v

# 인쇄 대기열 확인
lpstat -o

# USB 드라이버 상태
lsusb -t | grep -A 2 Printer

# /dev/usb/lp* 장치 확인
ls -la /dev/usb/lp*
```

---

## Scenario 1: 프린터가 USB에서 인식되지 않음

### 증상
- `lsusb | grep -i canon` 결과 없음
- "No Canon printer detected" 메시지

### 체크리스트
- [ ] 프린터 전원이 켜져 있는지 확인
- [ ] USB 케이블이 양쪽 끝에 단단히 연결되어 있는지 확인
- [ ] USB 케이블이 **데이터 케이블**인지 확인 (충전 전용 케이블은 안 됨)
- [ ] 다른 USB 포트에 연결해 보기
- [ ] 다른 USB 케이블로 교체해 보기

### 자동 복구
```bash
# USB 장치 재바인딩
sudo modprobe usblp
for dev in /sys/bus/usb/devices/*/idVendor; do
    if [[ "$(cat $dev 2>/dev/null)" == "04a9" ]]; then
        name=$(basename $(dirname $dev))
        echo $name | sudo tee /sys/bus/usb/drivers/usb/unbind
        sleep 2
        echo $name | sudo tee /sys/bus/usb/drivers/usb/bind
    fi
done
```

---

## Scenario 2: USB 인식되지만 CUPS에서 사용 불가

### 증상
- `lsusb` 에서 프린터 보임
- `ls /dev/usb/lp*` 결과 없음
- "Waiting for printer to become available" 메시지

### 원인
`ipp-usb` 서비스가 USB를 점유하고 있음

### 체크리스트
- [ ] `systemctl status ipp-usb` 로 ipp-usb 상태 확인
- [ ] `lsusb -t` 에서 드라이버가 `usbfs`인지 확인

### 자동 복구
```bash
# ipp-usb 비활성화
sudo systemctl stop ipp-usb
sudo pkill -9 ipp-usb
sudo systemctl mask ipp-usb

# USB 재바인딩
sudo modprobe -r usblp
sudo modprobe usblp

# USB 장치 재연결
for dev in /sys/bus/usb/devices/*/idVendor; do
    if [[ "$(cat $dev 2>/dev/null)" == "04a9" ]]; then
        name=$(basename $(dirname $dev))
        echo $name | sudo tee /sys/bus/usb/drivers/usb/unbind
        sleep 2
        echo $name | sudo tee /sys/bus/usb/drivers/usb/bind
    fi
done

sleep 3
ls -la /dev/usb/lp*
```

---

## Scenario 3: 프린터가 CUPS에 등록되지 않음

### 증상
- `lsusb` 에서 프린터 보임
- `/dev/usb/lp*` 존재
- `lpstat -p` 에서 프린터 없음

### 체크리스트
- [ ] 프린터 시리얼 번호 확인
- [ ] CUPS 서비스 실행 중인지 확인

### 수동 등록
```bash
# 시리얼 번호 확인
lsusb -v 2>/dev/null | grep -A 20 "04a9:3302" | grep iSerial

# 프린터 등록 (시리얼 번호 대체 필요)
sudo lpadmin -p SelphyCP1500 \
  -E \
  -v "usb://Canon/SELPHY%20CP1500?serial=YOUR_SERIAL_HERE" \
  -m "gutenprint.5.3://canon-cp1300/expert" \
  -D "Canon Selphy CP1500" \
  -L "PhotoBooth"

# 또는 기존 PPD 사용
sudo lpadmin -p SelphyCP1500-2 \
  -E \
  -v "usb://Canon/SELPHY%20CP1500?serial=YOUR_SERIAL_HERE" \
  -P /etc/cups/ppd/SelphyCP1500.ppd

# 프린터 활성화
sudo cupsenable SelphyCP1500
sudo cupsaccept SelphyCP1500
```

---

## Scenario 4: 인쇄 작업이 대기열에 멈춤

### 증상
- `lpstat -o` 에서 작업이 "Waiting" 또는 "Held" 상태
- 프린터가 동작하지 않음

### 체크리스트
- [ ] 프린터 전원 확인
- [ ] USB 연결 확인
- [ ] 용지/잉크 확인 (프린터 LCD)
- [ ] 프린터 에러 상태 확인

### 자동 복구
```bash
# 모든 작업 취소
sudo cancel -a

# 프린터 재활성화
sudo cupsdisable SelphyCP1500
sudo cupsenable SelphyCP1500

# 또는 모든 Selphy 프린터에 대해
for p in $(lpstat -p | grep -i selphy | awk '{print $2}'); do
    sudo cupsdisable $p
    sudo cupsenable $p
    sudo cupsaccept $p
done
```

---

## Scenario 5: 프린터가 "disabled" 상태

### 증상
- `lpstat -p` 에서 "disabled" 표시
- 인쇄 작업이 거부됨

### 체크리스트
- [ ] 이전 인쇄 오류 확인
- [ ] CUPS 에러 로그 확인

### 자동 복구
```bash
# 프린터 활성화
sudo cupsenable SelphyCP1500
sudo cupsaccept SelphyCP1500

# CUPS 재시작
sudo systemctl restart cups
```

---

## Scenario 6: 멀티 프린터 - 한 대만 인식됨

### 증상
- 두 대의 프린터를 연결했지만 `lsusb`에서 한 대만 보임

### 체크리스트
- [ ] 두 프린터 모두 전원이 켜져 있는지 확인
- [ ] **각 프린터가 다른 USB 포트에 연결**되어 있는지 확인
- [ ] USB 케이블 상태 확인 (둘 다 데이터 케이블인지)
- [ ] 전원 공급형 USB 허브 사용 고려

### 확인 방법
```bash
# 모든 USB 장치 확인
lsusb

# USB 트리 구조 확인
lsusb -t

# dmesg로 USB 연결 로그 확인
dmesg | grep -i usb | tail -30
```

### 해결책
1. 각 프린터를 **서로 다른 USB 포트**에 연결
2. 필요시 **전원 공급형 USB 허브** 사용
3. USB 케이블 교체 테스트

---

## Scenario 7: CUPS 서비스가 실행되지 않음

### 증상
- `lpstat` 명령 실패
- `systemctl status cups` 에서 inactive

### 자동 복구
```bash
# CUPS 시작
sudo systemctl start cups

# 부팅 시 자동 시작 설정
sudo systemctl enable cups

# 상태 확인
systemctl status cups
```

---

## Scenario 8: PPD 파일 오류

### 증상
- "Unable to open PPD" 오류
- "Missing PPD-Adobe-4.x header" 오류

### 해결책
```bash
# 사용 가능한 드라이버 확인
lpinfo -m | grep -i selphy

# CP1300 드라이버 사용 (CP1500과 호환)
sudo lpadmin -p SelphyCP1500 \
  -m "gutenprint.5.3://canon-cp1300/expert"

# 또는 기존 프린터의 PPD 복사
sudo cp /etc/cups/ppd/SelphyCP1500.ppd /etc/cups/ppd/SelphyCP1500-2.ppd
```

---

## 종합 자동 복구 스크립트

모든 문제를 한 번에 해결 시도:

```bash
#!/bin/bash
# 종합 프린터 복구 스크립트

echo "=== PhotoBooth Printer Recovery ==="

# 1. ipp-usb 비활성화
echo "Step 1: Disabling ipp-usb..."
sudo systemctl stop ipp-usb 2>/dev/null
sudo pkill -9 ipp-usb 2>/dev/null

# 2. usblp 모듈 로드
echo "Step 2: Loading usblp module..."
sudo modprobe usblp

# 3. USB 장치 재바인딩
echo "Step 3: Rebinding USB devices..."
for dev in /sys/bus/usb/devices/*/idVendor; do
    if [[ "$(cat $dev 2>/dev/null)" == "04a9" ]]; then
        name=$(basename $(dirname $dev))
        echo "  Rebinding: $name"
        echo $name | sudo tee /sys/bus/usb/drivers/usb/unbind &>/dev/null
        sleep 1
        echo $name | sudo tee /sys/bus/usb/drivers/usb/bind &>/dev/null
    fi
done
sleep 3

# 4. CUPS 재시작
echo "Step 4: Restarting CUPS..."
sudo systemctl restart cups
sleep 2

# 5. 인쇄 대기열 정리
echo "Step 5: Clearing print queue..."
sudo cancel -a 2>/dev/null

# 6. 모든 프린터 재활성화
echo "Step 6: Re-enabling printers..."
for p in $(lpstat -p 2>/dev/null | grep -i selphy | awk '{print $2}'); do
    sudo cupsenable $p 2>/dev/null
    sudo cupsaccept $p 2>/dev/null
done

# 7. 결과 확인
echo ""
echo "=== Result ==="
echo "USB Printers:"
lsusb | grep -i "04a9:3302"
echo ""
echo "USB Devices:"
ls -la /dev/usb/lp* 2>/dev/null || echo "  None found"
echo ""
echo "CUPS Printers:"
lpstat -p 2>/dev/null | grep -i selphy || echo "  None registered"
echo ""
echo "Done!"
```

---

## USB 케이블 요구사항

### Canon Selphy CP1500
- **타입**: USB Type-A to USB Type-C
- **Pi 쪽**: USB Type-A
- **프린터 쪽**: USB Type-C
- **중요**: **데이터 전송 지원** 케이블 (충전 전용 X)
- **권장 길이**: 1~1.5m

### 확인 방법
충전 전용 케이블은 데이터 핀이 없어 프린터가 인식되지 않습니다.
케이블을 연결하고 `lsusb`에서 프린터가 보이면 데이터 케이블입니다.

---

## 유용한 로그 위치

| 로그 | 위치 |
|------|------|
| CUPS 에러 | `/var/log/cups/error_log` |
| CUPS 접근 | `/var/log/cups/access_log` |
| 시스템 로그 | `journalctl -u cups` |
| USB 로그 | `dmesg \| grep -i usb` |
| PhotoBooth | `/var/log/photobooth/printer-troubleshoot.log` |

---

## 연락처

문제가 지속되면:
1. `photobooth-manager.sh` 실행 → Printer Management → Run printer troubleshooter
2. 로그 파일 수집 후 지원 요청
