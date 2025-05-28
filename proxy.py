#!/usr/bin/env python3
"""
WireGuard VPN Proxy for FastAPI Server
네트워크 네임스페이스를 사용하여 FastAPI 서버만 VPN을 통해 연결
"""

import os
import sys
import subprocess
import time
import signal
import argparse
import json
import logging
from pathlib import Path
from typing import Optional
import tempfile
import shutil

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WireGuardProxy:
    def __init__(self, config_file: str, interface_name: str = "wg0", namespace_name: str = "wg_ns"):
        self.config_file = config_file
        self.interface_name = interface_name
        self.namespace_name = namespace_name
        self.fastapi_process = None
        self.temp_config_file = None
        
    def check_root_privileges(self):
        """루트 권한 확인"""
        if os.geteuid() != 0:
            logger.error("이 스크립트는 루트 권한이 필요합니다. sudo를 사용해주세요.")
            return False
        return True
    
    def check_dependencies(self):
        """필요한 도구들이 설치되어 있는지 확인"""
        dependencies = ['wg', 'ip', 'iptables']
        missing = []
        
        for dep in dependencies:
            if shutil.which(dep) is None:
                missing.append(dep)
        
        if missing:
            logger.error(f"다음 도구들이 설치되어 있지 않습니다: {', '.join(missing)}")
            logger.info("Ubuntu/Debian: sudo apt install wireguard-tools iproute2 iptables")
            logger.info("CentOS/RHEL: sudo yum install wireguard-tools iproute iptables")
            return False
        
        return True
    
    def validate_config(self):
        """WireGuard 설정 파일 유효성 검사"""
        if not os.path.exists(self.config_file):
            logger.error(f"설정 파일을 찾을 수 없습니다: {self.config_file}")
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
                
            # 기본 섹션 확인
            if '[Interface]' not in content:
                logger.error("설정 파일에 [Interface] 섹션이 없습니다.")
                return False
                
            if '[Peer]' not in content:
                logger.error("설정 파일에 [Peer] 섹션이 없습니다.")
                return False
                
            logger.info("WireGuard 설정 파일 유효성 검사 통과")
            return True
            
        except Exception as e:
            logger.error(f"설정 파일 읽기 오류: {e}")
            return False
    
    def run_command(self, command: list, check_output: bool = False, namespace: bool = False):
        """명령어 실행"""
        if namespace:
            command = ['ip', 'netns', 'exec', self.namespace_name] + command
            
        try:
            if check_output:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            else:
                subprocess.run(command, check=True)
                return True
        except subprocess.CalledProcessError as e:
            logger.error(f"명령어 실행 실패: {' '.join(command)}")
            logger.error(f"오류: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(f"stderr: {e.stderr}")
            return False
    
    def create_namespace(self):
        """네트워크 네임스페이스 생성"""
        logger.info(f"네트워크 네임스페이스 '{self.namespace_name}' 생성 중...")
        
        # 기존 네임스페이스가 있으면 삭제
        self.cleanup_namespace()
        
        # 새 네임스페이스 생성
        if not self.run_command(['ip', 'netns', 'add', self.namespace_name]):
            return False
            
        # 루프백 인터페이스 활성화
        if not self.run_command(['ip', 'link', 'set', 'lo', 'up'], namespace=True):
            return False
            
        logger.info("네트워크 네임스페이스 생성 완료")
        return True
    
    def setup_wireguard(self):
        """WireGuard 인터페이스 설정"""
        logger.info("WireGuard 인터페이스 설정 중...")
        
        # WireGuard 인터페이스 생성
        if not self.run_command(['ip', 'link', 'add', 'dev', self.interface_name, 'type', 'wireguard']):
            return False
        
        # 네임스페이스로 인터페이스 이동
        if not self.run_command(['ip', 'link', 'set', self.interface_name, 'netns', self.namespace_name]):
            return False
        
        # WireGuard 설정 적용
        if not self.run_command(['wg', 'setconf', self.interface_name, self.config_file], namespace=True):
            return False
        
        # 설정 파일에서 IP 주소 추출 및 설정
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            # Address 라인 찾기
            for line in content.split('\n'):
                if line.strip().startswith('Address'):
                    address = line.split('=')[1].strip()
                    logger.info(f"인터페이스 IP 주소 설정: {address}")
                    if not self.run_command(['ip', 'addr', 'add', address, 'dev', self.interface_name], namespace=True):
                        return False
                    break
        except Exception as e:
            logger.error(f"IP 주소 설정 실패: {e}")
            return False
        
        # 인터페이스 활성화
        if not self.run_command(['ip', 'link', 'set', self.interface_name, 'up'], namespace=True):
            return False
        
        logger.info("WireGuard 인터페이스 설정 완료")
        return True
    
    def setup_routing(self):
        """라우팅 테이블 설정"""
        logger.info("라우팅 설정 중...")
        
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            # Endpoint에서 게이트웨이 정보 추출
            for line in content.split('\n'):
                if line.strip().startswith('Endpoint'):
                    endpoint = line.split('=')[1].strip()
                    server_ip = endpoint.split(':')[0]
                    logger.info(f"VPN 서버: {server_ip}")
                    
                    # 기본 라우트를 WireGuard 인터페이스로 설정
                    if not self.run_command(['ip', 'route', 'add', 'default', 'dev', self.interface_name], namespace=True):
                        return False
                    break
        except Exception as e:
            logger.error(f"라우팅 설정 실패: {e}")
            return False
        
        logger.info("라우팅 설정 완료")
        return True
    
    def start_fastapi_server(self):
        """네임스페이스 내에서 FastAPI 서버 시작"""
        logger.info("FastAPI 서버 시작 중...")
        
        # 현재 디렉토리의 main.py 경로
        main_py_path = os.path.join(os.path.dirname(__file__), 'main.py')
        
        if not os.path.exists(main_py_path):
            logger.error(f"main.py를 찾을 수 없습니다: {main_py_path}")
            return False
        
        # 네임스페이스 내에서 FastAPI 서버 실행
        command = [
            'ip', 'netns', 'exec', self.namespace_name,
            'python3', main_py_path
        ]
        
        try:
            # 환경 변수 복사
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(__file__)
            
            self.fastapi_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            # 서버 시작 대기
            time.sleep(3)
            
            if self.fastapi_process.poll() is None:
                logger.info("FastAPI 서버가 네임스페이스 내에서 성공적으로 시작되었습니다.")
                logger.info("서버 주소: http://127.0.0.1:8000")
                logger.info("API 문서: http://127.0.0.1:8000/docs")
                return True
            else:
                stdout, stderr = self.fastapi_process.communicate()
                logger.error("FastAPI 서버 시작 실패")
                if stderr:
                    logger.error(f"오류: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"FastAPI 서버 시작 중 오류: {e}")
            return False
    
    def cleanup_namespace(self):
        """네트워크 네임스페이스 정리"""
        try:
            # 네임스페이스 존재 확인
            result = subprocess.run(['ip', 'netns', 'list'], capture_output=True, text=True)
            if self.namespace_name in result.stdout:
                logger.info(f"네트워크 네임스페이스 '{self.namespace_name}' 삭제 중...")
                subprocess.run(['ip', 'netns', 'delete', self.namespace_name], check=False)
        except Exception as e:
            logger.warning(f"네임스페이스 정리 중 오류 (무시됨): {e}")
    
    def cleanup(self):
        """모든 리소스 정리"""
        logger.info("리소스 정리 중...")
        
        # FastAPI 프로세스 종료
        if self.fastapi_process:
            try:
                self.fastapi_process.terminate()
                self.fastapi_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.fastapi_process.kill()
            except Exception as e:
                logger.warning(f"FastAPI 프로세스 종료 중 오류: {e}")
        
        # 네임스페이스 정리
        self.cleanup_namespace()
        
        # 임시 파일 정리
        if self.temp_config_file and os.path.exists(self.temp_config_file):
            os.remove(self.temp_config_file)
        
        logger.info("정리 완료")
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"시그널 {signum} 받음. 정리 중...")
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """메인 실행 함수"""
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # 사전 검사
            if not self.check_root_privileges():
                return False
            
            if not self.check_dependencies():
                return False
            
            if not self.validate_config():
                return False
            
            # WireGuard 설정
            if not self.create_namespace():
                return False
            
            if not self.setup_wireguard():
                return False
            
            if not self.setup_routing():
                return False
            
            # FastAPI 서버 시작
            if not self.start_fastapi_server():
                return False
            
            logger.info("프록시 서버가 성공적으로 시작되었습니다!")
            logger.info("Ctrl+C로 종료할 수 있습니다.")
            
            # 서버 프로세스 모니터링
            while True:
                if self.fastapi_process.poll() is not None:
                    logger.error("FastAPI 서버가 종료되었습니다.")
                    break
                time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
        finally:
            self.cleanup()
        
        return True

def main():
    parser = argparse.ArgumentParser(description='WireGuard VPN Proxy for FastAPI')
    parser.add_argument('config', help='WireGuard 설정 파일 경로')
    parser.add_argument('--interface', default='wg0', help='WireGuard 인터페이스 이름 (기본값: wg0)')
    parser.add_argument('--namespace', default='wg_ns', help='네트워크 네임스페이스 이름 (기본값: wg_ns)')
    
    args = parser.parse_args()
    
    # 설정 파일 경로 확인
    config_path = os.path.abspath(args.config)
    if not os.path.exists(config_path):
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        return False
    
    # 프록시 실행
    proxy = WireGuardProxy(config_path, args.interface, args.namespace)
    return proxy.run()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)