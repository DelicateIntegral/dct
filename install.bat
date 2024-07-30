@echo off
setlocal

:: Capture the directory where the script is being executed from
set "SCRIPT_DIR=%~dp0"

:: Change to the script directory before running poetry install
cd /d "%SCRIPT_DIR%"
echo Current directory: %cd%

:: Check if Python 3.12 or newer is installed
for /f "tokens=*" %%a in ('python -c "import sys; print(sys.version_info >= (3, 12))"') do set IS_PYTHON_312=%%a

if "%IS_PYTHON_312%" == "True" (
    echo Python 3.12 or newer is installed.
) else (
    echo Python 3.12 or newer is not installed. Exiting...
    echo Press enter to exit...
    pause >nul
    exit
)

:: Ask user for installation path
set /p INSTALL_PATH=Enter the installation path: 

:: Remove any surrounding quotes from the path (if any)
set "INSTALL_PATH=%INSTALL_PATH:"=%"

:: Validate the provided path
if not exist "%INSTALL_PATH%" (
    echo The path "%INSTALL_PATH%" does not exist. Exiting...
    echo Press enter to exit...
    pause >nul
    exit
)

:: Create the dct directory
set "TOOL_PATH=%INSTALL_PATH%\dct"
if not exist "%TOOL_PATH%" (
    mkdir "%TOOL_PATH%"
)

:: Create the virtual environment
set "VENV_PATH=%USERPROFILE%\python\env\cyoaenv"
python -m venv "%VENV_PATH%"

:: Activate the virtual environment
call "%VENV_PATH%\Scripts\activate"

:: Upgrade pip and install poetry
python -m pip install --upgrade pip
pip install poetry

:: Run poetry install
poetry install
if %errorlevel% neq 0 (
    echo Poetry install failed. Exiting...
    echo Press enter to exit...
    pause >nul
    exit
)

:: Create launch-dct.bat
(
echo @echo off
echo call "%VENV_PATH%\Scripts\activate"
echo dct
echo deactivate
) > "%TOOL_PATH%\launch-dct.bat"

:: Create a desktop shortcut
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\dct.lnk"
call :CreateShortcut "%SHORTCUT_PATH%" "%TOOL_PATH%\launch-dct.bat" "%TOOL_PATH%"

:: Create a Start Menu shortcut
set "START_MENU_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\dct.lnk"
call :CreateShortcut "%START_MENU_PATH%" "%TOOL_PATH%\launch-dct.bat" "%TOOL_PATH%"

echo Done! The program has been installed at "%TOOL_PATH%\launch-dct.bat" and shortcuts created.
echo Press enter to exit...
pause >nul

:: Deactivate the virtual environment
deactivate

exit

:CreateShortcut
set SHORTCUT_FILE=%1
set TARGET_FILE=%2
set WORK_DIR=%3

powershell -command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_FILE%');$s.TargetPath='%TARGET_FILE%';$s.WorkingDirectory='%WORK_DIR%';$s.Save()"
exit /b

