@echo off
chcp 65001 >nul
echo =================================================================
echo        KURUMSAL BAYİLİK VE FRANCHISE SİSTEMİ BAŞLATICI
echo =================================================================
echo.
echo Sunucu hazırlanıyor ve başlatılıyor...
echo Port: 8093
echo.
start "" http://localhost:8093
python server.py
pause
