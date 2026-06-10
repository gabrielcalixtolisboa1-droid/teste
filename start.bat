@echo off
chcp 65001 >nul
title Estudo IA - Assistente Local

REM Navega para a pasta onde o start.bat esta, independente de onde foi chamado
cd /d "%~dp0"

echo.
echo  ============================================
echo   Estudo IA - Assistente Local de Estudos
echo  ============================================
echo.

REM ── Verificar Python ─────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 goto sem_python

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  Python encontrado: %PYVER%
goto venv

:sem_python
echo  [ERRO] Python nao foi encontrado!
echo.
echo  1. Acesse: https://www.python.org/downloads
echo  2. Baixe e instale o Python
echo  3. IMPORTANTE: marque "Add python.exe to PATH"
echo  4. Feche este prompt e execute start.bat novamente
echo.
pause
exit /b 1

REM ── Criar ambiente virtual ────────────────────────────────────
:venv
if exist "venv" goto ativar
echo  Criando ambiente virtual...
python -m venv venv
if errorlevel 1 goto erro_venv
goto ativar

:erro_venv
echo  [ERRO] Falha ao criar ambiente virtual.
pause
exit /b 1

REM ── Ativar venv ───────────────────────────────────────────────
:ativar
call venv\Scripts\activate.bat
if errorlevel 1 goto erro_ativar
goto dependencias

:erro_ativar
echo  [ERRO] Falha ao ativar o ambiente virtual.
pause
exit /b 1

REM ── Instalar dependencias ─────────────────────────────────────
:dependencias
echo  Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 goto instalar
goto ollama

:instalar
echo  Instalando dependencias pela primeira vez...
echo  Isso so acontece uma vez, pode demorar alguns minutos.
echo.
pip install -r requirements.txt
if errorlevel 1 goto erro_pip
goto ollama

:erro_pip
echo  [ERRO] Falha ao instalar dependencias.
pause
exit /b 1

REM ── Verificar Ollama ─────────────────────────────────────────
:ollama
echo.
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto iniciar_ollama
goto pastas

:iniciar_ollama
echo  Iniciando Ollama em segundo plano...
start /b ollama serve
timeout /t 3 /nobreak >nul

REM ── Criar pastas necessarias ──────────────────────────────────
:pastas
if not exist "uploads" mkdir uploads
if not exist "chroma_db" mkdir chroma_db

REM ── Iniciar servidor ─────────────────────────────────────────
echo.
echo  ============================================
echo   Servidor em: http://localhost:8000
echo   Pressione Ctrl+C para encerrar
echo  ============================================
echo.

timeout /t 2 /nobreak >nul
start http://localhost:8000

uvicorn app:app --host 127.0.0.1 --port 8000 --reload

pause
