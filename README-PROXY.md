# WireGuard VPN Proxy for FastAPI

이 프로젝트는 네트워크 네임스페이스를 사용하여 FastAPI 서버만 WireGuard VPN을 통해 연결하고, 호스트 OS에는 영향을 주지 않도록 하는 프록시 시스템입니다.

## 주요 특징

- 🔒 **격리된 VPN 연결**: 네트워크 네임스페이스를 사용하여 FastAPI 서버만 VPN을 통해 연결
- 🖥️ **호스트 OS 보호**: 호스트 시스템의 네트워크 설정에 영향 없음
- 🔧 **자동 설정**: WireGuard 인터페이스 자동 생성 및 설정
- 📊 **모니터링**: 서버 상태 모니터링 및 자동 정리
- 🛡️ **안전한 종료**: Ctrl+C로 안전하게 종료 및 리소스 정리

## 시스템 요구사항

### Linux 시스템 (Ubuntu/Debian 권장)
- WireGuard 도구
- iproute2 (ip 명령어)
- iptables
- Python 3.7+
- 루트 권한

### 설치 방법

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install wireguard-tools iproute2 iptables python3 python3-pip
```

#### CentOS/RHEL:
```bash
sudo yum install epel-release
sudo yum install wireguard-tools iproute iptables python3 python3-pip
```

## 설정 파일 준비

1. WireGuard 설정 파일을 준비합니다 (예: `my-vpn.conf`):

```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY_HERE
Address = 10.0.0.2/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = YOUR_SERVER_PUBLIC_KEY_HERE
Endpoint = your-vpn-server.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

2. 실제 VPN 서비스 제공업체에서 받은 값으로 교체:
   - `YOUR_PRIVATE_KEY_HERE`: 클라이언트 개인 키
   - `YOUR_SERVER_PUBLIC_KEY_HERE`: 서버 공개 키
   - `your-vpn-server.com:51820`: VPN 서버 주소 및 포트
   - `10.0.0.2/24`: 클라이언트 IP 주소 (서버 설정에 따라 변경)

## 사용 방법

### 1. 기본 실행
```bash
sudo python3 proxy.py my-vpn.conf
```

### 2. 커스텀 설정으로 실행
```bash
sudo python3 proxy.py my-vpn.conf --interface wg1 --namespace my_vpn_ns
```

### 3. 백그라운드 실행
```bash
sudo nohup python3 proxy.py my-vpn.conf > proxy.log 2>&1 &
```

## 명령어 옵션

- `config`: WireGuard 설정 파일 경로 (필수)
- `--interface`: WireGuard 인터페이스 이름 (기본값: wg0)
- `--namespace`: 네트워크 네임스페이스 이름 (기본값: wg_ns)

## 작동 원리

1. **네트워크 네임스페이스 생성**: 격리된 네트워크 환경 생성
2. **WireGuard 인터페이스 설정**: 네임스페이스 내에 VPN 인터페이스 생성
3. **라우팅 설정**: 모든 트래픽이 VPN을 통해 라우팅되도록 설정
4. **FastAPI 서버 시작**: 네임스페이스 내에서 main.py 실행
5. **모니터링**: 서버 상태 지속적으로 모니터링

## 연결 확인

서버가 시작되면 다음 주소로 접근할 수 있습니다:
- API 엔드포인트: `http://127.0.0.1:8000`
- API 문서: `http://127.0.0.1:8000/docs`

VPN 연결 확인:
```bash
# 네임스페이스 내에서 IP 확인
sudo ip netns exec wg_ns curl ipinfo.io

# 호스트에서 IP 확인 (비교용)
curl ipinfo.io
```

## 종료 방법

### 정상 종료
```bash
# Ctrl+C 또는
sudo pkill -f "python3 proxy.py"
```

### 강제 정리 (문제 발생 시)
```bash
# 네임스페이스 삭제
sudo ip netns delete wg_ns

# WireGuard 인터페이스 삭제 (필요시)
sudo ip link delete wg0
```

## 트러블슈팅

### 1. 권한 오류
```
오류: 이 스크립트는 루트 권한이 필요합니다.
해결: sudo를 사용하여 실행
```

### 2. WireGuard 도구 없음
```
오류: 다음 도구들이 설치되어 있지 않습니다: wg, ip, iptables
해결: 필요한 패키지 설치 (위의 설치 방법 참조)
```

### 3. 설정 파일 오류
```
오류: 설정 파일에 [Interface] 섹션이 없습니다.
해결: WireGuard 설정 파일 형식 확인
```

### 4. FastAPI 서버 시작 실패
```
오류: main.py를 찾을 수 없습니다.
해결: proxy.py와 main.py가 같은 디렉토리에 있는지 확인
```

### 5. 네트워크 연결 문제
```
해결 방법:
1. VPN 서버 주소와 포트 확인
2. 방화벽 설정 확인
3. 인터넷 연결 상태 확인
```

## 보안 고려사항

1. **설정 파일 보안**: WireGuard 설정 파일에는 개인 키가 포함되어 있으므로 적절한 권한 설정 필요
   ```bash
   chmod 600 my-vpn.conf
   ```

2. **루트 권한**: 스크립트는 루트 권한이 필요하므로 신뢰할 수 있는 환경에서만 실행

3. **로그 모니터링**: 프록시 로그를 정기적으로 확인하여 비정상적인 활동 감지

## 로그 확인

프록시 실행 로그는 다음과 같이 확인할 수 있습니다:
```bash
# 실시간 로그 확인
sudo python3 proxy.py my-vpn.conf

# 백그라운드 실행 시 로그 확인
tail -f proxy.log
```

## 문제 해결을 위한 디버깅

네트워크 네임스페이스 상태 확인:
```bash
# 네임스페이스 목록
sudo ip netns list

# 네임스페이스 내 인터페이스 확인
sudo ip netns exec wg_ns ip addr

# 네임스페이스 내 라우팅 테이블 확인
sudo ip netns exec wg_ns ip route
```