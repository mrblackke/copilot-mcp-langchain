@echo off
REM Ask Terminal Chat for Windows
REM Usage: 
REM   ask.bat "question"                 - Simple question mode
REM   ask.bat "command" "question"       - Command analysis mode
REM   ask.bat install                    - Install global ask command
REM   ask.bat uninstall                  - Remove global ask command
REM   ask.bat help                       - Show help

setlocal enabledelayedexpansion

REM Check for special commands first
if "%~1"=="install" goto :install_ask
if "%~1"=="uninstall" goto :uninstall_ask
if "%~1"=="help" goto :show_help
if "%~1"=="" goto :show_help

REM Function to ensure virtual environment is activated
call :ensure_virtual_env

REM Set UTF-8 code page
chcp 65001 >nul

REM Find and change to project root directory
call :find_project_root
cd /d "!project_root!"

if "%~2"=="" (
    REM Simple question mode
    set "question=%~1"
    
    echo Question: !question!
    
    REM Get system information
    call :get_system_info
    
    REM Create temporary file for JSON to avoid escaping issues
    set "tempfile=%TEMP%\gpt_temp_%RANDOM%.json"
    
    REM Create JSON content for simple question with system info
    set "json_content={\"command\":\"echo 'Simple question mode'\",\"command_output\":\"This is a direct question to the LLM without executing any command.\",\"question\":\"!question!\",\"system_info\":\"!system_info!\"}"
    
    REM Call MCP tool with UTF-8 encoding - pass JSON as argument
    set PYTHONIOENCODING=utf-8
    python -m mcp_server.run run lng_terminal_chat "!json_content!" > "%TEMP%\gpt_result.txt" 2>&1
    set "exitcode=!errorlevel!"
    
    REM Clean up temp file (if exists)
    if exist "!tempfile!" del "!tempfile!" >nul 2>&1
    
    if !exitcode! neq 0 (
        echo Error:
        type "%TEMP%\gpt_result.txt"
        del "%TEMP%\gpt_result.txt" >nul 2>&1
        exit /b 1
    )
    
    REM Extract and display result more robustly
    set "found_result="
    echo|set /p="Answer: "
    for /f "usebackq delims=" %%i in ("%TEMP%\gpt_result.txt") do (
        set "line=%%i"
        if "!line:📤 Result:=!" neq "!line!" set "found_result=1"
        if "!line:Result:=!" neq "!line!" set "found_result=1"
        if defined found_result (
            if "!line!" neq "" if "!line:Result:=!" equ "!line!" if "!line:📤 Result:=!" equ "!line!" (
                echo %%i
            )
        )
    )
    
    del "%TEMP%\gpt_result.txt" >nul 2>&1
    exit /b 0
    
) else (
    REM Command analysis mode
    set "command=%~1"
    set "question=%~2"
    
    echo Question: !question!
    echo ^> !command!
    
    REM Execute command and capture output
    !command! > "%TEMP%\cmd_output.txt" 2>&1
    set "cmd_exitcode=!errorlevel!"
    
    REM Display command output
    echo.
    type "%TEMP%\cmd_output.txt"
    echo.
    
    REM Get system information
    call :get_system_info
    
    REM Read command output for JSON (read into variable)
    set "output="
    for /f "usebackq delims=" %%i in ("%TEMP%\cmd_output.txt") do (
        if defined output (
            set "output=!output! %%i"
        ) else (
            set "output=%%i"
        )
    )
    
    REM Escape quotes and backslashes in output for JSON
    set "output=!output:\=\\!"
    set "output=!output:"=\"!"
    
    REM Escape quotes and backslashes in command for JSON  
    set "command=!command:"=\"!"
    set "command=!command:\=\\!"
    
    REM Create JSON content with proper escaping including system info
    set "json_content={\"command\":\"!command!\",\"command_output\":\"!output!\",\"question\":\"!question!\",\"system_info\":\"!system_info!\"}"
    
    REM Call MCP tool with UTF-8 encoding - pass JSON as argument
    set PYTHONIOENCODING=utf-8
    python -m mcp_server.run run lng_terminal_chat "!json_content!" > "%TEMP%\gpt_result.txt" 2>&1
    set "exitcode=!errorlevel!"
    
    REM Clean up temp files
    del "%TEMP%\cmd_output.txt" >nul 2>&1
    
    if !exitcode! neq 0 (
        echo Error:
        type "%TEMP%\gpt_result.txt"
        del "%TEMP%\gpt_result.txt" >nul 2>&1
        exit /b 1
    )
    
    REM Extract and display result
    set "found_result="
    echo|set /p="Answer: "
    for /f "usebackq delims=" %%i in ("%TEMP%\gpt_result.txt") do (
        set "line=%%i"
        if "!line:📤 Result:=!" neq "!line!" set "found_result=1"
        if "!line:Result:=!" neq "!line!" set "found_result=1"
        if defined found_result (
            if "!line!" neq "" if "!line:Result:=!" equ "!line!" if "!line:📤 Result:=!" equ "!line!" (
                echo %%i
            )
        )
    )
    
    del "%TEMP%\gpt_result.txt" >nul 2>&1
    exit /b 0
)

:install_ask
echo Installing ask command for current user...

REM Get current script path
set "current_script=%~f0"

REM Find user directories in PATH
set "target_dir="
echo Searching for user directories in PATH...

for %%p in ("%PATH:;=" "%") do (
    set "check_path=%%~p"
    REM Remove quotes
    set "check_path=!check_path:"=!"
    
    REM Check if path contains USERPROFILE and is writable
    echo !check_path! | findstr /I /C:"%USERPROFILE%" >nul
    if !errorlevel! equ 0 (
        REM Check if directory exists and is writable
        if exist "!check_path!" (
            REM Test write access by trying to create a temp file
            echo test > "!check_path!\test_write.tmp" 2>nul
            if exist "!check_path!\test_write.tmp" (
                del "!check_path!\test_write.tmp" >nul 2>&1
                echo Found writable user directory: !check_path!
                set "target_dir=!check_path!"
                goto :found_user_dir
            )
        )
    )
)

REM If no user directory found in PATH, installation is not possible
if not defined target_dir (
    echo.
    echo ERROR: No writable user directory found in PATH
    echo.
    echo Current PATH contains these directories:
    for %%p in ("%PATH:;=" "%") do (
        set "show_path=%%~p"
        set "show_path=!show_path:"=!"
        echo   !show_path!
    )
    echo.
    echo To install ask command, you need to add a user directory to PATH first.
    echo Common user directories:
    echo   %USERPROFILE%\bin
    echo   %USERPROFILE%\.local\bin
    echo   %APPDATA%\bin
    echo.
    echo Steps to add a directory to PATH:
    echo   1. Create a directory, for example: mkdir "%USERPROFILE%\bin"
    echo   2. Add it to PATH:
    echo      - Press Win+R, type "sysdm.cpl" and press Enter
    echo      - Click "Environment Variables"
    echo      - Under "User variables", select "Path" and click "Edit"
    echo      - Click "New" and add your directory path
    echo      - Click OK on all dialogs
    echo      - Restart Command Prompt
    echo.
    echo   Alternatively, run this command and restart Command Prompt:
    echo   setx PATH "%%PATH%%;%USERPROFILE%\bin"
    echo.
    exit /b 1
)

:found_user_dir
set "target_file=!target_dir!\ask.bat"

echo Target location: !target_file!

REM Create wrapper script that calls the original script
echo @echo off > "!target_file!"
echo REM Ask Terminal Chat - User wrapper >> "!target_file!"
echo REM Generated by ask.bat install >> "!target_file!"
echo. >> "!target_file!"
echo call "!current_script!" %%* >> "!target_file!"

if exist "!target_file!" (
    echo.
    echo Ask command installed successfully!
    echo Location: !target_file!
    echo You can now use 'ask' from anywhere in the command prompt!
    echo.
    call :show_usage_examples
) else (
    echo Error: Failed to create wrapper script
    exit /b 1
)
exit /b 0

:uninstall_ask
echo Removing ask command...

REM Find ask.bat in user directories in PATH
set "found_file="
echo Searching for installed ask command...

for %%p in ("%PATH:;=" "%") do (
    set "check_path=%%~p"
    REM Remove quotes
    set "check_path=!check_path:"=!"
    
    REM Check if path contains USERPROFILE and has ask.bat
    echo !check_path! | findstr /I /C:"%USERPROFILE%" >nul
    if !errorlevel! equ 0 (
        if exist "!check_path!\ask.bat" (
            REM Check if it's our wrapper by looking for our signature
            findstr /C:"Generated by ask.bat install" "!check_path!\ask.bat" >nul 2>&1
            if !errorlevel! equ 0 (
                set "found_file=!check_path!\ask.bat"
                echo Found installed ask command: !found_file!
                goto :found_uninstall
            )
        )
    )
)

:found_uninstall
if defined found_file (
    del "!found_file!" >nul 2>&1
    if exist "!found_file!" (
        echo Error: Could not remove !found_file!
        echo File may be in use
        exit /b 1
    ) else (
        echo Ask command removed successfully from: !found_file!
        echo You may need to restart your command prompt
    )
) else (
    echo Ask command not found in any user directories in PATH
    echo It may not be installed or already removed
    echo.
    echo Checked these user directories:
    for %%p in ("%PATH:;=" "%") do (
        set "show_path=%%~p"
        set "show_path=!show_path:"=!"
        echo !show_path! | findstr /I /C:"%USERPROFILE%" >nul
        if !errorlevel! equ 0 (
            echo   !show_path!
        )
    )
)
exit /b 0

:show_help
echo Ask Terminal Chat - AI assistant for command line
echo.
echo This tool helps you get answers about commands and general questions using AI.
echo System context (OS, shell, directory) is automatically included for better answers.
echo.
echo Installation:
echo   ask.bat install                                       # Install global 'ask' command (recommended)
echo.
call :show_usage_examples
exit /b 0

:show_usage_examples
echo Usage examples:
echo   ask help                                              # Show this help
echo   ask "What is Python?"                                 # Ask AI directly
echo   ask "dir" "How many files are in the directory?"      # Run command, ask AI about result  
echo   ask "tasklist" "Which processes use the most memory?" 
echo   ask uninstall                                         # Remove global command
goto :eof

:ensure_virtual_env
REM Function to ensure virtual environment is activated
set "venv_path=%~dp0..\.virtualenv"
set "activate_script=%venv_path%\Scripts\activate.bat"

REM Check if virtual environment is already active
if defined VIRTUAL_ENV (
    goto :eof
)

if exist "%activate_script%" (
    echo Activating virtual environment...
    call "%activate_script%"
) else (
    echo Error: Virtual environment not found at %venv_path%
    exit /b 1
)
goto :eof

:get_system_info
REM Function to get system information
set "current_dir=%CD%"
REM Escape backslashes for JSON
set "current_dir=!current_dir:\=\\!"

set "system_info=System Context: - OS: %OS% %PROCESSOR_ARCHITECTURE% - Command Prompt: Windows Batch - Current Directory: !current_dir!"
goto :eof

REM Function to find project root directory
:find_project_root
set "current_path=%~dp0"
set "project_root="

REM Loop to find project root by looking for mcp_server
:find_loop
REM Remove trailing backslash for consistent comparison
if "!current_path:~-1!"=="\" set "current_path=!current_path:~0,-1!"

REM Check for project indicator
if exist "!current_path!\mcp_server" (
    set "project_root=!current_path!"
    goto :found_root
)

REM Move up one directory
for %%F in ("!current_path!") do set "parent_path=%%~dpF"
if "!parent_path:~0,-1!"=="!current_path!" (
    REM Reached root, use current script directory
    set "project_root=%~dp0"
    goto :found_root
)
set "current_path=!parent_path:~0,-1!"
goto :find_loop

:found_root
goto :eof
