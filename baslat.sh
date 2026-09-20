#!/usr/bin/env bash
echo "================================================================="
echo "       KURUMSAL BAYİLİK VE FRANCHISE SİSTEMİ BAŞLATICI"
echo "================================================================="
echo ""
echo "Sunucu başlatılıyor: http://localhost:8093"
echo "Yönetim Paneli: http://localhost:8093/admin"
echo ""

if command -v python3 &>/dev/null; then
    python3 server.py
elif command -v python &>/dev/null; then
    python server.py
else
    echo "Hata: Python bulunamadı!"
    exit 1
fi
