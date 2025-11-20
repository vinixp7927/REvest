\
@echo off
setlocal enabledelayedexpansion

REM -------- Pure CMD bootstrap (no PowerShell required) --------

REM 1) Detect Python
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo Instale Python 3 e reinicie.
    pause
    exit /b 1
  ) else (
    set "PYTHON=py"
  )
) else (
  set "PYTHON=python"
)

REM 2) Create venv if missing
if not exist ".venv" (
  echo Criando ambiente virtual (.venv)...
  %PYTHON% -m venv .venv
  if errorlevel 1 (
    echo [ERRO] Falha ao criar a venv. Tente executar fora da pasta Downloads.
    pause
    exit /b 1
  )
)

REM 3) Activate venv
call ".venv\Scripts\activate.bat" || (
  echo [ERRO] Nao encontrei .venv\Scripts\activate.bat
  pause
  exit /b 1
)

REM 4) Install requirements
if exist "requirements.txt" (
  echo Instalando dependencias via requirements.txt...
  pip install -r requirements.txt
) else (
  echo Instalando dependencias minimas (Flask, Flask-Login, Flask-WTF)...
  pip install Flask Flask-Login Flask-WTF
)

REM 5) SECRET_KEY via Python (sem PowerShell)
for /f "usebackq tokens=*" %%i in (`python -c "import secrets; print(secrets.token_urlsafe(32))"`) do set "SECRET_KEY=%%i"
set FLASK_ENV=development

REM 6) Start app
if exist "app.py" (
  echo Iniciando o servidor Flask...
  echo URL: http://127.0.0.1:5000
  python app.py
) else (
  echo [ERRO] app.py nao encontrado na raiz do projeto.
  pause
  exit /b 1
)
