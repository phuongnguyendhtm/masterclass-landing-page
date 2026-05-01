@echo off
chcp 65001 >nul
echo ========================================
echo   PUSH WEBSITE LEN GITHUB + VERCEL
echo ========================================
echo.

cd /d "D:\My_brain_antigravity\masterclass-landing-page"

echo [1/3] Dang kiem tra thay doi...
git add -A

echo [2/3] Dang luu thay doi...
git commit -m "Cap nhat website - %date% %time%"

echo [3/3] Dang day len GitHub...
git push origin main

echo.
echo ========================================
echo   XONG! Website se tu cap nhat trong 30 giay.
echo ========================================
echo.
pause
