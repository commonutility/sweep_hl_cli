@echo off
REM Hyperliquid Trading Assistant - Setup Script for Windows

echo Setting up Hyperliquid Trading Assistant...
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3 is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)
python --version
echo Python found

REM Check Node.js version
echo.
echo Checking Node.js version...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed. Please install Node.js 16 or higher.
    pause
    exit /b 1
)
node --version
echo Node.js found

REM Create virtual environment
echo.
echo Creating Python virtual environment...
python -m venv venv
echo Virtual environment created

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo.
echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
echo Python dependencies installed

REM Install frontend dependencies
echo.
echo Installing frontend dependencies...
cd frontend
call npm install
cd ..
echo Frontend dependencies installed

REM Create credentials file if it doesn't exist
echo.
if not exist credentials.yaml (
    echo Creating credentials.yaml from template...
    copy credentials.yaml.template credentials.yaml
    echo credentials.yaml created
    echo.
    echo IMPORTANT: Edit credentials.yaml with your API keys before running the application!
) else (
    echo credentials.yaml already exists
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env from example...
    copy env.example .env
    echo .env created
    echo.
    echo OPTIONAL: Edit .env if you want to override default settings
) else (
    echo .env already exists
)

REM Create database directory if it doesn't exist
echo.
if not exist database (
    echo Creating database directory...
    mkdir database
    echo Database directory created
) else (
    echo Database directory already exists
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit credentials.yaml with your Hyperliquid API keys
echo 2. Run the application:
echo    - Backend: python run_backend.py --testnet
echo    - Frontend: cd frontend ^&^& npm run dev
echo.
echo For detailed instructions, see README.md
pause 