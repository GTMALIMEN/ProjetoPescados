@echo off
cd /d "%~dp0\.."

echo Criando arquivos .env e .env.example...

(
echo # Banco PostgreSQL local
echo DB_HOST=127.0.0.1
echo DB_PORT=5432
echo DB_NAME=pescadosteste
echo DB_USER=postgres
echo DB_PASSWORD=12345
echo.
echo # Ambiente
echo APP_ENV=local
echo.
echo # Coleta padrao
echo DATA_INICIO_PADRAO=2000-01-01
) > .env

(
echo # Banco PostgreSQL local
echo DB_HOST=127.0.0.1
echo DB_PORT=5432
echo DB_NAME=pescadosteste
echo DB_USER=postgres
echo DB_PASSWORD=12345
echo.
echo # Ambiente
echo APP_ENV=local
echo.
echo # Coleta padrao
echo DATA_INICIO_PADRAO=2000-01-01
) > .env.example

copy /Y .env.example env.example.txt >nul

echo.
echo Arquivos criados:
echo - .env
echo - .env.example
echo - env.example.txt
echo.
echo Se voce usou outra senha no PostgreSQL, altere DB_PASSWORD no arquivo .env.
