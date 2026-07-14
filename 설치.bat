@echo off
chcp 65001 >nul
title AI 견적 시스템 설치
echo ============================================
echo    AI 견적 시스템 - 설치 (최초 1회)
echo ============================================
echo.

echo [1/2] 파이썬 확인 중...
py --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo  [오류] 파이썬이 설치되어 있지 않습니다.
  echo  https://www.python.org/downloads/ 에서 Python 3.11 이상을 받아
  echo  설치하실 때 반드시 "Add Python to PATH" 를 체크한 후,
  echo  이 설치.bat 을 다시 실행해 주세요.
  echo.
  pause
  exit /b
)
py --version
echo.

echo [2/2] 필요한 라이브러리 설치 중... (네트워크 상태에 따라 몇 분 소요)
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo  [오류] 라이브러리 설치 중 문제가 발생했습니다. 인터넷 연결을 확인하고 다시 시도하세요.
  pause
  exit /b
)
echo.

echo ============================================
echo    설치 완료!
echo    이제 '시작.bat' 을 더블클릭하면 실행됩니다.
echo    브라우저에서  http://localhost:8010  으로 접속
echo ============================================
echo.
pause
