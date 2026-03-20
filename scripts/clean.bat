@echo off
REM ============================================
REM VidMark - Cleanup Script (Windows CMD)
REM Removes build artifacts, caches, temp files
REM ============================================

echo.
echo ========================================
echo  VidMark - Cleanup
echo ========================================
echo.

cd /d "%~dp0\.."

echo [1/6] Removing __pycache__ directories...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo   Removing: %%d
        rmdir /s /q "%%d"
    )
)

echo [2/6] Removing .pyc and .pyo files...
del /s /q *.pyc >nul 2>&1
del /s /q *.pyo >nul 2>&1

echo [3/6] Removing build/dist directories...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [4/6] Removing .spec files...
del /q *.spec >nul 2>&1

echo [5/6] Removing .egg-info directories...
for /d /r %%d in (*.egg-info) do (
    if exist "%%d" (
        echo   Removing: %%d
        rmdir /s /q "%%d"
    )
)

echo [6/6] Removing user temp/settings directories...
if exist "%USERPROFILE%\.vws_temp" (
    echo   Removing: %USERPROFILE%\.vws_temp
    rmdir /s /q "%USERPROFILE%\.vws_temp"
)
if exist "%USERPROFILE%\.vws_settings" (
    echo   Removing: %USERPROFILE%\.vws_settings
    rmdir /s /q "%USERPROFILE%\.vws_settings"
)

echo.
echo ========================================
echo  Cleanup complete!
echo ========================================
echo.
pause