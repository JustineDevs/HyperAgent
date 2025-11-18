@echo off
REM Sync main branch from development, excluding test files (Windows batch script)
REM Usage: scripts\sync_main_branch.bat

echo [*] Syncing main branch from development...
echo.

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo [-] Error: Not in a git repository
    exit /b 1
)

REM Get current branch
for /f "tokens=2" %%b in ('git branch --show-current') do set CURRENT_BRANCH=%%b
echo [*] Current branch: %CURRENT_BRANCH%

REM Switch to development branch
echo [*] Switching to development branch...
git checkout development 2>nul
if errorlevel 1 (
    echo [*] Development branch does not exist, creating from current branch...
    git checkout -b development
)

REM Pull latest changes (if remote exists)
git remote | findstr /C:"origin" >nul 2>&1
if not errorlevel 1 (
    echo [*] Pulling latest changes from origin/development...
    git pull origin development 2>nul || echo [!] No remote changes or remote not configured
)

REM Create or switch to main branch
echo [*] Creating/updating main branch...
git show-ref --verify --quiet refs/heads/main
if not errorlevel 1 (
    echo [*] Main branch exists, switching to it...
    git checkout main
    echo [*] Merging development into main...
    git merge development --no-edit --no-ff
) else (
    echo [*] Main branch does not exist, creating from development...
    git checkout -b main
)

REM Remove development-only files from main
echo.
echo [*] Removing development-only files from main branch...

if exist "tests\" (
    echo   [-] Removing: tests\
    rmdir /s /q "tests\"
)
if exist "scripts\" (
    echo   [-] Removing: scripts\
    rmdir /s /q "scripts\"
)
if exist "docs\" (
    echo   [-] Removing: docs\
    rmdir /s /q "docs\"
)
if exist "GUIDE\" (
    echo   [-] Removing: GUIDE\
    rmdir /s /q "GUIDE\"
)
if exist "examples\" (
    echo   [-] Removing: examples\
    rmdir /s /q "examples\"
)
if exist "pytest.ini" (
    echo   [-] Removing: pytest.ini
    del /f /q "pytest.ini"
)
if exist "tests\README.md" (
    echo   [-] Removing: tests\README.md
    del /f /q "tests\README.md"
)
if exist ".cursor\" (
    echo   [-] Removing: .cursor\
    rmdir /s /q ".cursor\"
)

REM Stage all changes
git add -A

REM Check if there are changes to commit
git diff --staged --quiet
if errorlevel 1 (
    echo.
    echo [*] Committing changes...
    git commit -m "chore: remove development files for production release" -m "- Removed tests/ directory" -m "- Removed scripts/ directory" -m "- Removed docs/ directory" -m "- Removed GUIDE/ directory" -m "- Removed examples/ directory" -m "- Removed pytest.ini" -m "- Removed test documentation" -m "- Removed planning documents"
    echo [+] Changes committed
) else (
    echo.
    echo [+] No changes to commit (files already removed)
)

echo.
echo [+] Main branch synced and cleaned
for /f "tokens=2" %%b in ('git branch --show-current') do echo [*] Current branch: %%b
echo.
echo [*] Next steps:
echo     1. Review changes: git log --oneline -5
echo     2. Push to remote: git push origin main
echo     3. Switch back to development: git checkout development

