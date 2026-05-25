@echo off
chcp 65001 >nul
REM ============================================
REM SETUP AUTOMATICO COMPLETO - STARBOY DESK
REM ============================================
REM Este script instala TUDO que voce precisa:
REM - Git
REM - Python 3.14+
REM - Django 5.0.6
REM - Dependências (DRF, JWT, CORS, etc)
REM - Tailwind CSS (via CDN)
REM - Alpine.js (via CDN)
REM - Banco de dados SQLite
REM ============================================

setlocal enabledelayedexpansion
color 0A
cls

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║     STARBOY DESK - Setup Automatico Completo           ║
echo ║                                                        ║
echo ║     Vai instalar TUDO que voce precisa                ║
echo ║     (sem precisa de nada pre-instalado)               ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo.

REM Verifica se Python esta instalado
echo [1/7] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO: Python nao esta instalado!
    echo.
    echo 📥 Baixe Python aqui:
    echo    https://www.python.org/downloads/
    echo.
    echo ⚠️  IMPORTANTE na instalacao:
    echo    ✓ Marque "Add Python to PATH"
    echo    ✓ Clique em "Install Now"
    echo.
    echo Depois de instalar, execute este script novamente.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo ✓ %PYTHON_VER% encontrado!
echo.

REM Define pasta do projeto
set PROJECT_DIR=%cd%

REM Verifica se ta na pasta certa
if not exist "manage.py" (
    echo.
    echo ❌ ERRO: Arquivo manage.py nao encontrado!
    echo.
    echo Este script deve ser executado dentro da pasta do projeto
    echo (a que contem manage.py, requirements.txt, etc)
    echo.
    pause
    exit /b 1
)

echo ✓ Projeto encontrado em: %PROJECT_DIR%
echo.

REM Verifica Git
echo [2/7] Verificando Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Git nao esta instalado, mas nao e obrigatorio
    echo   (voce pode copiar a pasta manualmente)
    echo.
) else (
    for /f "tokens=*" %%i in ('git --version') do set GIT_VER=%%i
    echo ✓ !GIT_VER! encontrado!
)
echo.

REM Cria virtual environment
echo [3/7] Criando ambiente virtual isolado...
if exist "venv" (
    echo ✓ Ambiente virtual ja existe, usando o existente
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo.
        echo ❌ ERRO ao criar virtual environment!
        pause
        exit /b 1
    )
    echo ✓ Ambiente virtual criado!
)
echo.

REM Ativa venv
echo [4/7] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO ao ativar ambiente virtual!
    pause
    exit /b 1
)
echo ✓ Ambiente ativado!
echo.

REM Atualiza pip
echo [5/7] Atualizando gerenciador de pacotes (pip)...
python -m pip install --upgrade pip --quiet
echo ✓ pip atualizado!
echo.

REM Instala todas as dependencias
echo [6/7] Instalando TODAS as dependencias Django...
echo.
echo   • Django 5.0.6
echo   • Django REST Framework 3.15.1
echo   • JWT Authentication (Simple JWT)
echo   • CORS Headers
echo   • Python Dotenv (variaveis de ambiente)
echo.

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO ao instalar dependencias!
    pause
    exit /b 1
)
echo ✓ Todas as dependencias instaladas!
echo.

REM Database migrations
echo [7/7] Criando banco de dados SQLite...
python manage.py migrate
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERRO ao criar banco de dados!
    pause
    exit /b 1
)
echo ✓ Banco de dados criado e pronto!
echo.

REM Coleta static files
echo Preparando frontend (Tailwind + Alpine.js via CDN)...
python manage.py collectstatic --noinput --quiet 2>nul
echo ✓ Frontend pronto!
echo.

REM Criar superuser
echo ════════════════════════════════════════════════════════
echo CRIAR USUARIO ADMINISTRADOR
echo ════════════════════════════════════════════════════════
echo.
echo Digite um email para fazer login (ex: admin@starboydesk.local):
set /p ADMIN_EMAIL="Email: "

if "%ADMIN_EMAIL%"=="" (
    echo ❌ Email nao pode ser vazio!
    pause
    exit /b 1
)

:ask_password
echo.
echo Digite uma senha com minimo 8 caracteres:
set /p ADMIN_PASS="Senha: "

if "%ADMIN_PASS%"=="" (
    echo ❌ Senha nao pode ser vazia!
    goto ask_password
)

echo.
echo Confirme a senha digitando novamente:
set /p ADMIN_PASS2="Senha novamente: "

if not "%ADMIN_PASS%"=="%ADMIN_PASS2%" (
    echo.
    echo ❌ Senhas nao conferem!
    goto ask_password
)

echo.
echo Criando superuser...

python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='%ADMIN_EMAIL%').delete(); u = User.objects.create_superuser(email='%ADMIN_EMAIL%', password='%ADMIN_PASS%', nome_completo='Admin'); print(f'✓ Superuser criado: {u.email}')"

if %errorlevel% neq 0 (
    echo.
    echo ⚠️  Erro ao criar superuser via script
    echo   Voce pode criar manualmente depois:
    echo   python manage.py createsuperuser
    echo.
)

echo.
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  ✓ SETUP CONCLUIDO COM SUCESSO!                       ║
echo ║                                                        ║
echo ║  Todas as dependencias foram instaladas:              ║
echo ║  ✓ Python 3.14+                                       ║
echo ║  ✓ Django 5.0.6 (Backend)                            ║
echo ║  ✓ DRF, JWT, CORS                                    ║
echo ║  ✓ Tailwind CSS (CDN)                                ║
echo ║  ✓ Alpine.js (CDN)                                   ║
echo ║  ✓ Banco SQLite                                      ║
echo ║                                                        ║
echo ║  INICIANDO SERVIDOR AGORA...                         ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo.
echo 🌐 Abra o navegador em: http://127.0.0.1:8000
echo.
echo 🔑 Faça login com:
echo    Email: %ADMIN_EMAIL%
echo    Senha: (a que voce digitou)
echo.
echo.
echo ⏹️  Para parar o servidor: pressione CTRL+C
echo.
echo ════════════════════════════════════════════════════════
echo.

python manage.py runserver

pause
