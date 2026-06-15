@echo off
cd /d "%~dp0\.."

if not exist .env (
    copy .env.example .env
    echo .env criado a partir de .env.example
) else (
    echo .env ja existe.
)

echo.
echo Ajuste DB_PASSWORD, DB_NAME etc se necessario.
notepad .env
pause
