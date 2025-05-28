@echo off
echo ========================================
echo   AI 기능 확장 서비스 시작
echo ========================================

echo.
echo 1. 메인 서비스 (main.py) 시작 중...
start "Main Service" cmd /k "python main.py"

echo 2. 3초 대기 중...
timeout /t 3 /nobreak > nul

echo 3. 확장 기능 서비스 (features.py) 시작 중...
start "Features Service" cmd /k "python features.py"

echo.
echo ========================================
echo   서비스가 시작되었습니다!
echo ========================================
echo.
echo 🔗 메인 서비스: http://localhost:8000
echo 🔗 확장 서비스: http://localhost:8001
echo 📖 API 문서: 
echo    - Main: http://localhost:8000/docs
echo    - Features: http://localhost:8001/docs
echo.
echo 테스트를 실행하려면 아무 키나 누르세요...
pause > nul

echo.
echo 테스트 시작 중...
python test_features.py

echo.
echo 서비스를 종료하려면 각 창에서 Ctrl+C를 누르세요.
pause