@echo off
cd /d "%~dp0"
echo 구매 안내 화면을 켭니다. 브라우저에서 http://127.0.0.1:8765
python -u server.py
pause
