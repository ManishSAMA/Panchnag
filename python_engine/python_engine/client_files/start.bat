@echo off
setlocal enabledelayedexpansion
title Jain Panchang
cd /d "%~dp0panchang_app"

if exist ".venv\Scripts\python.exe" goto run

echo First run: setting up Jain Panchang. This needs internet and takes a few minutes.
echo.
set "PY="

:: 1. Try Python launcher (py)
for %%V in (-3.14 -3.13 -3.12 -3.11 -3) do (
    py %%V -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PY=py %%V"
        goto found
    )
)

:: 2. Try python in PATH
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    goto found
)

:: 3. Scan common installation folders
for /d %%D in (
    "C:\Users\Als\AppData\Local\Programs\Python\Python3*"
    "%LOCALAPPDATA%\Programs\Python\Python3*"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python3*"
    "C:\Users\*\AppData\Local\Programs\Python\Python3*"
    "%ProgramFiles%\Python3*"
    "%ProgramFiles(x86)%\Python3*"
    "%SystemDrive%\Python3*"
    "C:\Python3*"
) do (
    if exist "%%~D\python.exe" (
        "%%~D\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PY="%%~D\python.exe""
            goto found
        )
    )
)

:: 4. Query Windows Registry for registered Python installations
for /f "tokens=2*" %%A in ('reg query "HKCU\Software\Python\PythonCore" /s /v "InstallPath" 2^>nul ^| findstr /i "InstallPath"') do (
    if exist "%%~Bpython.exe" (
        "%%~Bpython.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PY="%%~Bpython.exe""
            goto found
        )
    )
    if exist "%%~B\python.exe" (
        "%%~B\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PY="%%~B\python.exe""
            goto found
        )
    )
)

for /f "tokens=2*" %%A in ('reg query "HKLM\Software\Python\PythonCore" /s /v "InstallPath" 2^>nul ^| findstr /i "InstallPath"') do (
    if exist "%%~Bpython.exe" (
        "%%~Bpython.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PY="%%~Bpython.exe""
            goto found
        )
    )
    if exist "%%~B\python.exe" (
        "%%~B\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PY="%%~B\python.exe""
            goto found
        )
    )
)

:: 5. Fallback: prompt the user for custom path
echo Python was not found in PATH or standard installation folders.
set /p "CUSTOM_PY=If Python is installed, enter the path to python.exe [or press Enter to cancel]: "
if defined CUSTOM_PY (
    set "CUSTOM_PY=!CUSTOM_PY:"=!"
    if exist "!CUSTOM_PY!" (
        "!CUSTOM_PY!" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PY="!CUSTOM_PY!""
            goto found
        )
    )
)

echo.
echo Python [3.11, 3.12, 3.13, or 3.14] is required but was not found.
echo Install it from https://www.python.org/downloads/
echo [tick "Add python.exe to PATH" in the installer], then run start.bat again.
echo.
pause
exit /b 1

:found
echo Creating virtual environment using !PY!...
!PY! -m venv .venv || goto fail
".venv\Scripts\python.exe" -m pip install --upgrade pip || goto fail
".venv\Scripts\python.exe" -m pip install --find-links wheels -r requirements.txt || goto fail
echo.
echo Setup complete.

:run
echo Starting Jain Panchang. Your browser will open shortly.
echo Keep this window open while you use the app; close it to stop.
echo.
".venv\Scripts\python.exe" run_client.py
pause
exit /b 0

:fail
echo.
echo Setup failed. Check your internet connection and the messages above,
echo then run start.bat again.
if exist ".venv" rmdir /s /q ".venv"
pause
exit /b 1
