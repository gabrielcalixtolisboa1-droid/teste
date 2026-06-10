@echo off
chcp 65001 >nul
title Estudo IA – Assistente Local

echo.
echo  ============================================
echo   Estudo IA – Assistente Local de Estudos
echo  ============================================
echo.

REM ── Verificar Python ─────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao foi encontrado!
    echo.
    echo  1. Acesse: https://www.python.org/downloads
    echo  2. Baixe e instale o Python
    echo  3. IMPORTANTE: marque "Add python.exe to PATH"
    echo  4. Feche este prompt e execute start.bat novamente
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  Python encontrado: %PYVER%

REM ── Criar ambiente virtual ────────────────────────────────────
if not exist "venv" (
    echo  Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo  [ERRO] Falha ao criar venv. Tente: pip install virtualenv
        pause
        exit /b 1
    )
)

REM ── Ativar venv ───────────────────────────────────────────────
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERRO] Falha ao ativar o ambiente virtual.
    pause
    exit /b 1
)

REM ── Instalar dependências ─────────────────────────────────────
echo  Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo  Instalando dependencias pela primeira vez (pode demorar alguns minutos)...
    echo  Isso so acontece uma vez!
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo  [ERRO] Falha ao instalar dependencias.
        pause
        exit /b 1
    )
)

REM ── Verificar Ollama ─────────────────────────────────────────
echo.
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo  [AVISO] Ollama nao esta rodando.
    echo  Iniciando Ollama...
    start /b ollama serve
    timeout /t 3 /nobreak >nul
)

REM ── Criar pastas necessárias ──────────────────────────────────
if not exist "uploads" mkdir uploads
if not exist "chroma_db" mkdir chroma_db

REM ── Iniciar servidor ─────────────────────────────────────────
echo.
echo  ============================================
echo   Servidor iniciando em http://localhost:8000
echo   Pressione Ctrl+C para encerrar
echo  ============================================
echo.

timeout /t 2 /nobreak >nul
start http://localhost:8000

uvicorn app:app --host 127.0.0.1 --port 8000 --reload

pause
