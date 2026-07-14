@echo off
chcp 65001 >nul
echo AI 견적 서버(포트 8010)를 종료합니다...
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue; if ($c) { $c.OwningProcess | Select-Object -Unique | ForEach-Object { Stop-Process -Id $_ -Force }; Write-Host '서버를 종료했습니다.' } else { Write-Host '실행 중인 서버가 없습니다.' }"
echo.
pause
