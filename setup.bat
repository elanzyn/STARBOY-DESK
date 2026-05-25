@echo off
REM ============================================
REM SETUP AUTOMATICO - STARBOY DESK
REM ============================================
REM Este script faz download e instala tudo
REM para rodar o sistema STARBOY DESK
REM ============================================

echo.
echo ========================================
echo  STARBOY DESK - Setup Automatico
echo ========================================
echo.

REM Verifica se Python esta instalado
echo [1] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Python nao esta instalado!
    echo.
    echo Baixe Python em: https://www.python.org/downloads/
    echo IMPORTANTE: Marque "Add Python to PATH" durante instalacao
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python encontrado!
echo.

REM Define pasta do projeto
set PROJECT_DIR=%cd%\STARBOY-DESK

REM Verifica se ja existe pasta
if exist "%PROJECT_DIR%" (
    echo.
    echo [!] Pasta STARBOY-DESK ja existe em: %PROJECT_DIR%
    set /p DELETE="Quer deletar e clonar novamente? (s/n): "
    if /i "%DELETE%"=="s" (
        echo Deletando pasta existente...
        rmdir /s /q "%PROJECT_DIR%"
    ) else (
        echo OK, usando pasta existente
        goto skip_clone
    )
)

REM Clone do repositorio
echo.
echo [2] Clonando repositorio...
git clone https://github.com/elanzyn/STARBOY-DESK.git "%PROJECT_DIR%"
if %errorlevel% neq 0 (
    echo ERRO ao clonar repositorio!
    pause
    exit /b 1
)
echo [OK] Repositorio clonado!
echo.

:skip_clone

REM Entra na pasta do projeto
cd /d "%PROJECT_DIR%"
if %errorlevel% neq 0 (
    echo ERRO ao entrar na pasta: %PROJECT_DIR%
    pause
    exit /b 1
)

echo Diretorio atual: %cd%
echo.

REM Cria virtual environment
echo [3] Criando ambiente virtual...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERRO ao criar venv!
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado!
) else (
    echo [!] Ambiente virtual ja existe
)
echo.

REM Ativa venv
echo [4] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO ao ativar venv!
    pause
    exit /b 1
)
echo [OK] Ambiente ativado!
echo.

REM Instala dependencias
echo [5] Instalando dependencias (pode demorar um pouco)...
pip install --upgrade pip --quiet
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERRO ao instalar dependencias!
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas!
echo.

REM Migrations
echo [6] Rodando migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ERRO ao rodar migrations!
    pause
    exit /b 1
)
echo [OK] Migrations prontas!
echo.

REM Criar superuser
echo [7] Criando usuário de administração...
echo.
echo Digite um email para login (ex: admin@starboydesk.local):
set /p ADMIN_EMAIL="Email: "

echo Digite a senha para este usuario (minimo 8 caracteres):
set /p ADMIN_PASS="Senha: "

echo Confirme a senha:
set /p ADMIN_PASS2="Senha novamente: "

if not "%ADMIN_PASS%"=="%ADMIN_PASS2%" (
    echo ERRO: Senhas nao conferem!
    pause
    exit /b 1
)

echo.
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='%ADMIN_EMAIL%').delete(); User.objects.create_superuser(email='%ADMIN_EMAIL%', password='%ADMIN_PASS%')"

if %errorlevel% neq 0 (
    echo AVISO: Nao foi possivel criar superuser automaticamente
    echo Você pode criar manualmente depois rodando:
    echo   python manage.py createsuperuser
) else (
    echo [OK] Superuser criado com sucesso!
)
echo.

REM Coleta static files
echo [8] Preparando arquivos estáticos...
python manage.py collectstatic --noinput --quiet
echo [OK] Arquivos preparados!
echo.

REM Inicia servidor
echo ========================================
echo  SETUP CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo Iniciando servidor Django...
echo.
echo [!] O sistema estara disponivel em:
echo     http://127.0.0.1:8000
echo.
echo Para fazer login use:
echo   Email: %ADMIN_EMAIL%
echo   Senha: (a que voce digitou)
echo.
echo CTRL+C para parar o servidor
echo ========================================
echo.

python manage.py runserver

pause
