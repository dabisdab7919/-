@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 사이트를 다시 만드는 중입니다...
echo.
where python >nul 2>nul
if %errorlevel%==0 ( python tools\build.py & goto :end )
where py >nul 2>nul
if %errorlevel%==0 ( py tools\build.py & goto :end )
echo Python 이 설치되어 있지 않습니다.
echo https://www.python.org/downloads/ 에서 설치한 뒤(설치 화면에서 "Add python.exe to PATH" 체크) 다시 실행하세요.
:end
echo.
pause
