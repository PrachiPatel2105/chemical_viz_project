@echo off
echo ========================================
echo Chemical Viz Project - GitHub Upload
echo ========================================
echo.

echo Step 1: Initializing Git repository...
git init
if errorlevel 1 (
    echo Git initialization failed. Make sure Git is installed.
    pause
    exit /b 1
)

echo.
echo Step 2: Adding all files...
git add .
if errorlevel 1 (
    echo Failed to add files.
    pause
    exit /b 1
)

echo.
echo Step 3: Creating initial commit...
git commit -m "Initial commit: Chemical Equipment Visualizer - Cleaned and optimized"
if errorlevel 1 (
    echo Commit failed.
    pause
    exit /b 1
)

echo.
echo Step 4: Adding remote repository...
git remote add origin https://github.com/PrachiPatel2105/chemical_viz_project.git
if errorlevel 1 (
    echo Remote already exists or failed to add. Continuing...
)

echo.
echo Step 5: Setting main branch...
git branch -M main

echo.
echo Step 6: Pushing to GitHub...
git push -u origin main --force
if errorlevel 1 (
    echo Push failed. Please check your GitHub credentials and repository access.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Project uploaded to GitHub!
echo ========================================
echo.
echo Repository: https://github.com/PrachiPatel2105/chemical_viz_project
echo.
pause
