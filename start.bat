@echo off
REM Hyperliquid Trading Assistant - Start Script for Windows

echo Starting Hyperliquid Trading Assistant...
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Check if credentials.yaml exists
if not exist credentials.yaml (
    echo ERROR: credentials.yaml not found. Please run setup.bat and configure your API keys.
    pause
    exit /b 1
)

REM Check if OpenAI API key is set
REM Note: Commented out since OpenAI API key is now hardcoded in src/reasoning/llm_client.py
REM if "%OPENAI_API_KEY%"=="" (
REM     echo WARNING: OPENAI_API_KEY not set. LLM/chat features will not work.
REM     echo    Set it with: set OPENAI_API_KEY=sk-your-key-here
REM     echo.
REM )

echo Starting backend server...
start "Backend Server" cmd /k "call venv\Scripts\activate.bat && python run_backend.py --testnet"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo Starting frontend server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

REM Wait for services to start
timeout /t 3 /nobreak >nul

echo.
echo Application started successfully!
echo.
echo Frontend: http://localhost:5170
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Close the terminal windows to stop the services
echo.
pause 