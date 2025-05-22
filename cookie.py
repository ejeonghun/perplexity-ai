import platform
import browser_cookie3 # type: ignore
import os
import sqlite3
import json
import configparser
import glob
import re
import tempfile
import shutil
from pathlib import Path

# Define a set of common browser functions to try from browser_cookie3
# This helps in iterating and also if some browsers are not available on a particular OS.
SUPPORTED_BROWSERS_FUNCTIONS = [
    browser_cookie3.chrome,
    browser_cookie3.firefox,
    browser_cookie3.edge,
    browser_cookie3.safari,
    browser_cookie3.chromium,
    browser_cookie3.opera,
    browser_cookie3.brave,
    browser_cookie3.vivaldi,
    # Add other browser functions from browser_cookie3 if needed
]

def find_firefox_profile_directory():
    """Docker 환경에서 Firefox 프로필 디렉토리를 찾습니다."""
    firefox_dir = os.environ.get('FIREFOX_PROFILE_DIR', '/root/.mozilla/firefox')
    
    if not os.path.exists(firefox_dir):
        print(f"[browser_cookie_fetcher] Firefox 디렉토리를 찾을 수 없습니다: {firefox_dir}")
        return None
        
    # profiles.ini 파일 찾기
    profiles_ini_path = os.path.join(firefox_dir, 'profiles.ini')
    if os.path.exists(profiles_ini_path):
        config = configparser.ConfigParser()
        config.read(profiles_ini_path)
        
        # Default 또는 첫 번째 프로필 섹션 찾기
        for section in config.sections():
            if section.startswith('Profile') and config.has_option(section, 'Path'):
                profile_path = config.get(section, 'Path')
                if config.has_option(section, 'IsRelative') and config.getboolean(section, 'IsRelative'):
                    profile_path = os.path.join(firefox_dir, profile_path)
                print(f"[browser_cookie_fetcher] Firefox 프로필 디렉토리 발견: {profile_path}")
                return profile_path
    
    # profiles.ini가 없는 경우 디렉토리 패턴으로 찾기
    pattern = os.path.join(firefox_dir, "*.default*")
    profiles = glob.glob(pattern)
    if profiles:
        print(f"[browser_cookie_fetcher] Firefox 프로필 디렉토리 발견: {profiles[0]}")
        return profiles[0]
        
    print(f"[browser_cookie_fetcher] Firefox 프로필 디렉토리를 찾을 수 없습니다.")
    return None

def get_firefox_cookies_direct():
    """
    Docker 환경에서 Firefox 쿠키 파일에 직접 접근하여 perplexity.ai 쿠키를 가져옵니다.
    """
    profile_dir = find_firefox_profile_directory()
    if not profile_dir:
        return {}
        
    cookies_file = os.path.join(profile_dir, 'cookies.sqlite')
    if not os.path.exists(cookies_file):
        print(f"[browser_cookie_fetcher] Firefox 쿠키 파일을 찾을 수 없습니다: {cookies_file}")
        return {}
        
    # SQLite 파일을 임시 위치에 복사 (파일이 잠겨있을 수 있음)
    temp_dir = tempfile.mkdtemp()
    temp_cookies_file = os.path.join(temp_dir, 'cookies.sqlite')
    
    try:
        shutil.copy2(cookies_file, temp_cookies_file)
        
        # 쿠키 데이터 조회
        conn = sqlite3.connect(temp_cookies_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, value FROM moz_cookies WHERE host LIKE '%perplexity.ai'"
        )
        
        cookies_found = {}
        for name, value in cursor.fetchall():
            cookies_found[name] = value
            
        cursor.close()
        conn.close()
        
        if cookies_found:
            print(f"[browser_cookie_fetcher] Firefox에서 {len(cookies_found)}개의 perplexity.ai 쿠키를 직접 추출했습니다.")
        return cookies_found
        
    except Exception as e:
        print(f"[browser_cookie_fetcher] Firefox 쿠키 추출 중 오류 발생: {e}")
        return {}
    finally:
        # 임시 파일 정리
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def is_docker():
    """현재 환경이 Docker인지 확인합니다."""
    # Docker 환경 확인 방법 1: /.dockerenv 파일 존재 여부
    if os.path.exists('/.dockerenv'):
        return True
        
    # Docker 환경 확인 방법 2: cgroup 정보 확인
    try:
        with open('/proc/1/cgroup', 'r') as file:
            return 'docker' in file.read()
    except:
        pass
        
    return False

def get_perplexity_cookies() -> dict:
    '''
    Attempts to fetch cookies for the domain ".perplexity.ai" from various installed browsers.

    Returns:
        A dictionary of cookie_name: cookie_value pairs if found, otherwise an empty dictionary.
    '''
    cookies_found = {}
    os_name = platform.system()
    print(f"[browser_cookie_fetcher] Detected OS: {os_name}")
    
    # Docker 환경에서는 직접 파일 접근 방법 시도
    if is_docker():
        print("[browser_cookie_fetcher] Docker 환경 감지됨, 직접 쿠키 파일 접근을 시도합니다.")
        
        # Firefox 쿠키 직접 접근 시도
        firefox_cookies = get_firefox_cookies_direct()
        if firefox_cookies:
            return firefox_cookies
    
    # 일반적인 방법으로 시도
    domains_to_try = [".perplexity.ai", "perplexity.ai", "www.perplexity.ai"]
    
    for domain in domains_to_try:
        print(f"[browser_cookie_fetcher] {domain} 도메인 쿠키 검색 중...")
        for browser_func in SUPPORTED_BROWSERS_FUNCTIONS:
            try:
                print(f"[browser_cookie_fetcher] 브라우저 시도 중: {browser_func.__name__}...")
                # browser_cookie3 함수는 기본적으로 모든 도메인에 대한 쿠키를 로드합니다.
                cj = browser_func(domain_name=domain)
                
                for cookie in cj:
                    if "perplexity" in cookie.domain:  # 올바른 도메인인지 확인
                        cookies_found[cookie.name] = cookie.value
                
                if cookies_found:
                    print(f"[browser_cookie_fetcher] {browser_func.__name__}에서 {domain}에 대한 {len(cookies_found)}개의 쿠키를 찾았습니다.")
                    # 원하는 경우 여러 브라우저에서 쿠키를 합치는 대신 첫 번째 성공 시 반환
                    return cookies_found 
            except browser_cookie3.BrowserCookieError as e:
                print(f"[browser_cookie_fetcher] {browser_func.__name__}에서 쿠키를 찾을 수 없거나 오류 발생: {e}")
            except Exception as e:
                # 예: 브라우저가 설치되지 않은 경우 또는 라이브러리에 예상치 못한 문제가 있는 경우
                print(f"[browser_cookie_fetcher] {browser_func.__name__}의 쿠키 접근 중 오류 발생: {e}")

    # 환경 변수에서 쿠키 가져오기 시도 (Docker 환경에서 유용)
    if not cookies_found:
        print("[browser_cookie_fetcher] 환경 변수에서 perplexity.ai 쿠키 검색 중...")
        for key, value in os.environ.items():
            if key.startswith('PERPLEXITY_COOKIE_'):
                cookie_name = key.replace('PERPLEXITY_COOKIE_', '')
                cookies_found[cookie_name] = value
        
        if cookies_found:
            print(f"[browser_cookie_fetcher] 환경 변수에서 {len(cookies_found)}개의 쿠키를 찾았습니다.")
            return cookies_found

    if not cookies_found:
        print("[browser_cookie_fetcher] 어떤 지원되는 브라우저에서도 perplexity.ai 쿠키를 찾을 수 없습니다.")
    
    return cookies_found

if __name__ == '__main__':
    # 모듈을 직접 테스트
    print("perplexity.ai 쿠키 가져오기 시도 중...")
    cookies = get_perplexity_cookies()
    if cookies:
        print("\n가져온 쿠키:")
        for name, value in cookies.items():
            print(f"  {name}: {value[:5]}...{value[-5:] if len(value) > 10 else value}")  # 쿠키 값 일부만 표시
    else:
        print("\n쿠키를 찾을 수 없습니다.")
